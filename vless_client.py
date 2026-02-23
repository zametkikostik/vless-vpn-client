#!/usr/bin/env python3
"""
VLESS VPN Client - Production Version
Enterprise-grade VPN client for VLESS protocol with Reality obfuscation.

This module provides a robust VPN client implementation with automatic server
selection, health checking, and XRay core integration.

Author: VPN Development Team
Version: 2.0.0
License: MIT
"""

import os
import sys
import json
import time
import socket
import logging
import subprocess
import signal
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class VPNConfig:
    """VPN client configuration."""
    home_dir: Path = field(default_factory=Path.home)
    base_dir: Path = field(default=None)
    data_dir: Path = field(default=None)
    logs_dir: Path = field(default=None)
    config_dir: Path = field(default=None)
    
    servers_file: Path = field(default=None)
    config_file: Path = field(default=None)
    log_file: Path = field(default=None)
    xray_bin: Path = field(default=None)
    
    def __post_init__(self):
        self.base_dir = self.home_dir / "vpn-client"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"
        self.servers_file = self.data_dir / "servers.json"
        self.config_file = self.config_dir / "config.json"
        self.log_file = self.logs_dir / "client.log"
        self.xray_bin = self.home_dir / "vpn-client" / "bin" / "xray"


@dataclass
class Server:
    """VPN server representation."""
    host: str
    port: int
    uuid: str
    name: str = ""
    status: str = "online"
    latency: int = 9999
    stream_settings: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure application logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("vless_vpn")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


# =============================================================================
# VPN Client
# =============================================================================

