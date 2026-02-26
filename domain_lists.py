#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Загрузчик списков доменов из GitHub и доверенных источников

© 2026 VPN Client Aggregator
"""

import asyncio
import aiohttp
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """Конфигурация источника списков"""
    name: str
    url: str
    file_type: str  # 'txt', 'dat', 'json'
    category: Optional[str] = None
    trusted: bool = True


@dataclass
class DownloadResult:
    """Результат загрузки"""
    source: str
    success: bool
    domains_count: int = 0
    error: Optional[str] = None
    download_time: float = 0.0


class DomainListsLoader:
    """
    Загрузчик списков доменов из GitHub и доверенных источников.
    
    Источники:
    1. GitHub (igareck/vpn-configs-for-russia)
    2. v2fly/domain-list-community
    3. v2fly/geoip
    4. Loyalsoldier/v2ray-rules-dat
    """
    
    # GitHub источники
    GITHUB_SOURCES: Dict[str, SourceConfig] = {
        "white_list": SourceConfig(
            name="White List (Rus Mobile)",
            url="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
            file_type="txt",
            category="russian_direct",
            trusted=True
        ),
        "black_list_social": SourceConfig(
            name="Black List - Social",
            url="https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/facebook",
            file_type="txt",
            category="social",
            trusted=True
        ),
        "geosite": SourceConfig(
            name="GeoSite Database",
            url="https://github.com/v2fly/domain-list-community/releases/latest/download/geosite.dat",
            file_type="dat",
            trusted=True
        ),
        "geoip": SourceConfig(
            name="GeoIP Database",
            url="https://github.com/v2fly/geoip/releases/latest/download/geoip.dat",
            file_type="dat",
            trusted=True
        ),
        "loyalsoldier_direct": SourceConfig(
            name="LoyalSoldier - Direct",
            url="https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/direct-list.txt",
            file_type="txt",
            category="russian_direct",
            trusted=True
        ),
        "loyalsoldier_proxy": SourceConfig(
            name="LoyalSoldier - Proxy",
            url="https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/proxy-list.txt",
            file_type="txt",
            category="blocked",
            trusted=True
        )
    }
    
    # Категории доменов по умолчанию
    DEFAULT_CATEGORIES: Dict[str, List[str]] = {
        "social": [
            "facebook.com", "fbcdn.net", "facebook.net",
            "instagram.com", "cdninstagram.com",
            "twitter.com", "twimg.com", "x.com",
            "tiktok.com", "tiktokcdn.com", "tiktokv.com",
            "linkedin.com", "licdn.com",
            "pinterest.com", "pinimg.com",
            "reddit.com", "redd.it", "redditmedia.com",
            "telegram.org", "telegram.me", "t.me",
            "whatsapp.com", "whatsapp.net",
            "discord.com", "discordapp.com", "discordapp.net",
            "snapchat.com", "sc-cdn.net"
        ],
        "video": [
            "youtube.com", "ytimg.com", "googlevideo.com", "youtube-nocookie.com", "youtu.be",
            "vimeo.com", "vimeocdn.com", "vimeoplayer.com",
            "twitch.tv", "ttvnw.net", "jtvnw.net", "twitchcdn.net",
            "dailymotion.com", "dmcdn.net", "dai.ly",
            "netflix.com", "nflxvideo.net", "nflximg.net",
            "hulu.com", "huluim.com"
        ],
        "ai": [
            "openai.com", "chatgpt.com", "oaiusercontent.com", "api.openai.com",
            "claude.ai", "anthropic.com",
            "gemini.google.com", "bard.google.com", "ai.google.dev",
            "midjourney.com",
            "lovable.dev",  # ✅ Lovable.dev
            "huggingface.co", "huggingface.co.uk",
            "stability.ai",
            "deepmind.com",
            "replicate.com",
            "cohere.com",
            "ai21.com",
            "character.ai",
            "poe.com",
            "perplexity.ai",
            "you.com",
            "runwayml.com",
            "synthesia.io",
            "elevenlabs.io",
            "midjourney.com", "discord.gg"
        ],
        "blocked_media": [
            "meduza.io",
            "novayagazeta.ru",
            "dojd.ru",
            "holod.media",
            "importantstories.org",
            "bellingcat.com",
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "nytimes.com",
            "theguardian.com",
            "bbc.com", "bbc.co.uk",
            "dw.com",
            "radiofrance.fr",
            "rferl.org",
            "currenttime.tv",
            "mtvusa.com"
        ],
        "russian_services": [
            "vk.com", "vkuseraudio.net", "vkuservideo.net", "vkuser.net", "vk.ru", "m.vk.ru",
            "ok.ru", "odnoklassniki.ru", "okcdn.com",
            "yandex.ru", "yandex.net", "yandex.com", "yandex.ua", "yandex.by", "yandex.kz", "ya.ru",
            "mail.ru", "bk.ru", "inbox.ru", "list.ru",
            "rambler.ru",
            "sberbank.ru", "sberbank.com",
            "tinkoff.ru", "t-bank.ru",
            "alfabank.ru",
            "vtb.ru",
            "gazprombank.ru",
            "rosbank.ru",
            "gosuslugi.ru",
            "nalog.ru",
            "pfr.gov.ru",
            "rosreestr.ru",
            "mvd.ru",
            "minzdrav.gov.ru",
            "government.ru",
            "kremlin.ru",
            "duma.gov.ru",
            "rutube.ru",
            "kion.ru",
            "more.tv",
            "start.ru",
            "ivi.ru", "ivi.com",
            "okko.tv", "okko.ru",
            "tvzavr.ru",
            "smotrim.ru",
            "1tv.ru",
            "ntv.ru",
            "match.tv"
        ],
        "local_network": [
            "localhost",
            "127.0.0.1",
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12",
            ".local",
            ".lan"
        ]
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Инициализация загрузчика списков.
        
        Args:
            data_dir: Директория для хранения данных.
                     По умолчанию: ~/vpn-client-aggregator/data
        """
        if data_dir is None:
            self.data_dir = Path.home() / "vpn-client-aggregator" / "data"
        else:
            self.data_dir = data_dir
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Кэш загруженных данных
        self._cache: Dict[str, List[str]] = {}
        self._last_update: Dict[str, datetime] = {}
        
        # Статистика
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_domains': 0,
            'last_update': None
        }
    
    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ==========================================================================
    
    async def download_list(self, source: SourceConfig) -> DownloadResult:
        """
        Загрузка списка из источника.
        
        Args:
            source: Конфигурация источника
        
        Returns:
            Результат загрузки
        """
        start_time = datetime.now()
        dest_file = self.data_dir / f"{source.name.replace(' ', '_').lower()}.{source.file_type}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url, timeout=30, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Проверка безопасности
                        if self._validate_content(content, source.file_type):
                            # Сохранение файла
                            with open(dest_file, 'wb') as f:
                                f.write(content)
                            
                            # Парсинг доменов (для txt)
                            domains_count = 0
                            if source.file_type == 'txt':
                                domains = self._parse_txt_content(content)
                                domains_count = len(domains)
                                
                                # Сохранение в кэш
                                if source.category:
                                    self._cache[source.category] = domains
                            
                            download_time = (datetime.now() - start_time).total_seconds()
                            
                            # Обновление статистики
                            self.stats['total_downloads'] += 1
                            self.stats['successful_downloads'] += 1
                            self.stats['total_domains'] += domains_count
                            self.stats['last_update'] = datetime.now().isoformat()
                            self._last_update[source.name] = datetime.now()
                            
                            return DownloadResult(
                                source=source.name,
                                success=True,
                                domains_count=domains_count,
                                download_time=download_time
                            )
                        else:
                            error = "Небезопасный контент"
                            self.stats['failed_downloads'] += 1
                            return DownloadResult(
                                source=source.name,
                                success=False,
                                error=error
                            )
                    else:
                        error = f"HTTP {response.status}"
                        self.stats['failed_downloads'] += 1
                        return DownloadResult(
                            source=source.name,
                            success=False,
                            error=error
                        )
        except asyncio.TimeoutError:
            error = "Timeout"
            self.stats['failed_downloads'] += 1
            return DownloadResult(source=source.name, success=False, error=error)
        except Exception as e:
            error = str(e)
            self.stats['failed_downloads'] += 1
            return DownloadResult(source=source.name, success=False, error=error)
    
    async def update_all_lists(self) -> List[DownloadResult]:
        """
        Обновление всех списков.
        
        Returns:
            Список результатов загрузки
        """
        tasks = []
        for source in self.GITHUB_SOURCES.values():
            tasks.append(self.download_list(source))
        
        results = await asyncio.gather(*tasks)
        return list(results)
    
    def load_domain_lists(self) -> Dict[str, List[str]]:
        """
        Загрузка списков доменов из локальных файлов.
        
        Returns:
            Словарь категорий со списками доменов
        """
        lists = {}
        
        # Загрузка категорий по умолчанию
        lists_file = self.data_dir / "domain-lists.json"
        if lists_file.exists():
            try:
                with open(lists_file, 'r', encoding='utf-8') as f:
                    lists = json.load(f)
            except (json.JSONDecodeError, IOError):
                lists = self.DEFAULT_CATEGORIES.copy()
        else:
            lists = self.DEFAULT_CATEGORIES.copy()
            # Сохранение по умолчанию
            self.save_domain_lists(lists)
        
        # Загрузка белого списка
        white_list_file = self.data_dir / "white_list.txt"
        if white_list_file.exists():
            white_domains = self._parse_txt_file(white_list_file)
            if white_domains:
                lists['russian_direct'] = list(set(
                    lists.get('russian_direct', []) + white_domains
                ))
        
        return lists
    
    def save_domain_lists(self, lists: Dict[str, List[str]]):
        """
        Сохранение списков доменов.
        
        Args:
            lists: Словарь категорий со списками
        """
        lists_file = self.data_dir / "domain-lists.json"
        
        # Удаление дубликатов и сортировка
        cleaned_lists = {}
        for category, domains in lists.items():
            unique_domains = list(set(domains))
            cleaned_lists[category] = sorted(unique_domains)
        
        with open(lists_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_lists, f, indent=2, ensure_ascii=False)
    
    def get_domains_for_category(self, category: str) -> List[str]:
        """
        Получение доменов для категории.
        
        Args:
            category: Название категории
        
        Returns:
            Список доменов
        """
        # Проверка кэша
        if category in self._cache:
            return self._cache[category]
        
        # Загрузка из файлов
        lists = self.load_domain_lists()
        return lists.get(category, [])
    
    def get_all_vpn_domains(self) -> List[str]:
        """
        Получение всех доменов для VPN (чёрный список).
        
        Returns:
            Объединённый список доменов для VPN
        """
        lists = self.load_domain_lists()
        vpn_categories = ['social', 'video', 'ai', 'blocked_media']
        
        all_domains = []
        for category in vpn_categories:
            all_domains.extend(lists.get(category, []))
        
        return list(set(all_domains))
    
    def get_all_direct_domains(self) -> List[str]:
        """
        Получение всех доменов для прямого подключения.
        
        Returns:
            Объединённый список доменов напрямую
        """
        lists = self.load_domain_lists()
        direct_categories = ['russian_services', 'local_network']
        
        all_domains = []
        for category in direct_categories:
            all_domains.extend(lists.get(category, []))
        
        return list(set(all_domains))
    
    def should_update(self, max_age_hours: int = 24) -> bool:
        """
        Проверка необходимости обновления списков.
        
        Args:
            max_age_hours: Максимальный возраст кэша в часах
        
        Returns:
            True если нужно обновить
        """
        if not self.stats['last_update']:
            return True
        
        last_update = datetime.fromisoformat(self.stats['last_update'])
        age = datetime.now() - last_update
        
        return age > timedelta(hours=max_age_hours)
    
    # ==========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _validate_content(self, content: bytes, file_type: str) -> bool:
        """
        Проверка безопасности контента.
        
        Args:
            content: Содержимое файла
            file_type: Тип файла
        
        Returns:
            True если контент безопасен
        """
        # Проверка на executable код (для txt)
        if file_type == 'txt':
            try:
                text_content = content.decode('utf-8')[:1000]
                
                # Проверка на скрипты
                if '#!/' in text_content[:100]:
                    return False
                if '<script>' in text_content.lower():
                    return False
                if '<?php' in text_content:
                    return False
                
                # Проверка на домены (должны быть валидные строки)
                lines = text_content.split('\n')
                valid_lines = 0
                for line in lines[:20]:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Проверка на домен или IP
                        if self._is_valid_domain_or_ip(line):
                            valid_lines += 1
                
                # Если хотя бы половина строк валидны - файл ок
                return valid_lines >= len([l for l in lines[:20] if l.strip()]) * 0.5
                
            except UnicodeDecodeError:
                return False
        
        # Для dat файлов проверяем размер
        elif file_type == 'dat':
            return 1024 <= len(content) <= 100 * 1024 * 1024  # 1KB - 100MB
        
        return True
    
    def _parse_txt_content(self, content: bytes) -> List[str]:
        """
        Парсинг TXT контента для извлечения доменов.
        
        Args:
            content: Байты контента
        
        Returns:
            Список доменов
        """
        try:
            text = content.decode('utf-8')
            domains = []
            
            for line in text.split('\n'):
                line = line.strip()
                
                # Пропуск комментариев и пустых строк
                if not line or line.startswith('#'):
                    continue
                
                # Проверка на домен
                if self._is_valid_domain(line):
                    domains.append(line)
            
            return domains
        except:
            return []
    
    def _parse_txt_file(self, file_path: Path) -> List[str]:
        """
        Парсинг TXT файла.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Список доменов
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_txt_content(content.encode('utf-8'))
        except:
            return []
    
    def _is_valid_domain(self, domain: str) -> bool:
        """
        Проверка валидности домена.
        
        Args:
            domain: Домен для проверки
        
        Returns:
            True если домен валиден
        """
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    def _is_valid_domain_or_ip(self, line: str) -> bool:
        """
        Проверка на домен или IP адрес.
        
        Args:
            line: Строка для проверки
        
        Returns:
            True если это домен или IP
        """
        # Проверка на IP
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d+)?$'
        if re.match(ip_pattern, line):
            return True
        
        # Проверка на домен
        return self._is_valid_domain(line)
    
    def get_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Получение хеша файла (SHA-256).
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            SHA-256 хеш или None
        """
        if not file_path.exists():
            return None
        
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики загрузчика.
        
        Returns:
            Статистика
        """
        return {
            **self.stats,
            'data_dir': str(self.data_dir),
            'cache_entries': len(self._cache),
            'last_update': self.stats['last_update']
        }


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование DomainListsLoader...")
    
    loader = DomainListsLoader()
    
    # Загрузка локальных списков
    print("\n📋 Загрузка списков доменов...")
    lists = loader.load_domain_lists()
    
    for category, domains in lists.items():
        print(f"   {category}: {len(domains)} доменов")
    
    # Получение VPN доменов
    print("\n🌐 Домены для VPN:")
    vpn_domains = loader.get_all_vpn_domains()
    print(f"   Всего: {len(vpn_domains)} доменов")
    
    # Получение прямых доменов
    print("\n🏠 Домены для прямого подключения:")
    direct_domains = loader.get_all_direct_domains()
    print(f"   Всего: {len(direct_domains)} доменов")
    
    # Статистика
    stats = loader.get_stats()
    print(f"\n📊 Статистика:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ DomainListsLoader готов к работе!")
