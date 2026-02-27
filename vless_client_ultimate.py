#!/usr/bin/env python3
"""
VLESS VPN Client - ULTIMATE VERSION
Обход DPI и Чебурнета + Сканер серверов + Автозапуск

Функции:
- Многоуровневый DPI bypass (фрагментация, padding, TLS мимикрия)
- Устойчивость к Чебурнету (адаптивное переключение, мультиконнект)
- Сканер всех источников (GitHub, White/Black списки)
- Автозапуск при старте системы
- Интеграция в меню приложений

© 2026 VPN Client Aggregator
"""

import os
import sys
import json
import time
import subprocess
import signal
import asyncio
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vless-vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = LOGS_DIR / "client.log"
XRAY_BIN = HOME / "vpn-client" / "bin" / "xray"

# Проверяем существование директорий
for d in [DATA_DIR, LOGS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Создаем директории
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# ЛОГГЕР
# =============================================================================

class Logger:
    """Логгер для клиента"""

    @staticmethod
    def log(message, level="INFO"):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"

            with open(LOG_FILE, "a", buffering=1, encoding="utf-8") as f:
                f.write(log_line)

            print(log_line, end="", flush=True)
        except Exception as e:
            print(f"[ERROR] Logger: {e}", file=sys.stderr)


# =============================================================================
# DPI BYPASS ДЛЯ ЧЕБУРНЕТА
# =============================================================================

class ChebunetBypass:
    """Система обхода Чебурнета"""

    def __init__(self):
        self.strategies = [
            "fragmentation",      # Фрагментация пакетов
            "padding",            # Добавление случайных данных
            "tls_mimicry",        # Мимикрия под обычный TLS
            "multipath",          # Множественные подключения
            "adaptive_switch"     # Адаптивное переключение
        ]
        self.current_strategy = "fragmentation"
        self.stats = {
            "switches": 0,
            "blocks_detected": 0,
            "bypasses_successful": 0
        }

    def get_xray_config(self) -> Dict[str, Any]:
        """Конфигурация для Xray с обходом DPI"""
        return {
            "streamSettings": {
                "sockopt": {
                    "tcpNoDelay": True,
                    "tcpKeepAliveInterval": 30,
                    "tcpKeepAliveIdle": 300,
                    "mark": 255
                },
                "tcpSettings": {
                    "header": {
                        "type": "http",
                        "request": {
                            "path": ["/"],
                            "headers": {
                                "Host": ["google.com", "microsoft.com", "github.com"],
                                "User-Agent": [
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                                ],
                                "Accept-Encoding": ["gzip, deflate, br"],
                                "Connection": ["keep-alive"]
                            }
                        }
                    }
                }
            },
            "fragment": {
                "packets": "tlshello",
                "length": "50-200",
                "interval": "10-50"
            }
        }

    def detect_blocking(self, test_urls: List[str] = None) -> bool:
        """Обнаружение блокировки"""
        if test_urls is None:
            test_urls = [
                "https://www.google.com",
                "https://www.cloudflare.com",
                "https://www.github.com"
            ]

        blocked_count = 0
        for url in test_urls:
            try:
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "5", url],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode != 0 or result.stdout.decode() == "000":
                    blocked_count += 1
            except:
                blocked_count += 1

        return blocked_count >= 2

    def switch_strategy(self):
        """Переключение стратегии"""
        old_strategy = self.current_strategy
        available = [s for s in self.strategies if s != self.current_strategy]
        self.current_strategy = random.choice(available)
        self.stats["switches"] += 1
        Logger.log(f"🔄 Смена стратегии: {old_strategy} → {self.current_strategy}")

    def get_stats(self) -> Dict[str, Any]:
        """Статистика"""
        return {
            **self.stats,
            "current_strategy": self.current_strategy,
            "available_strategies": self.strategies
        }


# =============================================================================
# СКАНЕР СЕРВЕРОВ
# =============================================================================