class VLESSClient:
    """
    Production VLESS VPN client with Reality protocol support.
    
    Features:
    - Automatic server selection based on latency and availability
    - Reality protocol support for obfuscation
    - XRay core integration
    - Health checking and failover
    """
    
    def __init__(self, config: Optional[VPNConfig] = None):
        self.config = config or VPNConfig()
        self.logger = setup_logging(self.config.log_file)
        self.servers: List[Dict[str, Any]] = []
        self.xray_process: Optional[subprocess.Popen] = None
        self.running = False
        self.current_server: Optional[Dict[str, Any]] = None
        
        # Ensure directories exist
        for directory in [self.config.config_dir, self.config.data_dir, self.config.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_servers(self) -> bool:
        """Load server list from cache file."""
        try:
            if self.config.servers_file.exists():
                with open(self.config.servers_file, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
                self.logger.info(f"Loaded {len(self.servers)} servers from cache")
                return True
            else:
                self.logger.warning("Server cache file not found")
                self.servers = []
                return False
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self.servers = []
            return False
    
    def test_server_connectivity(self, host: str, port: int, timeout: int = 2) -> bool:
        """Test TCP connectivity to server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def select_best_server(self) -> Optional[Dict[str, Any]]:
        """
        Select the best available server using priority-based algorithm.
        
        Priority order:
        1. Low latency servers (<100ms) with Reality protocol
        2. WHITE list servers with Reality protocol
        3. Any Reality protocol servers with UUID
        
        Returns:
            Selected server configuration or None
        """
        if not self.servers:
            self.logger.error("No servers available in cache")
            return None
        
        # Priority 1: Low latency servers
        low_latency = [
            s for s in self.servers
            if s.get("uuid")
            and s.get("latency", 9999) < 100
            and s.get("stream_settings", {}).get("security") == "reality"
        ]
        
        # Priority 2: WHITE list servers
        white_servers = [
            s for s in self.servers
            if s.get("uuid")
            and "WHITE" in s.get("name", "").upper()
            and s.get("stream_settings", {}).get("security") == "reality"
        ]
        
        # Priority 3: All Reality servers
        all_reality = [
            s for s in self.servers
            if s.get("uuid")
            and "chatgpt" not in s.get("host", "").lower()
            and s.get("stream_settings", {}).get("security") == "reality"
        ]
        
        # Select candidate pool
        candidates = low_latency if low_latency else (white_servers if white_servers else all_reality)
        
        if not candidates:
            self.logger.error("No Reality servers with UUID available")
            return None
        
        # Sort by latency
        candidates.sort(key=lambda x: x.get("latency", 9999))
        
        # Test top 5 servers
        self.logger.info(f"Testing {min(len(candidates), 5)} servers...")
        for server in candidates[:5]:
            if self.test_server_connectivity(server['host'], server['port'], timeout=2):
                server_type = "LOW-PING" if server.get("latency", 9999) < 100 else "WHITE" if "WHITE" in server.get("name", "").upper() else "BLACK"
                self.logger.info(f"Server available: {server['host']}:{server['port']} ({server_type}, latency: {server.get('latency', 'N/A')}ms)")
                return server
        
        # Fallback to first server
        self.logger.warning("Connectivity tests failed, using first available server")
        return candidates[0]
    
    def generate_config(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Generate XRay configuration for selected server."""
        stream_settings = server.get("stream_settings", {})
        security = stream_settings.get("security", "tls")
        
        if security == "reality":
            reality_settings = stream_settings.get("reality_settings", {})
            config = {
                "log": {"loglevel": "warning"},
                "inbounds": [
                    {
                        "port": 10808,
                        "protocol": "socks",
                        "settings": {"auth": "noauth", "udp": True},
                        "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
                    },
                    {
                        "port": 10809,
                        "protocol": "http",
                        "settings": {"allowTransparent": False}
                    }
                ],
                "outbounds": [{
                    "tag": "proxy",
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": server["host"],
                            "port": server["port"],
                            "users": [{
                                "id": server.get("uuid", ""),
                                "encryption": "none",
                                "flow": server.get("flow", "xtls-rprx-vision")
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "serverName": reality_settings.get("serverName", server["host"]),
                            "fingerprint": "chrome",
                            "publicKey": reality_settings.get("publicKey", ""),
                            "shortId": reality_settings.get("shortId", "")
                        }
                    }
                }]
            }
        else:
            tls_settings = stream_settings.get("tls_settings", {})
            config = {
                "log": {"loglevel": "warning"},
                "inbounds": [
                    {
                        "port": 10808,
                        "protocol": "socks",
                        "settings": {"auth": "noauth", "udp": True},
                        "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
                    },
                    {
                        "port": 10809,
                        "protocol": "http",
                        "settings": {"allowTransparent": False}
                    }
                ],
                "outbounds": [{
                    "tag": "proxy",
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": server["host"],
                            "port": server["port"],
                            "users": [{
                                "id": server.get("uuid", ""),
                                "encryption": "none",
                                "flow": ""
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "tls",
                        "tlsSettings": {
                            "serverName": tls_settings.get("serverName", server["host"]),
                            "alpn": ["h2", "http/1.1"],
                            "fingerprint": "chrome"
                        }
                    }
                }]
            }
        
        return config
    
    def start_xray(self, server: Dict[str, Any]) -> bool:
        """Start XRay core with generated configuration."""
        try:
            # Generate and save configuration
            config = self.generate_config(server)
            with open(self.config.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration generated: {self.config.config_file}")
            
            # Verify XRay binary
            if not self.config.xray_bin.exists():
                self.logger.error("XRay binary not found")
                return False
            
            # Start XRay
            cmd = [str(self.config.xray_bin), "run", "-c", str(self.config.config_file)]
            self.xray_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup
            time.sleep(3)
            
            # Verify process is running
            if self.xray_process.poll() is None:
                self.logger.info("XRay started successfully")
                self.current_server = server
                return True
            else:
                self.logger.error("XRay failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start XRay: {e}")
            return False
    
    def stop_xray(self) -> None:
        """Stop XRay core and cleanup."""
        try:
            if self.xray_process:
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
                self.logger.info("XRay stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop XRay: {e}")
        
        # Force kill if still running
        try:
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        except Exception:
            pass
        
        self.current_server = None
    
    def connect(self) -> bool:
        """Establish VPN connection."""
        self.logger.info("=" * 60)
        self.logger.info("VLESS VPN Client - Production Version 2.0.0")
        self.logger.info("=" * 60)
        
        # Load servers
        if not self.load_servers():
            self.logger.error("No servers available. Run update first.")
            return False
        
        # Select best server
        server = self.select_best_server()
        if not server:
            return False
        
        # Connect
        self.logger.info(f"Connecting to {server['host']}:{server['port']}...")
        
        if self.start_xray(server):
            self.logger.info("VPN connected successfully")
            self.logger.info("  SOCKS5: 127.0.0.1:10808")
            self.logger.info("  HTTP: 127.0.0.1:10809")
            return True
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from VPN."""
        self.logger.info("=" * 60)
        self.logger.info("Disconnecting from VPN")
        self.logger.info("=" * 60)
        
        self.running = False
        self.stop_xray()
        self.logger.info("VPN disconnected")
    
    def status(self) -> Dict[str, Any]:
        """Get current VPN status."""
        # Load servers for statistics
        try:
            if self.config.servers_file.exists():
                with open(self.config.servers_file, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
        except Exception:
            self.servers = []
        
        # Check XRay process
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
        is_connected = result.returncode == 0
        
        online_count = sum(1 for s in self.servers if s.get("status") == "online")
        
        return {
            "connected": is_connected,
            "total_servers": len(self.servers),
            "online_servers": online_count,
            "current_server": self.current_server,
            "socks_port": 10808,
            "http_port": 10809
        }
    
    def print_status(self) -> None:
        """Print VPN status to console."""
        status = self.status()
        
        print("\n" + "=" * 60)
        print("VLESS VPN CLIENT - STATUS")
        print("=" * 60)
        
        if status["connected"]:
            print("Status: Connected")
            if self.current_server:
                print(f"Server: {self.current_server['host']}:{self.current_server['port']}")
        else:
            print("Status: Disconnected")
        
        print(f"\nTotal servers: {status['total_servers']}")
        print(f"Online: {status['online_servers']}")
        
        print("\nProxy endpoints:")
        print(f"  SOCKS5: 127.0.0.1:{status['socks_port']}")
        print(f"  HTTP: 127.0.0.1:{status['http_port']}")
        print("=" * 60)
    
    def update_servers(self) -> bool:
        """Update server list from GitHub repository."""
        import urllib.request
        from urllib.parse import urlparse
        
        self.logger.info("Updating servers from GitHub...")
        
        try:
            api_url = "https://api.github.com/repos/igareck/vpn-configs-for-russia/contents"
            req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                files = json.loads(response.read().decode())
            
            vless_files = [
                f for f in files
                if f["type"] == "file" and f["name"].endswith(".txt")
            ]
            
            self.logger.info(f"Found {len(vless_files)} configuration files")
            
            new_servers = []
            for file_info in vless_files:
                try:
                    download_url = file_info.get("download_url")
                    if not download_url:
                        continue
                    
                    self.logger.info(f"Downloading: {file_info['name']}")
                    req = urllib.request.Request(download_url)
                    with urllib.request.urlopen(req, timeout=30) as response:
                        content = response.read().decode("utf-8")
                    
                    for line in content.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("vless://"):
                            server = self._parse_vless_url(line, file_info["name"])
                            if server:
                                new_servers.append(server)
                                
                except Exception as e:
                    self.logger.warning(f"Failed to process {file_info['name']}: {e}")
            
            # Save servers
            if new_servers:
                with open(self.config.servers_file, 'w', encoding='utf-8') as f:
                    json.dump(new_servers, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Saved {len(new_servers)} servers")
                return True
            else:
                self.logger.warning("No servers found")
                return False
                
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
    def _parse_vless_url(self, url: str, name: str) -> Optional[Dict[str, Any]]:
        """Parse VLESS URL into server configuration."""
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            
            parsed = urlparse(url)
            uuid = parsed.username or ""
            host = parsed.hostname or ""
            port = parsed.port or 443
            
            if not uuid or not host:
                return None
            
            qs = parse_qs(parsed.query)
            params = {k: unquote(v[0]) if v else "" for k, v in qs.items()}
            
            security = params.get("security", "tls")
            
            server = {
                "host": host,
                "port": port,
                "uuid": uuid,
                "name": name,
                "status": "online",
                "latency": 9999,
                "stream_settings": {
                    "security": security
                }
            }
            
            if security == "reality":
                server["stream_settings"]["reality_settings"] = {
                    "serverName": params.get("sni", host),
                    "fingerprint": "chrome",
                    "publicKey": params.get("pbk", ""),
                    "shortId": params.get("sid", "")
                }
            else:
                server["stream_settings"]["tls_settings"] = {
                    "serverName": params.get("sni", host),
                    "alpn": ["h2", "http/1.1"],
                    "fingerprint": "chrome"
                }
            
            return server
            
        except Exception:
            return None


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="VLESS VPN Client - Production Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vless-vpn start --auto    Connect to VPN automatically
  vless-vpn status          Show connection status
  vless-vpn update          Update server list from GitHub
  vless-vpn stop            Disconnect from VPN
        """
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "update"],
        help="Command to execute"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-connect to best server"
    )
    
    args = parser.parse_args()
    
    client = VLESSClient()
    
    # Signal handler
    def signal_handler(sig, frame):
        client.logger.info("Received termination signal")
        client.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Execute command
    if args.command == "start":
        if client.connect():
            client.running = True
            client.logger.info("Waiting for termination signal (Ctrl+C to stop)...")
            try:
                while client.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                client.logger.info("Received Ctrl+C, disconnecting...")
                client.disconnect()
        else:
            client.logger.error("Failed to connect")
            sys.exit(1)
    
    elif args.command == "stop":
        client.disconnect()
    
    elif args.command == "status":
        client.print_status()
    
    elif args.command == "update":
        success = client.update_servers()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
