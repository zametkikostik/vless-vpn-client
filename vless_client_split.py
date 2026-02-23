#!/usr/bin/env python3
"""
VLESS Client Aggregator с разделением трафика
Российские сайты - напрямую, иностранные - через VPN
"""

import os
import sys
import json
import time
import base64
import urllib.request
import urllib.error
import subprocess
import threading
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import socket
import ssl

# Пути
SCRIPT_PATH = Path(__file__).resolve()
if SCRIPT_PATH.parent == Path.home() / ".local" / "bin":
    BASE_DIR = Path.home() / "vpn-client"
else:
    BASE_DIR = SCRIPT_PATH.parent

CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
XRAY_CONFIG = CONFIG_DIR / "config.json"
XRAY_CONFIG_SPLIT = CONFIG_DIR / "config-split.json"
WHITELIST_FILE = DATA_DIR / "whitelist.txt"
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"
SERVERS_FILE = DATA_DIR / "servers.json"
LOG_FILE = LOGS_DIR / "client.log"
GEOSITE_FILE = Path.home() / ".local" / "bin" / "geosite.dat"

# Создаем директории
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# GitHub
GITHUB_REPO = "igareck/vpn-configs-for-russia"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"


class Logger:
    @staticmethod
    def log(message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass


class VLESSConfig:
    @staticmethod
    def parse_vless_url(url: str) -> Optional[Dict[str, Any]]:
        try:
            if not url.startswith("vless://"):
                return None
            
            url_part = url[8:]
            name = ""
            if "#" in url_part:
                url_part, name = url_part.rsplit("#", 1)
                name = urllib.parse.unquote(name)
            
            if "?" not in url_part:
                return None
            
            main_part, query = url_part.split("?", 1)
            
            if "@" not in main_part:
                return None
            
            uuid, hostport = main_part.split("@", 1)
            
            if hostport.startswith("["):
                bracket_end = hostport.find("]")
                host = hostport[1:bracket_end]
                port = int(hostport[bracket_end+2:])
            else:
                host, port = hostport.rsplit(":", 1)
                port = int(port)
            
            params = {}
            for param in query.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = urllib.parse.unquote(value)
            
            return {
                "uuid": uuid,
                "host": host,
                "port": port,
                "name": name,
                "params": params,
                "raw_url": url,
                "added": datetime.now().isoformat(),
                "status": "unknown",
                "last_check": None,
                "latency": None
            }
        except Exception as e:
            Logger.log(f"Ошибка парсинга VLESS URL: {e}", "ERROR")
            return None
    
    @staticmethod
    def config_to_xray_split(config: Dict[str, Any]) -> Dict[str, Any]:
        """Конфиг XRay с разделением трафика"""
        params = config.get("params", {})
        security = params.get("security", "reality")
        sni = params.get("sni", config["host"])
        fp = params.get("fp", "chrome")
        pbk = params.get("pbk", "")
        sid = params.get("sid", "")
        network = params.get("type", "tcp")
        
        xray_config = {
            "remarks": config.get("name", "VLESS Split"),
            "log": {
                "loglevel": "warning",
                "access": str(LOGS_DIR / "access.log"),
                "error": str(LOGS_DIR / "error.log")
            },
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
                    "settings": {}
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": config["host"],
                            "port": config["port"],
                            "users": [{"id": config["uuid"], "encryption": "none", "flow": params.get("flow", "")}]
                        }]
                    },
                    "streamSettings": {
                        "network": network,
                        "security": security,
                        "realitySettings": {
                            "serverName": sni,
                            "fingerprint": fp,
                            "publicKey": pbk,
                            "shortId": sid,
                            "spiderX": "/"
                        } if security == "reality" else {}
                    },
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                },
                {
                    "protocol": "blackhole",
                    "tag": "block"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    # Российские сайты - напрямую
                    {
                        "type": "field",
                        "domain": [
                            "geosite:category-ru"
                        ],
                        "outboundTag": "direct"
                    },
                    # Российские IP - напрямую
                    {
                        "type": "field",
                        "ip": [
                            "geoip:ru"
                        ],
                        "outboundTag": "direct"
                    },
                    # Всё остальное - через прокси
                    {
                        "type": "field",
                        "network": "tcp,udp",
                        "outboundTag": "proxy"
                    }
                ]
            }
        }
        
        return xray_config
    
    @staticmethod
    def config_to_xray_full(config: Dict[str, Any]) -> Dict[str, Any]:
        """Конфиг XRay - весь трафик через VPN"""
        params = config.get("params", {})
        security = params.get("security", "reality")
        sni = params.get("sni", config["host"])
        fp = params.get("fp", "chrome")
        pbk = params.get("pbk", "")
        sid = params.get("sid", "")
        network = params.get("type", "tcp")
        
        xray_config = {
            "remarks": config.get("name", "VLESS Full"),
            "log": {
                "loglevel": "warning",
                "access": str(LOGS_DIR / "access.log"),
                "error": str(LOGS_DIR / "error.log")
            },
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
                    "settings": {}
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": config["host"],
                            "port": config["port"],
                            "users": [{"id": config["uuid"], "encryption": "none", "flow": params.get("flow", "")}]
                        }]
                    },
                    "streamSettings": {
                        "network": network,
                        "security": security,
                        "realitySettings": {
                            "serverName": sni,
                            "fingerprint": fp,
                            "publicKey": pbk,
                            "shortId": sid,
                            "spiderX": "/"
                        } if security == "reality" else {}
                    },
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                },
                {
                    "protocol": "blackhole",
                    "tag": "block"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    # Весь трафик через прокси
                    {
                        "type": "field",
                        "network": "tcp,udp",
                        "outboundTag": "proxy"
                    }
                ]
            }
        }
        
        return xray_config


