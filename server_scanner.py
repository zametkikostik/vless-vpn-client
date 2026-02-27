#!/usr/bin/env python3
"""
VPN Server Scanner v2.0
- Парсинг из GitHub (авто-сбор серверов)
- Проверка пинга (реальный замер задержки)
- Интеграция с GUI
"""

import asyncio
import aiohttp
import json
import re
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ServerData:
    """Данные сервера"""
    host: str
    port: int
    uuid: str
    protocol: str = "vless"
    security: str = "reality"
    sni: str = ""
    pbk: str = ""
    sid: str = ""
    fp: str = "chrome"
    alpn: List[str] = None
    country: str = "🌍"
    name: str = ""
    latency: int = 9999
    is_working: bool = False
    source: str = "unknown"
    checked_at: str = ""
    
    def __post_init__(self):
        if self.alpn is None:
            self.alpn = ["h2", "http/1.1"]


class ServerScanner:
    """Сканер серверов с парсингом и пингом"""
    
    def __init__(self, progress_callback=None):
        self.data_dir = Path.home() / "vpn-client-aggregator" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.servers_file = self.data_dir / "servers.json"
        self.working_file = self.data_dir / "working_servers.json"
        self.servers: List[ServerData] = []
        self.working_servers: List[ServerData] = []
        self.progress_callback = progress_callback  # Для GUI
        self.new_servers_count = 0
    
    def log(self, message: str):
        """Логирование"""
        print(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    # ==========================================================================
    # ПАРСИНГ ИЗ GITHUB
    # ==========================================================================
    
    async def parse_all_sources(self):
        """Парсинг всех источников"""
        self.log("📂 Парсинг источников...")
        
        await asyncio.gather(
            self.parse_github_repos(),
            self.parse_vless_lists(),
            self.parse_subscription_urls(),
        )
        
        self.log(f"📊 Найдено серверов: {len(self.servers)}")
    
    async def parse_github_repos(self):
        """Парсинг GitHub репозиториев"""
        self.log("  🔍 GitHub репозитории...")
        
        # Репозитории с конфигами
        github_urls = [
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in github_urls:
                try:
                    async with session.get(url, timeout=15) as response:
                        if response.status == 200:
                            content = await response.text()
                            servers = self.parse_config_content(content, "github")
                            self.servers.extend(servers)
                            self.log(f"    ✅ {url.split('/')[-1]}: {len(servers)} серверов")
                except Exception as e:
                    self.log(f"    ❌ {url.split('/')[-1]}: {e}")
    
    async def parse_vless_lists(self):
        """Парсинг списков VLESS"""
        self.log("  🔍 Списки VLESS...")
        
        vless_urls = [
            "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/etc/list/list.txt",
            "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
            "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all",
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in vless_urls:
                try:
                    async with session.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as response:
                        if response.status == 200:
                            content = await response.text()
                            servers = self.parse_vless_links(content, "vless-list")
                            self.servers.extend(servers)
                            self.log(f"    ✅ {url.split('/')[-1]}: {len(servers)} серверов")
                except Exception as e:
                    self.log(f"    ❌ {url}: {e}")
    
    async def parse_subscription_urls(self):
        """Парсинг subscription URL"""
        self.log("  🔍 Subscription URLs...")
        
        # Добавьте свои subscription URL
        sub_urls = [
            # Пример: "https://example.com/sub"
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in sub_urls:
                try:
                    async with session.get(url, timeout=15) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Пробуем декодировать base64
                            try:
                                decoded = base64.b64decode(content).decode('utf-8')
                                servers = self.parse_vless_links(decoded, "subscription")
                                self.servers.extend(servers)
                                self.log(f"    ✅ {url}: {len(servers)} серверов")
                            except:
                                pass
                except Exception as e:
                    self.log(f"    ❌ {url}: {e}")
    
    def parse_config_content(self, content: str, source: str) -> List[ServerData]:
        """Парсинг содержимого конфига"""
        servers = []
        
        # Паттерн для Reality серверов
        pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)[^@]*@[^?]*\?[^s]*sni=([^&\s]+)[^p]*pbk=([^&\s]+)(?:[^s]*sid=([^&\s]+))?|(\d+\.\d+\.\d+\.\d+):(\d+)[^@]*@[^?]*\?[^s]*sni=([^&\s]+)[^p]*pbk=([^&\s]+)'
        
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            try:
                if match.group(1):  # С sid
                    server = ServerData(
                        host=match.group(1),
                        port=int(match.group(2)),
                        uuid="",  # Нужно извлечь отдельно
                        sni=match.group(3),
                        pbk=match.group(4),
                        sid=match.group(5) or "",
                        source=source
                    )
                else:  # Без sid
                    server = ServerData(
                        host=match.group(6),
                        port=int(match.group(7)),
                        uuid="",
                        sni=match.group(8),
                        pbk=match.group(9),
                        sid="",
                        source=source
                    )
                servers.append(server)
            except:
                continue
        
        return servers
    
    def parse_vless_links(self, content: str, source: str) -> List[ServerData]:
        """Парсинг VLESS ссылок"""
        servers = []
        
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('vless://'):
                try:
                    server = self.parse_vless_url(line, source)
                    if server:
                        servers.append(server)
                except:
                    continue
        
        return servers
    
    def parse_vless_url(self, url: str, source: str) -> Optional[ServerData]:
        """Парсинг VLESS URL"""
        try:
            # Удаляем vless://
            url = url.replace('vless://', '')
            
            # Разбираем название
            if '#' in url:
                url, name = url.split('#', 1)
                name = name.replace('%20', ' ')
            else:
                name = ""
            
            # Разбираем основную часть
            parts = url.split('@')
            if len(parts) != 2:
                return None
            
            uuid = parts[0]
            host_port = parts[1]
            
            # Разбираем хост:порт
            if ':' not in host_port:
                return None
            
            host, rest = host_port.split(':', 1)
            port_str = rest.split('?')[0]
            
            if not port_str.isdigit():
                return None
            
            port = int(port_str)
            
            # Разбираем параметры
            if '?' not in rest:
                return None
            
            params = rest.split('?', 1)[1]
            params_dict = {}
            for param in params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params_dict[key] = value
            
            security = params_dict.get('security', 'none')
            sni = params_dict.get('sni', params_dict.get('host', ''))
            pbk = params_dict.get('pbk', '')
            sid = params_dict.get('sid', '')
            fp = params_dict.get('fp', 'chrome')
            
            # Определяем страну по названию
            country = self.detect_country(name)
            
            server = ServerData(
                host=host,
                port=port,
                uuid=uuid,
                security=security,
                sni=sni,
                pbk=pbk,
                sid=sid,
                fp=fp,
                country=country,
                name=name,
                source=source
            )
            
            return server
        except:
            pass
        
        return None
    
    def detect_country(self, name: str) -> str:
        """Определение страны по названию"""
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
            'belarus': '🇧🇾', 'by ': '🇧🇾',
            'kazakhstan': '🇰🇿', 'kz ': '🇰🇿',
        }
        
        for key, flag in flags.items():
            if key in name_lower:
                return flag
        
        return '🌍'
    
    # ==========================================================================
    # ПРОВЕРКА СЕРВЕРОВ
    # ==========================================================================
    
    async def check_servers(self, max_concurrent: int = 50):
        """Проверка всех серверов"""
        self.log("🔍 Проверка серверов...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Проверяем уникальные серверы
        unique_servers = {}
        for server in self.servers:
            key = f"{server.host}:{server.port}"
            if key not in unique_servers:
                unique_servers[key] = server
        
        self.log(f"📊 Уникальных серверов: {len(unique_servers)}")
        
        # Создаём задачи
        tasks = [self.check_server(server, semaphore) for server in unique_servers.values()]
        
        # Выполняем
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем рабочие
        for result in results:
            if result and isinstance(result, ServerData) and result.is_working:
                self.working_servers.append(result)
        
        self.log(f"✅ Рабочих серверов: {len(self.working_servers)}")
    
    async def check_server(self, server: ServerData, semaphore: asyncio.Semaphore) -> Optional[ServerData]:
        """Проверка одного сервера"""
        async with semaphore:
            try:
                # Замер пинга
                start_time = asyncio.get_event_loop().time()
                
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(server.host, server.port),
                    timeout=5
                )
                
                end_time = asyncio.get_event_loop().time()
                latency = int((end_time - start_time) * 1000)  # мс
                
                writer.close()
                await writer.wait_closed()
                
                server.is_working = True
                server.latency = latency
                server.checked_at = datetime.now().isoformat()
                
                self.log(f"  ✅ {server.country} {server.host}:{server.port} ({latency}ms)")
                return server
                
            except Exception as e:
                self.log(f"  ❌ {server.country} {server.host}:{server.port}")
                return None
    
    # ==========================================================================
    # СОХРАНЕНИЕ
    # ==========================================================================
    
    def save_results(self):
        """Сохранение результатов"""
        # Сортируем по пингу
        self.working_servers.sort(key=lambda s: s.latency)
        
        # Сохраняем рабочие
        working_data = {
            "scanned_at": datetime.now().isoformat(),
            "total": len(self.servers),
            "working": len(self.working_servers),
            "servers": [asdict(s) for s in self.working_servers]
        }
        
        with open(self.working_file, 'w', encoding='utf-8') as f:
            json.dump(working_data, f, indent=2, ensure_ascii=False)
        
        self.log(f"💾 Рабочие: {self.working_file}")
        
        # Объединяем с существующими
        self.merge_with_existing()
    
    def merge_with_existing(self):
        """Объединение с существующим списком"""
        existing_servers = []
        
        if self.servers_file.exists():
            try:
                with open(self.servers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing_servers = data
                    else:
                        existing_servers = data.get('servers', [])
            except:
                pass
        
        # Добавляем новые рабочие
        new_count = 0
        for server in self.working_servers:
            # Проверяем дубликаты
            exists = False
            for existing in existing_servers:
                e_host = existing.get('host', existing.get('address', ''))
                e_port = existing.get('port', 443)
                if e_host == server.host and e_port == server.port:
                    exists = True
                    # Обновляем данные
                    existing['latency'] = server.latency
                    existing['is_working'] = True
                    existing['last_checked'] = server.checked_at
                    break
            
            if not exists:
                # Добавляем новый сервер
                new_server = {
                    'host': server.host,
                    'port': server.port,
                    'uuid': server.uuid,
                    'protocol': 'vless',
                    'country': server.country,
                    'name': server.name,
                    'is_working': True,
                    'latency': server.latency,
                    'last_checked': server.checked_at,
                    'stream_settings': {
                        'reality_settings': {
                            'serverName': server.sni,
                            'publicKey': server.pbk,
                            'shortId': server.sid,
                            'fingerprint': server.fp
                        }
                    }
                }
                existing_servers.append(new_server)
                new_count += 1
        
        # Сохраняем
        with open(self.servers_file, 'w', encoding='utf-8') as f:
            json.dump(existing_servers, f, indent=2, ensure_ascii=False)
        
        self.new_servers_count = new_count
        self.log(f"💾 Добавлено {new_count} новых серверов")
    
    def show_top(self, count: int = 10):
        """Показать топ рабочих"""
        if not self.working_servers:
            self.log("❌ Нет рабочих серверов")
            return
        
        self.log(f"\n🏆 Топ-{count} рабочих серверов:")
        for i, server in enumerate(self.working_servers[:count], 1):
            self.log(f"  {i}. {server.country} {server.name or server.host}:{server.port} ({server.latency}ms)")


async def main():
    """Основная функция"""
    print("🛡️  VPN Server Scanner v2.0")
    print("=" * 60)
    
    scanner = ServerScanner()
    
    # Парсим источники
    await scanner.parse_all_sources()
    
    if not scanner.servers:
        print("❌ Серверы не найдены!")
        return
    
    # Проверяем серверы
    await scanner.check_servers()
    
    # Сохраняем
    scanner.save_results()
    
    # Показываем топ
    scanner.show_top(10)
    
    print("=" * 60)
    print("✅ Сканирование завершено!")
    print(f"📊 Найдено: {len(scanner.servers)}")
    print(f"✅ Рабочих: {len(scanner.working_servers)}")
    print(f"🆕 Новых: {scanner.new_servers_count}")


if __name__ == '__main__':
    asyncio.run(main())