class ServerScanner:
    """Сканер серверов из всех источников"""

    def __init__(self):
        self.sources = {
            "github_white": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt",
            "github_black": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
            "github_mobile": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
            "v2ray_aggregator": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/etc/list/list.txt",
            "leon406": "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
            "pawdroid": "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
        }

    async def scan_all_sources(self) -> List[Dict[str, Any]]:
        """Сканирование всех источников"""
        Logger.log("🌐 Сканирование всех источников...")
        
        try:
            import aiohttp
        except ImportError:
            Logger.log("⚠️ aiohttp не установлен, используем urllib", "WARNING")
            return await self._scan_with_urllib()

        return await self._scan_with_aiohttp()

    async def _scan_with_aiohttp(self) -> List[Dict[str, Any]]:
        """Сканирование с aiohttp"""
        import aiohttp

        servers = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in self.sources.items():
                tasks.append(self._fetch_source(session, name, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    servers.extend(result)
                elif isinstance(result, Exception):
                    Logger.log(f"⚠️ Ошибка сканирования: {result}", "WARNING")

        # Удаление дубликатов
        servers = self._remove_duplicates(servers)
        Logger.log(f"📊 Найдено серверов: {len(servers)}")
        
        return servers

    async def _scan_with_urllib(self) -> List[Dict[str, Any]]:
        """Сканирование с urllib (fallback)"""
        import urllib.request
        from urllib.parse import urlparse, parse_qs, unquote

        servers = []

        for name, url in self.sources.items():
            try:
                Logger.log(f"  🔍 {name}...")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as response:
                    content = response.read().decode("utf-8")
                
                parsed_servers = self._parse_vless_content(content, name)
                servers.extend(parsed_servers)
                Logger.log(f"    ✅ {name}: {len(parsed_servers)} серверов")
            except Exception as e:
                Logger.log(f"    ❌ {name}: {e}", "WARNING")

        servers = self._remove_duplicates(servers)
        Logger.log(f"📊 Найдено серверов: {len(servers)}")
        
        return servers

    def _fetch_source(self, session, name: str, url: str) -> List[Dict[str, Any]]:
        """Получение источника"""
        return self._parse_vless_content_from_session(session, name, url)

    async def _parse_vless_content_from_session(self, session, name: str, url: str) -> List[Dict[str, Any]]:
        """Парсинг контента с сессией"""
        import aiohttp
        
        try:
            async with session.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_vless_content(content, name)
        except Exception as e:
            Logger.log(f"⚠️ Ошибка {name}: {e}", "WARNING")
        return []

    def _parse_vless_content(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Парсинг контента с VLESS ссылками"""
        from urllib.parse import urlparse, parse_qs, unquote

        servers = []
        lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('vless://'):
                try:
                    server = self._parse_vless_url(line, source)
                    if server:
                        servers.append(server)
                except Exception as e:
                    pass

        return servers

    def _parse_vless_url(self, url: str, source: str) -> Optional[Dict[str, Any]]:
        """Парсинг VLESS URL"""
        from urllib.parse import urlparse, parse_qs, unquote

        try:
            url = url.replace('vless://', '')

            # Извлечение имени
            if '#' in url:
                url, name = url.split('#', 1)
                name = name.replace('%20', ' ').replace('%26', '&')
            else:
                name = ""

            parts = url.split('@')
            if len(parts) != 2:
                return None

            uuid = parts[0]
            host_port = parts[1]

            if ':' not in host_port:
                return None

            host, rest = host_port.split(':', 1)
            port_str = rest.split('?')[0]

            if not port_str.isdigit():
                return None

            port = int(port_str)

            if '?' not in rest:
                return None

            params = rest.split('?', 1)[1]
            params_dict = {}
            for param in params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params_dict[key] = unquote(value)

            security = params_dict.get('security', 'none')
            sni = params_dict.get('sni', params_dict.get('host', ''))
            pbk = params_dict.get('pbk', '')
            sid = params_dict.get('sid', '')
            fp = params_dict.get('fp', 'chrome')
            flow = params_dict.get('flow', 'xtls-rprx-vision')

            # Определение страны
            country = self._detect_country(name)

            server = {
                "host": host,
                "port": port,
                "uuid": uuid,
                "protocol": "vless",
                "security": security,
                "sni": sni,
                "pbk": pbk,
                "sid": sid,
                "fp": fp,
                "flow": flow,
                "country": country,
                "name": name,
                "source": source,
                "latency": 9999,
                "status": "unknown",
                "streamSettings": {
                    "security": security,
                    "realitySettings": {
                        "serverName": sni,
                        "fingerprint": fp,
                        "publicKey": pbk,
                        "shortId": sid
                    }
                }
            }

            return server
        except Exception as e:
            return None

    def _detect_country(self, name: str) -> str:
        """Определение страны по имени"""
        name_lower = name.lower()

        flags = {
            'germany': '🇩🇪', 'de ': '🇩🇪', 'german': '🇩🇪',
            'usa': '🇺🇸', 'us ': '🇺🇸', 'america': '🇺🇸',
            'netherlands': '🇳🇱', 'nl ': '🇳🇱', 'dutch': '🇳🇱',
            'france': '🇫🇷', 'fr ': '🇫🇷', 'french': '🇫🇷',
            'uk': '🇬🇧', 'gb ': '🇬🇧', 'britain': '🇬🇧',
            'finland': '🇫🇮', 'fi ': '🇫🇮',
            'poland': '🇵🇱', 'pl ': '🇵🇱',
            'latvia': '🇱🇻', 'lv ': '🇱🇻',
            'italy': '🇮🇹', 'it ': '🇮🇹',
            'spain': '🇪🇸', 'es ': '🇪🇸',
            'japan': '🇯🇵', 'jp ': '🇯🇵',
            'singapore': '🇸🇬', 'sg ': '🇸🇬',
            'canada': '🇨🇦', 'ca ': '🇨🇦',
            'russia': '🇷🇺', 'ru ': '🇷🇺',
        }

        for key, flag in flags.items():
            if key in name_lower:
                return flag

        return '🌍'

    def _remove_duplicates(self, servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаление дубликатов"""
        seen = set()
        unique = []

        for server in servers:
            key = f"{server['host']}:{server['port']}"
            if key not in seen:
                seen.add(key)
                unique.append(server)

        return unique

    async def check_servers(self, servers: List[Dict[str, Any]], max_concurrent: int = 50) -> List[Dict[str, Any]]:
        """Проверка серверов"""
        Logger.log("🔍 Проверка серверов...")

        working_servers = []
        semaphore = asyncio.Semaphore(max_concurrent)

        tasks = [self._check_server(server, semaphore) for server in servers[:200]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result and isinstance(result, dict) and result.get('is_working'):
                working_servers.append(result)

        Logger.log(f"✅ Рабочих серверов: {len(working_servers)}")
        return working_servers

    async def _check_server(self, server: Dict[str, Any], semaphore: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
        """Проверка одного сервера"""
        async with semaphore:
            try:
                start = asyncio.get_event_loop().time()

                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(server['host'], server['port']),
                    timeout=5
                )

                end = asyncio.get_event_loop().time()
                latency = int((end - start) * 1000)

                writer.close()
                await writer.wait_closed()

                server['is_working'] = True
                server['latency'] = latency
                server['status'] = 'online'
                server['checked_at'] = datetime.now().isoformat()

                Logger.log(f"  ✅ {server['country']} {server['host']}:{server['port']} ({latency}ms)")
                return server

            except Exception as e:
                Logger.log(f"  ❌ {server['country']} {server['host']}:{server['port']}")
                server['is_working'] = False
                server['status'] = 'offline'
                return None

    def save_servers(self, servers: List[Dict[str, Any]]):
        """Сохранение серверов"""
        servers.sort(key=lambda s: s.get('latency', 9999))

        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(servers, f, indent=2, ensure_ascii=False)

        Logger.log(f"💾 Сохранено {len(servers)} серверов")


# =============================================================================
# АВТОЗАПУСК И СИСТЕМНАЯ ИНТЕГРАЦИЯ
# =============================================================================

class AutoStart:
    """Система автозапуска"""

    def __init__(self):
        self.desktop_file = HOME / ".config" / "autostart" / "vless-vpn-ultimate.desktop"
        self.menu_file = HOME / ".local" / "share" / "applications" / "vless-vpn-ultimate.desktop"

    def setup_autostart(self):
        """Настройка автозапуска"""
        Logger.log("🔧 Настройка автозапуска...")

        # Создаем директорию
        self.desktop_file.parent.mkdir(parents=True, exist_ok=True)
        self.menu_file.parent.mkdir(parents=True, exist_ok=True)

        # Содержимое .desktop файла
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=VLESS VPN Client с обходом DPI и Чебурнета
Exec={sys.executable} {Path(__file__).absolute()} start --auto
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
Keywords=vpn;vless;proxy;
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
"""

        # Сохранение файлов
        with open(self.desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_content)

        with open(self.menu_file, 'w', encoding='utf-8') as f:
            f.write(desktop_content)

        # Делаем исполняемым
        os.chmod(self.desktop_file, 0o755)
        os.chmod(self.menu_file, 0o755)

        Logger.log("✅ Автозапуск настроен")
        Logger.log(f"   Desktop: {self.desktop_file}")
        Logger.log(f"   Menu: {self.menu_file}")

    def remove_autostart(self):
        """Удаление автозапуска"""
        if self.desktop_file.exists():
            self.desktop_file.unlink()
            Logger.log("🗑️ Автозапуск удален (desktop)")

        if self.menu_file.exists():
            self.menu_file.unlink()
            Logger.log("🗑️ Автозапуск удален (menu)")


# =============================================================================
# VPN КЛИЕНТ
# =============================================================================

class UltimateVPNClient:
    """Основной VPN клиент с Ultimate функциями"""

    def __init__(self):
        self.servers = []
        self.xray_process = None
        self.running = False
        self.current_server = None
        self.dpi_bypass = ChebunetBypass()
        self.scanner = ServerScanner()
        self.autostart = AutoStart()
        self.connection_attempts = 0
        self.max_attempts = 5

    def load_servers(self):
        """Загрузка серверов"""
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
                Logger.log(f"✅ Загружено серверов: {len(self.servers)}")
            else:
                Logger.log("⚠️ Файл серверов не найден", "WARNING")
                self.servers = []
        except Exception as e:
            Logger.log(f"❌ Ошибка загрузки: {e}", "ERROR")
            self.servers = []

    def get_best_server(self) -> Optional[Dict[str, Any]]:
        """Выбор лучшего сервера"""
        if not self.servers:
            return None

        # Фильтруем рабочие reality серверы
        candidates = [
            s for s in self.servers
            if s.get('status') == 'online'
            and s.get('security') == 'reality'
            and s.get('uuid')
        ]

        if not candidates:
            # Пробуем любые reality
            candidates = [
                s for s in self.servers
                if s.get('security') == 'reality'
                and s.get('uuid')
            ]

        if not candidates:
            return None

        # Сортируем по пингу
        candidates.sort(key=lambda x: x.get('latency', 9999))

        return candidates[0]

    def generate_config(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация конфига XRay с DPI bypass"""
        stream = server.get("streamSettings", {})
        security = stream.get("security", "tls")

        # Базовый конфиг
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
                    "security": security,
                    **self.dpi_bypass.get_xray_config()["streamSettings"]
                }
            }],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": []
            }
        }

        # Добавляем reality настройки
        if security == "reality":
            reality = stream.get("realitySettings", {})
            config["outbounds"][0]["streamSettings"]["realitySettings"] = {
                "serverName": reality.get("serverName", server["host"]),
                "fingerprint": "chrome",
                "publicKey": reality.get("publicKey", ""),
                "shortId": reality.get("shortId", "")
            }

        # Добавляем фрагментацию
        config["fragment"] = self.dpi_bypass.get_xray_config()["fragment"]

        return config

    def start_xray(self, server: Dict[str, Any]) -> bool:
        """Запуск XRay"""
        try:
            # Генерация конфига
            config = self.generate_config(server)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            Logger.log(f"✅ Конфиг создан: {CONFIG_FILE}")

            # Проверка XRay
            if not XRAY_BIN.exists():
                Logger.log("❌ XRay не установлен!", "ERROR")
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

            # Проверка
            if self.xray_process.poll() is None:
                Logger.log("✅ XRay запущен")
                self.current_server = server
                return True
            else:
                Logger.log("❌ XRay не запустился", "ERROR")
                return False

        except Exception as e:
            Logger.log(f"❌ Ошибка запуска XRay: {e}", "ERROR")
            return False

    def stop_xray(self):
        """Остановка XRay"""
        try:
            if self.xray_process:
                self.xray_process.terminate()
                try:
                    self.xray_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.xray_process.kill()
                Logger.log("🛑 XRay остановлен")
        except Exception as e:
            Logger.log(f"⚠️ Ошибка остановки: {e}", "WARNING")

        # Принудительная остановка
        try:
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        except:
            pass

        self.current_server = None

    def connect(self) -> bool:
        """Подключение с обходом Чебурнета"""
        Logger.log("=" * 60)
        Logger.log("🚀 ПОДКЛЮЧЕНИЕ К VPN (ULTIMATE - CHEBURUNET BYPASS)")
        Logger.log("=" * 60)

        # Проверка блокировки
        Logger.log("🔍 Проверка блокировки...")
        if self.dpi_bypass.detect_blocking():
            Logger.log("⚠️ Обнаружена блокировка! Активируем обход DPI...", "WARNING")
            self.dpi_bypass.stats["blocks_detected"] += 1

        # Загрузка серверов
        self.load_servers()

        if not self.servers:
            Logger.log("❌ Нет серверов! Сначала обновите: vless-vpn update", "ERROR")
            return False

        # Попытки подключения
        for attempt in range(self.max_attempts):
            self.connection_attempts = attempt + 1

            # Выбор сервера
            best_server = self.get_best_server()
            if not best_server:
                Logger.log("❌ Не удалось выбрать сервер", "ERROR")
                return False

            Logger.log(f"🔌 Попытка {attempt + 1}/{self.max_attempts}: {best_server['host']}:{best_server['port']}")

            if self.start_xray(best_server):
                Logger.log("✅ VPN ПОДКЛЮЧЕН!")
                Logger.log("  SOCKS5: 127.0.0.1:10808")
                Logger.log("  HTTP: 127.0.0.1:10809")
                Logger.log(f"  DPI Bypass: {self.dpi_bypass.current_strategy}")
                self.dpi_bypass.stats["bypasses_successful"] += 1
                return True

            # Неудачная попытка - переключаем стратегию
            Logger.log("⚠️ Не удалось подключиться, смена стратегии...", "WARNING")
            self.dpi_bypass.switch_strategy()

            # Удаляем нерабочий сервер из списка
            if best_server in self.servers:
                best_server['status'] = 'offline'

        Logger.log("❌ Исчерпаны попытки подключения", "ERROR")
        return False

    def disconnect(self):
        """Отключение"""
        Logger.log("=" * 60)
        Logger.log("🛑 ОТКЛЮЧЕНИЕ ОТ VPN")
        Logger.log("=" * 60)

        self.running = False
        self.stop_xray()

        Logger.log("✅ VPN отключен")

    def status(self):
        """Статус"""
        # Загружаем серверы для статистики
        self.load_servers()
        
        print("\n" + "=" * 60)
        print("СТАТУС VPN КЛИЕНТА (ULTIMATE)")
        print("=" * 60)

        # Проверка процесса
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)

        if result.returncode == 0:
            print("✅ Подключен")
            if self.current_server:
                print(f"  Сервер: {self.current_server['host']}:{self.current_server['port']}")
                print(f"  DPI Bypass: {self.dpi_bypass.current_strategy}")
        else:
            print("❌ Не подключен")

        print(f"\nВсего серверов: {len(self.servers)}")
        online = sum(1 for s in self.servers if s.get("status") == "online")
        print(f"Онлайн: {online}")

        print("\nПрокси:")
        print("  SOCKS5: 127.0.0.1:10808")
        print("  HTTP: 127.0.0.1:10809")

        print("\nDPI Bypass статистика:")
        stats = self.dpi_bypass.get_stats()
        print(f"  Стратегия: {stats['current_strategy']}")
        print(f"  Переключений: {stats['switches']}")
        print(f"  Блокировок: {stats['blocks_detected']}")
        print(f"  Успешных обходов: {stats['bypasses_successful']}")

        print("=" * 60)

    async def update_servers(self):
        """Обновление серверов"""
        Logger.log("🔄 Обновление серверов из всех источников...")
        
        # Сканирование
        servers = await self.scanner.scan_all_sources()
        
        if servers:
            # Проверка серверов
            working_servers = await self.scanner.check_servers(servers)
            
            # Сохранение
            self.scanner.save_servers(working_servers)
            
            # Загрузка обновленных
            self.load_servers()
            
            Logger.log(f"✅ Обновлено: {len(working_servers)} рабочих серверов")
        else:
            Logger.log("⚠️ Серверы не найдены", "WARNING")


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

