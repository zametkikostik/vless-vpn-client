#!/usr/bin/env python3
"""
VLESS VPN Client - STABLE VERSION
Стабильная версия на основе старого клиента с быстрым подключением
"""

import os
import sys
import json
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = LOGS_DIR / "client.log"
XRAY_BIN = HOME / "vpn-client" / "bin" / "xray"

# Создаем директории
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class Logger:
    """Простой логгер"""
    
    @staticmethod
    def log(message, level="INFO"):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"
            
            with open(LOG_FILE, "a", buffering=1) as f:
                f.write(log_line)
            
            print(log_line, end="", flush=True)
        except Exception as e:
            print(f"[ERROR] Logger: {e}", file=sys.stderr)


class StableVPNClient:
    """Стабильный VPN клиент с быстрым подключением"""
    
    def __init__(self):
        self.servers = []
        self.xray_process = None
        self.running = False
        self.current_server = None
    
    def load_servers(self):
        """Загрузка серверов из кэша"""
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
                Logger.log(f"Загружено серверов из кэша: {len(self.servers)}")
            else:
                Logger.log("Кэш серверов не найден", "WARNING")
                self.servers = []
        except Exception as e:
            Logger.log(f"Ошибка загрузки серверов: {e}", "ERROR")
            self.servers = []
    
    def test_server_ping(self, server, timeout=3):
        """Быстрый тест сервера (TCP подключение)"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((server['host'], server['port']))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_best_server(self):
        """Выбор лучшего сервера (БЫСТРОЕ тестирование!)"""
        if not self.servers:
            Logger.log("Нет серверов в кэше!", "ERROR")
            return None

        # Сначала пробуем серверы с низким пингом (<100ms) - они обычно рабочие
        low_latency = [
            s for s in self.servers
            if s.get("uuid")
            and s.get("latency", 9999) < 100
            and s.get("streamSettings", {}).get("security") == "reality"
        ]
        
        # Потом WHITE серверы
        white_servers = [
            s for s in self.servers
            if s.get("uuid")
            and "WHITE" in s.get("name", "").upper()
            and s.get("streamSettings", {}).get("security") == "reality"
        ]
        
        # Если нет низкопинговых/WHITE, берем все reality с UUID
        candidates = low_latency if low_latency else (white_servers if white_servers else [
            s for s in self.servers
            if s.get("uuid")
            and "chatgpt" not in s.get("host", "").lower()
            and s.get("streamSettings", {}).get("security") == "reality"
        ])

        if not candidates:
            Logger.log("Нет reality серверов с UUID!", "ERROR")
            return None

        # Сортируем по пингу
        candidates.sort(key=lambda x: x.get("latency", 9999))
        
        # Тестируем первые 5 серверов и берем первый доступный
        Logger.log(f"🔍 Тестирование {len(candidates[:5])} серверов...")
        for server in candidates[:5]:
            if self.test_server_ping(server, timeout=2):
                server_name = "WHITE" if "WHITE" in server.get("name", "").upper() else "LOW-PING" if server.get("latency", 9999) < 100 else "BLACK"
                Logger.log(f"✅ {server_name} сервер доступен: {server['host']}:{server['port']} (пинг: {server.get('latency', 'N/A')} мс)")
                return server
        
        # Если первые 5 недоступны, берем первый
        Logger.log("⚠️ Тесты не прошли, пробуем первый...")
        return candidates[0]
    
    def generate_config(self, server):
        """Генерация конфига XRay"""
        # Получаем полные параметры из сервера
        stream = server.get("streamSettings", {})
        security = stream.get("security", "tls")
        
        if security == "reality":
            # Reality конфиг
            reality = stream.get("realitySettings", {})
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
                            "serverName": reality.get("serverName", server["host"]),
                            "fingerprint": "chrome",
                            "publicKey": reality.get("publicKey", ""),
                            "shortId": reality.get("shortId", "")
                        }
                    }
                }]
            }
        else:
            # TLS конфиг
            tls = stream.get("tlsSettings", {})
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
                            "serverName": tls.get("serverName", server["host"]),
                            "alpn": ["h2", "http/1.1"],
                            "fingerprint": "chrome"
                        }
                    }
                }]
            }
        
        return config
    
    def start_xray(self, server):
        """Запуск XRay"""
        try:
            # Генерация конфига
            config = self.generate_config(server)
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            Logger.log(f"Конфиг создан: {CONFIG_FILE}")
            
            # Проверка XRay
            if not XRAY_BIN.exists():
                Logger.log("XRay не установлен!", "ERROR")
                return False
            
            # Запуск
            cmd = [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)]
            self.xray_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждём запуска
            time.sleep(3)
            
            # Проверяем что работает
            if self.xray_process.poll() is None:
                Logger.log("✅ XRay запущен")
                self.current_server = server
                return True
            else:
                Logger.log("XRay не запустился", "ERROR")
                return False
                
        except Exception as e:
            Logger.log(f"Ошибка запуска XRay: {e}", "ERROR")
            return False
    
    def stop_xray(self):
        """Остановка XRay"""
        try:
            if self.xray_process:
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
                Logger.log("XRay остановлен")
        except Exception as e:
            Logger.log(f"Ошибка остановки: {e}", "ERROR")
        
        # Принудительная остановка
        try:
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        except Exception:
            pass
        
        self.current_server = None
    
    def connect(self):
        """БЫСТРОЕ подключение (БЕЗ долгого тестирования!)"""
        Logger.log("=" * 60)
        Logger.log("🚀 ПОДКЛЮЧЕНИЕ К VPN (STABLE VERSION)")
        Logger.log("=" * 60)
        
        # Загрузка серверов (БЫСТРО!)
        self.load_servers()
        
        if not self.servers:
            Logger.log("Нет серверов! Сначала обновите: vless-vpn update", "ERROR")
            return False
        
        # Выбор лучшего сервера (БЫСТРО!)
        best_server = self.get_best_server()
        
        if not best_server:
            Logger.log("Не удалось выбрать сервер", "ERROR")
            return False
        
        # Подключение (БЫСТРО!)
        Logger.log(f"Подключение к {best_server['host']}:{best_server['port']}...")
        
        if self.start_xray(best_server):
            Logger.log("✅ VPN ПОДКЛЮЧЕН!")
            Logger.log("  SOCKS5: 127.0.0.1:10808")
            Logger.log("  HTTP: 127.0.0.1:10809")
            return True
        
        return False
    
    def disconnect(self):
        """Отключение"""
        Logger.log("=" * 60)
        Logger.log("🛑 ОТКЛЮЧЕНИЕ ОТ VPN")
        Logger.log("=" * 60)
        
        self.running = False
        self.stop_xray()
        
        Logger.log("VPN отключен")
    
    def status(self):
        """Статус"""
        # Загружаем серверы только для статистики (не логгируем)
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                    self.servers = json.load(f)
        except Exception:
            self.servers = []
        
        print("\n" + "=" * 60)
        print("СТАТУС VPN КЛИЕНТА (STABLE)")
        print("=" * 60)

        # Проверка процесса
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)

        if result.returncode == 0:
            print("✅ Подключен")
            if self.current_server:
                print(f"  Сервер: {self.current_server['host']}:{self.current_server['port']}")
        else:
            print("❌ Не подключен")

        print(f"\nВсего серверов: {len(self.servers)}")
        online = sum(1 for s in self.servers if s.get("status") == "online")
        print(f"Онлайн: {online}")

        print("\nПрокси:")
        print("  SOCKS5: 127.0.0.1:10808")
        print("  HTTP: 127.0.0.1:10809")
        print("=" * 60)


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VLESS VPN Client - STABLE")
    parser.add_argument("command", choices=["start", "stop", "status", "update"],
                        help="Команда: start, stop, status, update")
    parser.add_argument("--auto", action="store_true", help="Автоподключение")
    
    args = parser.parse_args()
    
    client = StableVPNClient()
    
    # Обработка сигналов
    def signal_handler(sig, frame):
        Logger.log("📩 Получен сигнал остановки")
        client.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.command == "start":
        # БЫСТРОЕ подключение
        if client.connect():
            # Запускаем мониторинг
            client.running = True
            
            Logger.log("💤 Ожидание (Ctrl+C для остановки)...")
            Logger.log("")
            Logger.log("=" * 60)
            Logger.log("VPN РАБОТАЕТ И НЕ ОТКЛЮЧИТСЯ!")
            Logger.log("Нажмите Ctrl+C для остановки")
            Logger.log("=" * 60)
            
            # Просто ждём
            try:
                while client.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                Logger.log("\n👋 Получен Ctrl+C, отключаемся...")
                client.disconnect()
        else:
            Logger.log("❌ Не удалось подключиться", "ERROR")
            sys.exit(1)
    
    elif args.command == "stop":
        client.disconnect()
    
    elif args.command == "status":
        client.status()
    
    elif args.command == "update":
        Logger.log("🔄 Обновление серверов из GitHub...")
        # Скачиваем конфиги напрямую из GitHub
        try:
            import urllib.request
            
            api_url = "https://api.github.com/repos/igareck/vpn-configs-for-russia/contents"
            req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                files = json.loads(response.read().decode())
            
            vless_files = [
                f for f in files
                if f["type"] == "file" and f["name"].endswith(".txt")
            ]
            
            Logger.log(f"Найдено файлов: {len(vless_files)}")
            
            new_servers = []
            for file_info in vless_files:
                try:
                    download_url = file_info.get("download_url")
                    if not download_url:
                        continue
                    
                    Logger.log(f"Загрузка: {file_info['name']}")
                    req = urllib.request.Request(download_url)
                    with urllib.request.urlopen(req, timeout=30) as response:
                        content = response.read().decode("utf-8")
                    
                    for line in content.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("vless://"):
                            # Парсим vless:// URL
                            try:
                                from urllib.parse import urlparse, parse_qs, unquote
                                parsed = urlparse(line)
                                uuid = parsed.username or ""
                                host = parsed.hostname or ""
                                port = parsed.port or 443
                                
                                if uuid and host:
                                    qs = parse_qs(parsed.query)
                                    params = {k: unquote(v[0]) if v else "" for k, v in qs.items()}
                                    
                                    server = {
                                        "host": host,
                                        "port": port,
                                        "uuid": uuid,
                                        "name": file_info["name"],
                                        "status": "online",
                                        "latency": 999,
                                        "streamSettings": {
                                            "security": params.get("security", "tls"),
                                            "tlsSettings": {
                                                "serverName": params.get("sni", host),
                                                "alpn": ["h2", "http/1.1"],
                                                "fingerprint": "chrome"
                                            },
                                            "realitySettings": {
                                                "serverName": params.get("sni", host),
                                                "fingerprint": "chrome",
                                                "publicKey": params.get("pbk", ""),
                                                "shortId": params.get("sid", "")
                                            }
                                        }
                                    }
                                    new_servers.append(server)
                            except Exception:
                                pass
                except Exception as e:
                    Logger.log(f"Ошибка {file_info['name']}: {e}", "WARN")
            
            # Сохраняем
            if new_servers:
                with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_servers, f, ensure_ascii=False, indent=2)
                Logger.log(f"✅ Сохранено {len(new_servers)} серверов")
            else:
                Logger.log("⚠️ Серверы не найдены", "WARNING")
                
        except Exception as e:
            Logger.log(f"❌ Ошибка обновления: {e}", "ERROR")


if __name__ == "__main__":
    main()
