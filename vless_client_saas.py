#!/usr/bin/env python3
"""
VLESS VPN Client - SaaS Production Edition
Commercial-grade VPN solution for enterprise deployment.

© 2024 VPN Solutions Inc. All rights reserved.
Licensed under Commercial License - See LICENSE.md
"""

__version__ = "3.0.0-enterprise"
__author__ = "VPN Solutions Development Team"
__copyright__ = "Copyright 2024, VPN Solutions Inc."
__license__ = "PROPRIETARY"

import os
import sys
import json
import time
import socket
import logging
import subprocess
import signal
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import urllib.request
from urllib.parse import urlparse, parse_qs, unquote

# =============================================================================
# Configuration Constants
# =============================================================================

class Config:
    """Application configuration constants."""
    
    APP_NAME = "VLESS VPN Client"
    APP_VERSION = "3.0.0-enterprise"
    AUTHOR = "VPN Solutions Inc."
    
    # Paths
    HOME_DIR = Path.home()
    BASE_DIR = HOME_DIR / "vpn-client"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    CONFIG_DIR = BASE_DIR / "config"
    CACHE_DIR = BASE_DIR / "cache"
    
    # Files
    SERVERS_FILE = DATA_DIR / "servers.json"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    LOG_FILE = LOGS_DIR / "client.log"
    LICENSE_FILE = BASE_DIR / "LICENSE"
    
    # XRay
    XRAY_BIN = HOME_DIR / "vpn-client" / "bin" / "xray"
    
    # Network
    SOCKS_PORT = 10808
    HTTP_PORT = 10809
    DEFAULT_TIMEOUT = 5
    
    # Server selection
    MAX_TEST_SERVERS = 5
    MIN_LATENCY_THRESHOLD = 100
    
    # GitHub
    GITHUB_REPO = "igareck/vpn-configs-for-russia"
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents"


# =============================================================================
# Enums
# =============================================================================

class ServerPriority(Enum):
    """Server selection priority levels."""
    LOW_LATENCY = 1
    WHITE_LIST = 2
    BLACK_LIST = 3


class ConnectionStatus(Enum):
    """VPN connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ServerConfig:
    """VPN server configuration."""
    host: str
    port: int
    uuid: str
    name: str = ""
    status: str = "online"
    latency: int = 9999
    security: str = "reality"
    server_name: str = ""
    public_key: str = ""
    short_id: str = ""
    fingerprint: str = "chrome"
    flow: str = "xtls-rprx-vision"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary."""
        stream = data.get("stream_settings", {})
        reality = stream.get("reality_settings", {})
        return cls(
            host=data.get("host", ""),
            port=data.get("port", 443),
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            status=data.get("status", "online"),
            latency=data.get("latency", 9999),
            security=stream.get("security", "reality"),
            server_name=reality.get("serverName", ""),
            public_key=reality.get("publicKey", ""),
            short_id=reality.get("shortId", ""),
            flow=data.get("flow", "xtls-rprx-vision")
        )


@dataclass
class ConnectionInfo:
    """VPN connection information."""
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    server: Optional[ServerConfig] = None
    socks_port: int = Config.SOCKS_PORT
    http_port: int = Config.HTTP_PORT
    connected_at: Optional[datetime] = None
    bytes_sent: int = 0
    bytes_received: int = 0


# =============================================================================
# Logging Setup
# =============================================================================

class LoggerFactory:
    """Factory for creating loggers."""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[Path] = None) -> logging.Logger:
        """Get or create logger instance."""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        cls._loggers[name] = logger
        return logger


# =============================================================================
# VPN Client Core
# =============================================================================