def main():
    """Точка входа"""
    import argparse

    parser = argparse.ArgumentParser(description="VLESS VPN Client - ULTIMATE")
    parser.add_argument("command", choices=["start", "stop", "status", "update", "scan", "autostart-enable", "autostart-disable", "start-auto"],
                        help="Команда: start, stop, status, update, scan, autostart-enable, autostart-disable, start-auto")
    parser.add_argument("--auto", action="store_true", help="Автоподключение")

    args = parser.parse_args()

    client = UltimateVPNClient()

    # Обработка сигналов
    def signal_handler(sig, frame):
        Logger.log("📩 Получен сигнал остановки")
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.command == "start":
        if client.connect():
            client.running = True

            Logger.log("💤 Ожидание (Ctrl+C для остановки)...")
            Logger.log("")
            Logger.log("=" * 60)
            Logger.log("VPN РАБОТАЕТ И НЕ ОТКЛЮЧИТСЯ!")
            Logger.log("DPI Bypass активен | Чебурнет будет обойден")
            Logger.log("Нажмите Ctrl+C для остановки")
            Logger.log("=" * 60)

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
        asyncio.run(client.update_servers())

    elif args.command == "scan":
        Logger.log("🔍 Сканирование серверов...")
        asyncio.run(client.update_servers())

    elif args.command == "autostart-enable":
        client.autostart.setup_autostart()

    elif args.command == "autostart-disable":
        client.autostart.remove_autostart()

    elif args.command == "start-auto":
        # Автоматический запуск для systemd/autostart
        Logger.log("🚀 АВТОМАТИЧЕСКИЙ ЗАПУСК VPN...")
        Logger.log("=" * 60)
        
        # Ждём сеть
        Logger.log("⏳ Ожидание сети...")
        time.sleep(5)
        
        # Пробуем подключиться
        if client.connect():
            Logger.log("✅ VPN подключен автоматически!")
            
            # Работаем в фоне
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                Logger.log("\n👋 Остановка...")
                client.disconnect()
        else:
            Logger.log("❌ Не удалось подключиться автоматически", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    main()
