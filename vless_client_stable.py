#!/usr/bin/env python3
"""
VLESS VPN Client - STABLE EDITION
Версия с повышенной стабильностью и авто-восстановлением
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
WHITELIST_FILE = DATA_DIR / "whitelist.txt"
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"
SERVERS_FILE = DATA_DIR / "servers.json"
LOG_FILE = LOGS_DIR / "client.log"

# Создаем директории
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Источники
GITHUB_REPO = "igareck/vpn-configs-for-russia"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"


class Logger:
    """Стабильный логгер с буферизацией"""
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        """Логирование с защитой от ошибок"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"
            
            # Пишем в лог файл с буферизацией
            with open(LOG_FILE, "a", buffering=1) as f:
                f.write(log_line)
            
            # Дублируем в stdout
            print(log_line, end="", flush=True)
            
        except Exception as e:
            print(f"[ERROR] Logger failed: {e}", file=sys.stderr)


class ServerManager:
    """Менеджер серверов с кэшированием"""
    
    def __init__(self):
        self.servers = []
        self.whitelist = set()
        self.blacklist = set()
        
    def load_servers(self):
        """Загрузка серверов с защитой от ошибок"""
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
                Logger.log(f"Загружено серверов из кэша: {len(self.servers)}")
            else:
                Logger.log("Кэш серверов не найден", "WARNING")
                self.servers = []
        except Exception as e:
            Logger.log(f"Ошибка загрузки кэша: {e}", "ERROR")
            self.servers = []
    
    def save_servers(self):
        """Сохранение серверов"""
        try:
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.servers, f, indent=2, ensure_ascii=False)
            Logger.log(f"Сохранено серверов: {len(self.servers)}")
        except Exception as e:
            Logger.log(f"Ошибка сохранения: {e}", "ERROR")
    
    def load_lists(self):
        """Загрузка white/black списков"""
        try:
            if WHITELIST_FILE.exists():
                with open(WHITELIST_FILE) as f:
                    self.whitelist = set(line.strip() for line in f if line.strip())
            
            if BLACKLIST_FILE.exists():
                with open(BLACKLIST_FILE) as f:
                    self.blacklist = set(line.strip() for line in f if line.strip())
            
            Logger.log(f"Загружено whitelist: {len(self.whitelist)}, blacklist: {len(self.blacklist)}")
        except Exception as e:
            Logger.log(f"Ошибка загрузки списков: {e}", "ERROR")
    
    def get_working_servers(self):
        """Получить рабочие серверы"""
        return [s for s in self.servers if s.get("status") == "online" and s.get("latency", 9999) < 500]


class ConfigFetcher:
    """Загрузка конфигов с GitHub"""
    
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
    
    def fetch_configs(self):
        """Загрузка конфигов с повторными попытками"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                Logger.log(f"Загрузка конфигов из GitHub (попытка {attempt + 1}/{max_retries})...")
                
                # Запрос к GitHub API
                req = urllib.request.Request(
                    GITHUB_API_BASE,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode())
                
                # Парсинг файлов
                files = [f for f in data if f["name"].endswith(".txt")]
                Logger.log(f"Найдено файлов с VLESS: {len(files)}")
                
                all_servers = []
                for file_info in files:
                    servers = self._parse_file(file_info)
                    all_servers.extend(servers)
                    Logger.log(f"  Обработан {file_info['name']}: {len(servers)} серверов")
                
                self.server_manager.servers = all_servers
                self.server_manager.save_servers()
                Logger.log(f"Всего серверов: {len(all_servers)}")
                return True
                
            except Exception as e:
                Logger.log(f"Ошибка загрузки (попытка {attempt + 1}): {e}", "ERROR")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    Logger.log("Все попытки загрузки исчерпаны", "ERROR")
                    return False
        
        return False
    
    def _parse_file(self, file_info: dict) -> list:
        """Парсинг файла с серверами"""
        servers = []
        try:
            response = urllib.request.urlopen(file_info["download_url"], timeout=30)
            content = response.read().decode("utf-8")
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("vless://"):
                    server = self._parse_vless(line)
                    if server:
                        servers.append(server)
        except Exception as e:
            Logger.log(f"Ошибка парсинга {file_info['name']}: {e}", "ERROR")
        
        return servers
    
    def _parse_vless(self, url: str) -> Optional[dict]:
        """Парсинг VLESS ссылки"""
        try:
            # Упрощённый парсинг
            parts = url.replace("vless://", "").split("@")
            if len(parts) != 2:
                return None
            
            uuid = parts[0].split(":")[0] if ":" in parts[0] else parts[0]
            host_port = parts[1].split("?")[0]
            host, port = host_port.rsplit(":", 1)
            
            return {
                "uuid": uuid,
                "host": host,
                "port": int(port),
                "name": url.split("#")[-1] if "#" in url else f"{host}:{port}",
                "status": "online",
                "latency": 9999
            }
        except Exception as e:
            Logger.log(f"Ошибка парсинга VLESS: {e}", "ERROR")
            return None


class ServerTester:
    """Тестирование серверов"""
    
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
    
    def test_all_servers(self):
        """Тестирование всех серверов"""
        servers = self.server_manager.servers
        if not servers:
            Logger.log("Нет серверов для тестирования", "ERROR")
            return
        
        Logger.log(f"Начало тестирования {len(servers)} серверов...")
        online = 0
        offline = 0
        
        # Тестируем только первые 100 для скорости
        for i, server in enumerate(servers[:100]):
            if self._test_server(server):
                online += 1
            else:
                offline += 1
            
            # Прогресс каждые 20 серверов
            if (i + 1) % 20 == 0:
                Logger.log(f"Тестирование: {i + 1}/{len(servers[:100])}")
        
        Logger.log(f"Тестирование завершено: онлайн={online}, оффлайн={offline}")
    
    def _test_server(self, server: dict) -> bool:
        """Тест одного сервера"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server["host"], server["port"]))
            sock.close()
            
            if result == 0:
                server["status"] = "online"
                server["latency"] = 50  # Примерное значение
                return True
            else:
                server["status"] = "offline"
                return False
        except Exception:
            server["status"] = "offline"
            return False