class VLESSClientCore:
    """
    Core VPN client functionality.
    
    Enterprise-grade VLESS VPN client with Reality protocol support.
    Designed for commercial deployment and SaaS integration.
    """
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("VLESSClient", Config.LOG_FILE)
        self.servers: List[ServerConfig] = []
        self.connection: ConnectionInfo = ConnectionInfo()
        self.xray_process: Optional[subprocess.Popen] = None
        self.running = False
        
        # Initialize directories
        self._init_directories()
    
    def _init_directories(self) -> None:
        """Create required directories."""
        for directory in [Config.DATA_DIR, Config.LOGS_DIR, Config.CONFIG_DIR, Config.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_servers(self) -> bool:
        """Load server list from cache."""
        try:
            if Config.SERVERS_FILE.exists():
                with open(Config.SERVERS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.servers = [ServerConfig.from_dict(s) for s in data]
                self.logger.info(f"Loaded {len(self.servers)} servers from cache")
                return True
            
            self.logger.warning("Server cache file not found")
            self.servers = []
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self.servers = []
            return False
    
    def save_servers(self) -> bool:
        """Save server list to cache."""
        try:
            data = [s.to_dict() for s in self.servers]
            with open(Config.SERVERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(self.servers)} servers")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save servers: {e}")
            return False
    
    def test_connectivity(self, host: str, port: int, timeout: int = 2) -> bool:
        """Test TCP connectivity to server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_servers_by_priority(self) -> List[ServerConfig]:
        """Get servers sorted by priority."""
        if not self.servers:
            return []
        
        # Priority 1: Low latency
        low_latency = [
            s for s in self.servers
            if s.status == "online" and s.latency < Config.MIN_LATENCY_THRESHOLD
        ]
        
        # Priority 2: WHITE list
        white_list = [
            s for s in self.servers
            if s.status == "online" and "WHITE" in s.name.upper()
        ]
        
        # Priority 3: All online
        all_online = [s for s in self.servers if s.status == "online"]
        
        if low_latency:
            return sorted(low_latency, key=lambda x: x.latency)
        elif white_list:
            return sorted(white_list, key=lambda x: x.latency)
        else:
            return sorted(all_online, key=lambda x: x.latency)
    
    def select_best_server(self, location: Optional[str] = None) -> Optional[ServerConfig]:
        """
        Select best available server.
        
        Args:
            location: Optional location filter
        
        Returns:
            Selected server or None
        """
        candidates = self.get_servers_by_priority()
        
        if not candidates:
            self.logger.error("No servers available")
            return None
        
        # Filter by location if specified
        if location:
            location_lower = location.lower()
            candidates = [
                s for s in candidates
                if location_lower in s.name.lower() or location_lower.upper() in s.name
            ]
            
            if not candidates:
                self.logger.warning(f"No servers found for location: {location}")
                candidates = self.get_servers_by_priority()
        
        # Test top servers
        self.logger.info(f"Testing {min(len(candidates), Config.MAX_TEST_SERVERS)} servers...")
        
        for server in candidates[:Config.MAX_TEST_SERVERS]:
            if self.test_connectivity(server.host, server.port):
                self.logger.info(f"Selected: {server.host}:{server.port} (latency: {server.latency}ms)")
                return server
        
        # Fallback
        self.logger.warning("Connectivity tests failed, using first available")
        return candidates[0] if candidates else None
    
    def generate_xray_config(self, server: ServerConfig) -> Dict[str, Any]:
        """Generate XRay configuration."""
        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "port": Config.SOCKS_PORT,
                    "protocol": "socks",
                    "settings": {"auth": "noauth", "udp": True},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
                },
                {
                    "port": Config.HTTP_PORT,
                    "protocol": "http",
                    "settings": {"allowTransparent": False}
                }
            ],
            "outbounds": [{
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": server.host,
                        "port": server.port,
                        "users": [{
                            "id": server.uuid,
                            "encryption": "none",
                            "flow": server.flow
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "serverName": server.server_name or server.host,
                        "fingerprint": server.fingerprint,
                        "publicKey": server.public_key,
                        "shortId": server.short_id
                    }
                }
            }]
        }
        
        return config
    
    def start_xray(self, server: ServerConfig) -> bool:
        """Start XRay core."""
        try:
            # Generate config
            config = self.generate_xray_config(server)
            
            # Save config
            with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration generated: {Config.CONFIG_FILE}")
            
            # Verify XRay binary
            if not Config.XRAY_BIN.exists():
                self.logger.error("XRay binary not found")
                return False
            
            # Start XRay
            cmd = [str(Config.XRAY_BIN), "run", "-c", str(Config.CONFIG_FILE)]
            self.xray_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup
            time.sleep(3)
            
            # Verify running
            if self.xray_process.poll() is None:
                self.logger.info("XRay started successfully")
                self.connection.server = server
                self.connection.status = ConnectionStatus.CONNECTED
                self.connection.connected_at = datetime.now()
                return True
            else:
                self.logger.error("XRay failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start XRay: {e}")
            return False
    
    def stop_xray(self) -> None:
        """Stop XRay core."""
        try:
            if self.xray_process:
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
                self.logger.info("XRay stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop XRay: {e}")
        
        # Force kill
        try:
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        except Exception:
            pass
        
        self.connection.status = ConnectionStatus.DISCONNECTED
        self.connection.server = None
    
    def connect(self, location: Optional[str] = None) -> bool:
        """
        Establish VPN connection.
        
        Args:
            location: Optional location filter
        
        Returns:
            True if connected successfully
        """
        self.logger.info("=" * 60)
        self.logger.info(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.logger.info(f"© {Config.AUTHOR}")
        self.logger.info("=" * 60)
        
        self.connection.status = ConnectionStatus.CONNECTING
        
        # Load servers
        if not self.load_servers():
            self.logger.error("No servers available. Run update first.")
            self.connection.status = ConnectionStatus.ERROR
            return False
        
        # Select server
        server = self.select_best_server(location)
        if not server:
            self.connection.status = ConnectionStatus.ERROR
            return False
        
        # Connect
        self.logger.info(f"Connecting to {server.host}:{server.port}...")
        
        if self.start_xray(server):
            self.logger.info("✓ VPN connected successfully")
            self.logger.info(f"  SOCKS5: 127.0.0.1:{Config.SOCKS_PORT}")
            self.logger.info(f"  HTTP: 127.0.0.1:{Config.HTTP_PORT}")
            self.running = True
            return True
        
        self.connection.status = ConnectionStatus.ERROR
        return False
    
    def disconnect(self) -> None:
        """Disconnect from VPN."""
        self.logger.info("=" * 60)
        self.logger.info("Disconnecting from VPN")
        self.logger.info("=" * 60)
        
        self.running = False
        self.stop_xray()
        self.logger.info("VPN disconnected")
    
    def get_status(self) -> ConnectionInfo:
        """Get current connection status."""
        # Check XRay process
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
        
        if result.returncode == 0 and self.connection.status != ConnectionStatus.DISCONNECTED:
            self.connection.status = ConnectionStatus.CONNECTED
        else:
            self.connection.status = ConnectionStatus.DISCONNECTED
        
        return self.connection
    
    def update_servers(self) -> bool:
        """Update server list from GitHub."""
        self.logger.info("Updating servers from GitHub...")
        
        try:
            req = urllib.request.Request(
                Config.GITHUB_API,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                files = json.loads(response.read().decode())
            
            vless_files = [
                f for f in files
                if f["type"] == "file" and f["name"].endswith(".txt")
            ]
            
            self.logger.info(f"Found {len(vless_files)} configuration files")
            
            new_servers: List[ServerConfig] = []
            
            for file_info in vless_files:
                try:
                    download_url = file_info.get("download_url")
                    if not download_url:
                        continue
                    
                    self.logger.debug(f"Downloading: {file_info['name']}")
                    
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
            
            if new_servers:
                self.servers = new_servers
                return self.save_servers()
            else:
                self.logger.warning("No servers found")
                return False
                
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
    def _parse_vless_url(self, url: str, name: str) -> Optional[ServerConfig]:
        """Parse VLESS URL."""
        try:
            parsed = urlparse(url)
            uuid = parsed.username or ""
            host = parsed.hostname or ""
            port = parsed.port or 443
            
            if not uuid or not host:
                return None
            
            qs = parse_qs(parsed.query)
            params = {k: unquote(v[0]) if v else "" for k, v in qs.items()}
            
            security = params.get("security", "tls")
            
            server = ServerConfig(
                host=host,
                port=port,
                uuid=uuid,
                name=name,
                security=security
            )
            
            if security == "reality":
                server.server_name = params.get("sni", host)
                server.public_key = params.get("pbk", "")
                server.short_id = params.get("sid", "")
            
            return server
            
        except Exception:
            return None
    
    def list_locations(self) -> Dict[str, int]:
        """Get available locations with server counts."""
        locations: Dict[str, int] = {}
        
        location_map = {
            "US": "USA", "USA": "USA",
            "DE": "Germany", "DEU": "Germany",
            "NL": "Netherlands", "NLD": "Netherlands",
            "GB": "UK", "GBR": "UK",
            "FR": "France", "FRA": "France",
            "RU": "Russia", "RUS": "Russia",
        }
        
        for server in self.servers:
            if server.status != "online":
                continue
            
            country = "Other"
            for code, name in location_map.items():
                if code in server.name.upper():
                    country = name
                    break
            
            locations[country] = locations.get(country, 0) + 1
        
        return locations


# =============================================================================
# CLI Interface
# =============================================================================

class VPNCLI:
    """Command-line interface for VPN client."""
    
    def __init__(self):
        self.client = VLESSClientCore()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers."""
        def handler(sig, frame):
            self.client.logger.info("Received termination signal")
            self.client.running = False
            self.client.disconnect()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
    
    def run(self) -> None:
        """Run CLI."""
        parser = self._create_parser()
        args = parser.parse_args()
        
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog="vless-vpn",
            description=f"{Config.APP_NAME} - {Config.APP_VERSION}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  vless-vpn start --auto              Connect with auto-selected server
  vless-vpn start -l USA --daemon     Connect to USA with auto-reconnect
  vless-vpn locations                 Show available locations
  vless-vpn status                    Show connection status
  vless-vpn update                    Update server list
  vless-vpn stop                      Disconnect from VPN

For commercial licensing, contact: sales@vpnsolutions.io
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Start command
        start_parser = subparsers.add_parser("start", help="Start VPN connection")
        start_parser.add_argument("--auto", "-a", action="store_true", help="Auto-select server")
        start_parser.add_argument("--location", "-l", type=str, help="Location filter")
        start_parser.add_argument("--daemon", "-d", action="store_true", help="Daemon mode")
        start_parser.set_defaults(func=self.cmd_start)
        
        # Stop command
        stop_parser = subparsers.add_parser("stop", help="Stop VPN connection")
        stop_parser.set_defaults(func=self.cmd_stop)
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Show status")
        status_parser.set_defaults(func=self.cmd_status)
        
        # Update command
        update_parser = subparsers.add_parser("update", help="Update servers")
        update_parser.set_defaults(func=self.cmd_update)
        
        # Locations command
        locations_parser = subparsers.add_parser("locations", help="List locations")
        locations_parser.set_defaults(func=self.cmd_locations)
        
        return parser
    
    def cmd_start(self, args: argparse.Namespace) -> None:
        """Handle start command."""
        location = args.location if args.location else None
        
        if args.daemon:
            self._run_daemon(location)
        else:
            if self.client.connect(location):
                self.client.logger.info("Waiting for termination signal (Ctrl+C to stop)...")
                try:
                    while self.client.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.client.logger.info("Received Ctrl+C, disconnecting...")
                    self.client.disconnect()
            else:
                self.client.logger.error("Failed to connect")
                sys.exit(1)
    
    def _run_daemon(self, location: Optional[str]) -> None:
        """Run in daemon mode."""
        self.client.logger.info("Starting VPN in daemon mode (auto-reconnect enabled)")
        
        while True:
            if self.client.connect(location):
                try:
                    while self.client.running:
                        time.sleep(5)
                        
                        # Check XRay health
                        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
                        if result.returncode != 0:
                            self.client.logger.warning("XRay stopped, reconnecting...")
                            break
                except KeyboardInterrupt:
                    self.client.logger.info("Received Ctrl+C, disconnecting...")
                    self.client.disconnect()
                    break
                except Exception as e:
                    self.client.logger.error(f"Connection error: {e}, reconnecting...")
                    time.sleep(5)
            else:
                self.client.logger.error("Failed to connect, retrying in 10 seconds...")
                time.sleep(10)
    
    def cmd_stop(self, args: argparse.Namespace) -> None:
        """Handle stop command."""
        self.client.disconnect()
    
    def cmd_status(self, args: argparse.Namespace) -> None:
        """Handle status command."""
        status = self.client.get_status()
        
        print("\n" + "=" * 60)
        print(f" {Config.APP_NAME} - STATUS")
        print("=" * 60)
        
        if status.status == ConnectionStatus.CONNECTED:
            print("Status: ● Connected")
            if status.server:
                print(f"Server: {status.server.host}:{status.server.port}")
                if status.connected_at:
                    uptime = datetime.now() - status.connected_at
                    print(f"Uptime: {uptime}")
        else:
            print("Status: ○ Disconnected")
        
        print(f"\nTotal servers: {len(self.client.servers)}")
        online = sum(1 for s in self.client.servers if s.status == "online")
        print(f"Online: {online}")
        
        print("\nProxy endpoints:")
        print(f"  SOCKS5: 127.0.0.1:{status.socks_port}")
        print(f"  HTTP: 127.0.0.1:{status.http_port}")
        print("=" * 60)
    
    def cmd_update(self, args: argparse.Namespace) -> None:
        """Handle update command."""
        success = self.client.update_servers()
        sys.exit(0 if success else 1)
    
    def cmd_locations(self, args: argparse.Namespace) -> None:
        """Handle locations command."""
        if not self.client.servers:
            self.client.load_servers()
        
        locations = self.client.list_locations()
        
        print("\n" + "=" * 60)
        print(" AVAILABLE LOCATIONS")
        print("=" * 60)
        print(f"{'#':<4} {'Location':<20} {'Servers':<10}")
        print("-" * 60)
        
        for i, (country, count) in enumerate(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:20], 1):
            print(f"{i:<4} {country:<20} {count:<10}")
        
        if len(locations) > 20:
            print(f"... and {len(locations) - 20} more")
        
        print("=" * 60)
        print("\nUsage: vless-vpn start --location <country>")
        print("=" * 60)


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point."""
    cli = VPNCLI()
    cli.run()


if __name__ == "__main__":
    main()