class ServerManager:
    def __init__(self):
        self.servers: List[Dict[str, Any]] = []
        self.whitelist: set = set()
        self.blacklist: set = set()
        self.load_lists()
    
    def load_lists(self):
        if WHITELIST_FILE.exists():
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                self.whitelist = set(line.strip() for line in f if line.strip())
        
        if BLACKLIST_FILE.exists():
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                self.blacklist = set(line.strip() for line in f if line.strip())
        
        Logger.log(f"Загружено whitelist: {len(self.whitelist)}, blacklist: {len(self.blacklist)}")
    
    def save_servers(self):
        with open(SERVERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.servers, f, indent=2, ensure_ascii=False)
    
    def load_servers(self):
        if SERVERS_FILE.exists():
            try:
                with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
                Logger.log(f"Загружено серверов из кэша: {len(self.servers)}")
            except Exception as e:
                Logger.log(f"Ошибка загрузки кэша: {e}", "ERROR")
    
    def add_to_whitelist(self, host: str):
        self.whitelist.add(host)
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(self.whitelist)))
        Logger.log(f"Добавлен в whitelist: {host}")
    
    def add_to_blacklist(self, host: str):
        self.blacklist.add(host)
        with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(self.blacklist)))
        Logger.log(f"Добавлен в blacklist: {host}")
    
    def get_working_servers(self) -> List[Dict[str, Any]]:
        result = []
        for server in self.servers:
            if server["host"] not in self.blacklist:
                if not self.whitelist or server["host"] in self.whitelist:
                    if server.get("status") == "online":
                        result.append(server)
        result.sort(key=lambda x: x.get("latency") or 9999)
        return result


class ConfigFetcher:
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
    
    def fetch_configs(self) -> int:
        Logger.log("Загрузка конфигов из GitHub...")
        new_servers = []
        
        try:
            api_url = GITHUB_API_BASE
            Logger.log(f"Запрос к GitHub API: {api_url}")
            
            req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                files = json.loads(response.read().decode())
            
            vless_files = [
                f for f in files 
                if f["type"] == "file" and 
                f["name"].endswith(".txt") and 
                ("VLESS" in f["name"] or "White" in f["name"] or "BLACK" in f["name"])
            ]
            
            Logger.log(f"Найдено файлов с VLESS: {len(vless_files)}")
            
            for file_info in vless_files:
                try:
                    download_url = file_info.get("download_url")
                    if not download_url:
                        continue
                    
                    Logger.log(f"Загрузка: {file_info['name']}")
                    req = urllib.request.Request(download_url)
                    with urllib.request.urlopen(req, timeout=30) as response:
                        content = response.read().decode("utf-8")
                    
                    file_count = 0
                    for line in content.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("vless://"):
                            config = VLESSConfig.parse_vless_url(line)
                            if config:
                                new_servers.append(config)
                                file_count += 1
                    
                    Logger.log(f"  Обработан {file_info['name']}: {file_count} серверов")
                
                except Exception as e:
                    Logger.log(f"Ошибка загрузки файла {file_info['name']}: {e}", "WARN")
            
            self._update_servers_list(new_servers)
            return len(new_servers)
        
        except Exception as e:
            Logger.log(f"Ошибка загрузки конфигов: {e}", "ERROR")
            return 0
    
    def _update_servers_list(self, new_servers: List[Dict[str, Any]]):
        existing_hosts = {s["host"] for s in self.server_manager.servers}
        
        for server in new_servers:
            if server["host"] not in existing_hosts:
                self.server_manager.servers.append(server)
                Logger.log(f"Добавлен новый сервер: {server['host']}:{server['port']}")
        
        self.server_manager.save_servers()
        Logger.log(f"Всего серверов: {len(self.server_manager.servers)}")