class XRayController:
    """Контроллер XRay"""
    
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.process = None
    
    def start(self, server: dict) -> bool:
        """Запуск XRay"""
        try:
            # Создание конфига
            config = self._generate_config(server)
            config_file = CONFIG_DIR / "config.json"
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            Logger.log(f"Конфиг создан: {config_file}")
            
            # Запуск XRay
            xray_path = Path.home() / "vpn-client" / "bin" / "xray"
            if not xray_path.exists():
                Logger.log("XRay не установлен!", "ERROR")
                return False
            
            cmd = [str(xray_path), "run", "-c", str(config_file)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждём запуска
            time.sleep(2)
            
            if self.process.poll() is None:
                Logger.log("XRay запущен")
                return True
            else:
                Logger.log("XRay не запустился", "ERROR")
                return False
                
        except Exception as e:
            Logger.log(f"Ошибка запуска XRay: {e}", "ERROR")
            return False
    
    def stop(self):
        """Остановка XRay"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                Logger.log("XRay остановлен")
        except Exception as e:
            Logger.log(f"Ошибка остановки: {e}", "ERROR")
        
        # Принудительная остановка
        try:
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        except Exception:
            pass
    
    def _generate_config(self, server: dict) -> dict:
        """Генерация конфига XRay"""
        return {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": 10808,
                    "protocol": "socks",
                    "settings": {
                        "auth": "noauth",
                        "udp": True
                    }
                },
                {
                    "port": 10809,
                    "protocol": "http"
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": server["host"],
                                "port": server["port"],
                                "users": [
                                    {
                                        "id": server.get("uuid", ""),
                                        "encryption": "none",
                                        "flow": ""
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "tls",
                        "tlsSettings": {
                            "serverName": server.get("sni", server["host"]),
                            "alpn": ["http/1.1"]
                        }
                    }
                }
            ]
        }


class VPNClient:
    """Основной клиент с авто-восстановлением"""
    
    def __init__(self):
        self.server_manager = ServerManager()
        self.config_fetcher = ConfigFetcher(self.server_manager)
        self.tester = ServerTester(self.server_manager)
        self.xray = XRayController(self.server_manager)
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def connect(self, auto: bool = True, mode: str = "split") -> bool:
        """Подключение с авто-восстановлением"""
        Logger.log("=" * 60)
        Logger.log("Запуск VPN клиента (STABLE EDITION v2)...")
        Logger.log(f"Режим работы: {mode.upper()}")
        Logger.log("=" * 60)
        
        # Загрузка списков
        self.server_manager.load_lists()
        
        # Загрузка кэша
        self.server_manager.load_servers()
        
        # Если нет серверов - обновляем
        if len(self.server_manager.servers) == 0:
            Logger.log("Список серверов пуст, загружаем...")
            if not self.config_fetcher.fetch_configs():
                Logger.log("Не удалось загрузить серверы", "ERROR")
                return False
        
        # Тестирование (только первые 50 для скорости)
        Logger.log("Тестирование серверов (первые 50)...")
        self.tester.test_all_servers()
        
        # Поиск рабочих серверов
        working_servers = self.server_manager.get_working_servers()
        
        if not working_servers:
            Logger.log("Нет рабочих серверов!", "ERROR")
            # Пробуем подключиться к любому из blacklist
            for server in self.server_manager.servers:
                if server["host"] not in self.server_manager.blacklist:
                    working_servers.append(server)
                    break
        
        if not working_servers:
            Logger.log("Критическая ошибка: нет серверов", "ERROR")
            return False
        
        # Подключение
        best_server = working_servers[0]
        Logger.log(f"Подключение к серверу: {best_server['host']}:{best_server['port']}")
        
        if self.xray.start(best_server):
            Logger.log("✅ VPN ПОДКЛЮЧЕН!")
            Logger.log(f"  SOCKS5 прокси: 127.0.0.1:10808")
            Logger.log(f"  HTTP прокси: 127.0.0.1:10809")
            Logger.log(f"  Режим: {'SPLIT' if mode == 'split' else 'FULL'}")
            
            # Запуск мониторинга
            self.running = True
            self._start_monitoring()
            
            # Ожидание сигнала остановки (теперь не выходим сразу!)
            while self.running:
                time.sleep(1)
            
            return True
        
        return False
    
    def disconnect(self):
        """Отключение"""
        Logger.log("Отключение от VPN...")
        self.running = False
        self.xray.stop()
        Logger.log("VPN отключен")
    
    def _start_monitoring(self):
        """Мониторинг подключения с авто-восстановлением"""
        def monitor():
            while self.running:
                try:
                    # Проверка процесса XRay
                    result = subprocess.run(
                        ["pgrep", "-f", "xray"],
                        capture_output=True
                    )
                    
                    if result.returncode != 0:
                        Logger.log("⚠️ XRay не запущен! Попытка восстановления...", "WARNING")
                        self._reconnect()
                    
                    time.sleep(5)
                except Exception as e:
                    Logger.log(f"Ошибка мониторинга: {e}", "ERROR")
                    time.sleep(3)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _reconnect(self):
        """Попытка переподключения"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            Logger.log("Превышено количество попыток подключения", "ERROR")
            self.running = False
            return
        
        self.reconnect_attempts += 1
        Logger.log(f"Попытка восстановления {self.reconnect_attempts}/{self.max_reconnect_attempts}...")
        
        # Остановка
        self.xray.stop()
        time.sleep(2)
        
        # Запуск
        working_servers = self.server_manager.get_working_servers()
        if working_servers:
            if self.xray.start(working_servers[0]):
                Logger.log("✅ Соединение восстановлено!")
                self.reconnect_attempts = 0
            else:
                Logger.log("❌ Не удалось восстановить соединение", "ERROR")
        else:
            Logger.log("❌ Нет доступных серверов", "ERROR")


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VLESS VPN Client - STABLE")
    parser.add_argument("command", choices=["start", "stop", "status", "update"],
                        help="Команда: start, stop, status, update")
    parser.add_argument("--auto", action="store_true", help="Автоподключение")
    parser.add_argument("--mode", choices=["split", "full"], default="split",
                        help="Режим работы")
    
    args = parser.parse_args()
    
    client = VPNClient()
    
    # Обработка сигналов
    def signal_handler(sig, frame):
        Logger.log("Получен сигнал остановки")
        client.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.command == "start":
        success = client.connect(auto=args.auto, mode=args.mode)
        
        if success:
            # Ожидание сигнала остановки
            while client.running:
                time.sleep(1)
        else:
            Logger.log("Не удалось подключиться", "ERROR")
            sys.exit(1)
    
    elif args.command == "stop":
        client.disconnect()
    
    elif args.command == "status":
        print("\n" + "=" * 60)
        print("СТАТУС VPN КЛИЕНТА")
        print("=" * 60)
        
        # Проверка процесса
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
        if result.returncode == 0:
            print("✓ Подключен")
        else:
            print("✗ Не подключен")
        
        print(f"\nВсего серверов: {len(client.server_manager.servers)}")
        print(f"Онлайн: {len(client.server_manager.get_working_servers())}")
        print(f"Whitelist: {len(client.server_manager.whitelist)}")
        print(f"Blacklist: {len(client.server_manager.blacklist)}")
        
        print("\nПрокси:")
        print("  SOCKS5: 127.0.0.1:10808")
        print("  HTTP: 127.0.0.1:10809")
        print("=" * 60)
    
    elif args.command == "update":
        Logger.log("Обновление списка серверов...")
        client.config_fetcher.fetch_configs()


if __name__ == "__main__":
    main()