class ServerTester:
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.test_timeout = 5
    
    def test_server(self, server: Dict[str, Any]) -> bool:
        host = server["host"]
        port = server["port"]
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.test_timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            latency = (time.time() - start_time) * 1000
            
            if result == 0:
                server["status"] = "online"
                server["latency"] = round(latency, 2)
                server["last_check"] = datetime.now().isoformat()
                return True
            else:
                server["status"] = "offline"
                server["last_check"] = datetime.now().isoformat()
                return False
        
        except Exception as e:
            server["status"] = "offline"
            server["last_check"] = datetime.now().isoformat()
            return False
    
    def test_all_servers(self, max_concurrent: int = 10):
        Logger.log(f"Начало тестирования {len(self.server_manager.servers)} серверов...")
        servers = self.server_manager.servers
        results = {"online": 0, "offline": 0}
        
        def test_worker(server_list):
            for server in server_list:
                if self.test_server(server):
                    results["online"] += 1
                else:
                    results["offline"] += 1
        
        threads = []
        chunk_size = max(1, len(servers) // max_concurrent)
        
        for i in range(0, len(servers), chunk_size):
            chunk = servers[i:i+chunk_size]
            t = threading.Thread(target=test_worker, args=(chunk,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.server_manager.save_servers()
        Logger.log(f"Тестирование завершено: онлайн={results['online']}, оффлайн={results['offline']}")


class XRayController:
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.xray_process = None
        self.current_server = None
    
    def is_installed(self) -> bool:
        try:
            result = subprocess.run(["xray", "version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def start(self, server: Dict[str, Any], mode: str = "split") -> bool:
        if not self.is_installed():
            Logger.log("XRay не установлен!", "ERROR")
            return False
        
        # Генерируем конфиг в зависимости от режима
        if mode == "split":
            config = VLESSConfig.config_to_xray_split(server)
            config_file = XRAY_CONFIG_SPLIT
            Logger.log(f"Режим: РАЗДЕЛЕНИЕ (РФ напрямую, остальное через VPN)")
        else:
            config = VLESSConfig.config_to_xray_full(server)
            config_file = XRAY_CONFIG
            Logger.log(f"Режим: ВСЁ через VPN")
        
        # Применяем blacklist
        if self.server_manager.blacklist:
            for host in self.server_manager.blacklist:
                config["routing"]["rules"].insert(0, {
                    "type": "field",
                    "domain": [f"full:{host}"],
                    "outboundTag": "block"
                })
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.stop()
        
        try:
            self.xray_process = subprocess.Popen(
                ["xray", "run", "-c", str(config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.current_server = server
            Logger.log(f"XRay запущен с сервером: {server['host']}:{server['port']}")
            time.sleep(2)
            
            if self.xray_process.poll() is None:
                Logger.log("XRay работает нормально")
                return True
            else:
                Logger.log("XRay не запустился", "ERROR")
                return False
        
        except Exception as e:
            Logger.log(f"Ошибка запуска XRay: {e}", "ERROR")
            return False
    
    def stop(self):
        if self.xray_process:
            try:
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
                Logger.log("XRay остановлен")
            except Exception as e:
                Logger.log(f"Ошибка остановки XRay: {e}", "WARN")
            finally:
                self.xray_process = None
                self.current_server = None


class VPNClient:
    def __init__(self):
        self.server_manager = ServerManager()
        self.config_fetcher = ConfigFetcher(self.server_manager)
        self.tester = ServerTester(self.server_manager)
        self.xray = XRayController(self.server_manager)
        self.running = False
        self.auto_update_interval = 300
    
    def connect(self, mode: str = "split", auto: bool = True) -> bool:
        Logger.log("=" * 60)
        Logger.log("Запуск VPN клиента...")
        Logger.log(f"Режим работы: {mode.upper()}")
        
        self.server_manager.load_servers()
        
        if len(self.server_manager.servers) == 0:
            Logger.log("Список серверов пуст, загружаем...")
            self.config_fetcher.fetch_configs()
        
        Logger.log("Тестирование серверов...")
        self.tester.test_all_servers()
        
        working_servers = self.server_manager.get_working_servers()
        
        if not working_servers:
            Logger.log("Нет доступных серверов!", "ERROR")
            if auto:
                Logger.log("Пытаемся подключиться к любому серверу...")
                for server in self.server_manager.servers:
                    if server["host"] not in self.server_manager.blacklist:
                        working_servers.append(server)
                        break
        
        if not working_servers:
            Logger.log("Критическая ошибка: нет серверов для подключения", "ERROR")
            return False
        
        best_server = working_servers[0]
        Logger.log(f"Подключение к серверу: {best_server['host']}:{best_server['port']}")
        
        if self.xray.start(best_server, mode):
            Logger.log("✓ VPN подключен!")
            Logger.log(f"  SOCKS5 прокси: 127.0.0.1:10808")
            Logger.log(f"  HTTP прокси: 127.0.0.1:10809")
            
            if mode == "split":
                Logger.log("  → Российские сайты: НАПРЯМУЮ")
                Logger.log("  → Иностранные сайты: через VPN")
            else:
                Logger.log("  → Весь трафик: через VPN")
            
            return True
        
        return False
    
    def disconnect(self):
        Logger.log("Отключение от VPN...")
        self.xray.stop()
        Logger.log("VPN отключен")
    
    def update_configs(self):
        Logger.log("Обновление списка серверов...")
        self.config_fetcher.fetch_configs()
        self.tester.test_all_servers()
    
    def run_auto(self, mode: str = "split"):
        self.running = True
        
        def signal_handler(sig, frame):
            Logger.log("Получен сигнал остановки")
            self.running = False
            self.disconnect()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        Logger.log("Запуск в режиме автоподдержки...")
        
        if not self.connect(mode):
            Logger.log("Не удалось подключиться, повторяем через 30 сек...")
        
        last_update = time.time()
        
        while self.running:
            time.sleep(10)
            
            if self.xray.xray_process and self.xray.xray_process.poll() is not None:
                Logger.log("Соединение разорвано, переподключение...", "WARN")
                self.connect(mode)
            
            if time.time() - last_update > self.auto_update_interval:
                Logger.log("Плановое обновление конфигов...")
                self.update_configs()
                
                if self.xray.current_server:
                    current = self.xray.current_server
                    if (current["host"] in self.server_manager.blacklist or 
                        current.get("status") == "offline"):
                        Logger.log("Текущий сервер недоступен, поиск нового...")
                        self.connect(mode)
                
                last_update = time.time()
    
    def status(self):
        print("\n" + "=" * 60)
        print("СТАТУС VPN КЛИЕНТА")
        print("=" * 60)
        
        if self.xray.current_server:
            print(f"✓ Подключен: {self.xray.current_server['host']}:{self.xray.current_server['port']}")
            print(f"  Сервер: {self.xray.current_server.get('name', 'N/A')}")
            print(f"  Задержка: {self.xray.current_server.get('latency', 'N/A')} мс")
        else:
            print("✗ Не подключен")
        
        print(f"\nВсего серверов: {len(self.server_manager.servers)}")
        
        online = sum(1 for s in self.server_manager.servers if s.get("status") == "online")
        print(f"Онлайн: {online}")
        print(f"Whitelist: {len(self.server_manager.whitelist)}")
        print(f"Blacklist: {len(self.server_manager.blacklist)}")
        
        print(f"\nПрокси:")
        print(f"  SOCKS5: 127.0.0.1:10808")
        print(f"  HTTP: 127.0.0.1:10809")
        print("=" * 60 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VLESS VPN Client с разделением трафика")
    parser.add_argument("command", choices=["start", "stop", "status", "update", "add-white", "add-black"],
                       help="Команда: start, stop, status, update, add-white, add-black")
    parser.add_argument("--mode", choices=["split", "full"], default="split",
                       help="split = РФ напрямую, full = всё через VPN")
    parser.add_argument("--host", help="Хост для whitelist/blacklist")
    parser.add_argument("--auto", action="store_true", help="Режим автоподдержки")
    
    args = parser.parse_args()
    
    client = VPNClient()
    
    if args.command == "start":
        if args.auto:
            client.run_auto(mode=args.mode)
        else:
            client.connect(mode=args.mode)
    
    elif args.command == "stop":
        client.disconnect()
    
    elif args.command == "status":
        client.status()
    
    elif args.command == "update":
        client.update_configs()
    
    elif args.command == "add-white":
        if args.host:
            client.server_manager.add_to_whitelist(args.host)
        else:
            print("Укажите --host")
    
    elif args.command == "add-black":
        if args.host:
            client.server_manager.add_to_blacklist(args.host)
        else:
            print("Укажите --host")


if __name__ == "__main__":
    main()
