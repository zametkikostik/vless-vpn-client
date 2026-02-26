#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Split-tunneling менеджер - раздельное туннелирование трафика

© 2026 VPN Client Aggregator
"""

import json
import ipaddress
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class RouteAction(Enum):
    """Действия маршрутизации"""
    PROXY = "proxy"      # Через VPN
    DIRECT = "direct"    # Напрямую
    BLOCK = "block"      # Блокировать


@dataclass
class RouteRule:
    """Правило маршрутизации"""
    type: str  # 'domain', 'ip', 'geoip', 'geosite'
    value: str
    action: RouteAction
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для Xray"""
        return {
            "type": "field",
            "outboundTag": self.action.value,
            self.type: [self.value] if not self.value.startswith('geosite:') and not self.value.startswith('geoip:') else [self.value]
        }


@dataclass
class SplitTunnelConfig:
    """Конфигурация split-tunneling"""
    enabled: bool = True
    blacklist_categories: List[str] = field(default_factory=list)
    whitelist_categories: List[str] = field(default_factory=list)
    custom_proxy_domains: List[str] = field(default_factory=list)
    custom_direct_domains: List[str] = field(default_factory=list)
    custom_proxy_ips: List[str] = field(default_factory=list)
    custom_direct_ips: List[str] = field(default_factory=list)
    block_bittorrent: bool = True
    block_private_ips: bool = False


class SplitTunnelManager:
    """
    Менеджер раздельного туннелирования (Split-tunneling).
    
    Управление маршрутизацией трафика:
    - Через VPN (прокси)
    - Напрямую (direct)
    - Блокировка (block)
    """
    
    # Категории по умолчанию
    DEFAULT_CATEGORIES = {
        'social': [
            "facebook.com", "fbcdn.net", "facebook.net",
            "instagram.com", "cdninstagram.com",
            "twitter.com", "twimg.com", "x.com",
            "tiktok.com", "tiktokcdn.com", "tiktokv.com",
            "telegram.org", "telegram.me", "t.me",
            "whatsapp.com", "whatsapp.net",
            "discord.com", "discordapp.com"
        ],
        'video': [
            "youtube.com", "ytimg.com", "googlevideo.com", "youtu.be",
            "vimeo.com", "vimeocdn.com",
            "twitch.tv", "ttvnw.net", "jtvnw.net",
            "netflix.com", "nflxvideo.net"
        ],
        'ai': [
            "openai.com", "chatgpt.com", "oaiusercontent.com",
            "claude.ai", "anthropic.com",
            "gemini.google.com", "bard.google.com",
            "midjourney.com",
            "lovable.dev",  # ✅ Lovable.dev
            "huggingface.co",
            "stability.ai",
            "deepmind.com",
            "perplexity.ai",
            "character.ai"
        ],
        'blocked_media': [
            "meduza.io",
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "nytimes.com",
            "theguardian.com",
            "bbc.com", "bbc.co.uk",
            "dw.com"
        ],
        'russian_services': [
            "vk.com", "vkuseraudio.net", "vkuservideo.net",
            "ok.ru", "odnoklassniki.ru",
            "yandex.ru", "yandex.net", "yandex.com",
            "mail.ru", "bk.ru", "inbox.ru",
            "sberbank.ru", "tinkoff.ru",
            "gosuslugi.ru", "nalog.ru",
            "rutube.ru", "kion.ru", "ivi.ru"
        ]
    }
    
    def __init__(self, config: Optional[SplitTunnelConfig] = None):
        """
        Инициализация менеджера split-tunneling.
        
        Args:
            config: Конфигурация split-tunneling
        """
        self.config = config or SplitTunnelConfig(
            enabled=True,
            blacklist_categories=['social', 'video', 'ai', 'blocked_media'],
            whitelist_categories=['russian_services'],
            block_bittorrent=True,
            block_private_ips=False
        )
        
        # Кэш доменов
        self._proxy_domains: Set[str] = set()
        self._direct_domains: Set[str] = set()
        self._proxy_ips: Set[str] = set()
        self._direct_ips: Set[str] = set()
        
        # Загрузка списков
        self._load_domain_lists()
    
    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def generate_routing_rules(self) -> List[Dict[str, Any]]:
        """
        Генерация правил маршрутизации для Xray.
        
        Returns:
            Список правил в формате Xray
        """
        if not self.config.enabled:
            return []
        
        rules = []
        
        # 1. Блокировка частных IP (если включено)
        if self.config.block_private_ips:
            rules.append({
                "type": "field",
                "outboundTag": "block",
                "ip": [
                    "geoip:private"
                ]
            })
        
        # 2. Блокировка BitTorrent (если включено)
        if self.config.block_bittorrent:
            rules.append({
                "type": "field",
                "outboundTag": "block",
                "protocol": ["bittorrent"]
            })
        
        # 3. Прямое подключение для российских сервисов
        direct_domains = self.get_direct_domains()
        if direct_domains:
            # Группировка по доменам верхнего уровня
            domain_rules = self._group_domains_for_xray(direct_domains)
            rules.append({
                "type": "field",
                "outboundTag": "direct",
                "domain": domain_rules
            })
        
        # 4. Прямое подключение для локальных сетей
        if self.config.custom_direct_ips:
            rules.append({
                "type": "field",
                "outboundTag": "direct",
                "ip": self._normalize_ips(self.config.custom_direct_ips)
            })
        
        # 5. VPN для заблокированных ресурсов
        proxy_domains = self.get_proxy_domains()
        if proxy_domains:
            domain_rules = self._group_domains_for_xray(proxy_domains)
            rules.append({
                "type": "field",
                "outboundTag": "proxy",
                "domain": domain_rules
            })
        
        # 6. VPN для кастомных IP
        if self.config.custom_proxy_ips:
            rules.append({
                "type": "field",
                "outboundTag": "proxy",
                "ip": self._normalize_ips(self.config.custom_proxy_ips)
            })
        
        # 7. GeoIP правила
        rules.append({
            "type": "field",
            "outboundTag": "direct",
            "ip": ["geoip:ru"]
        })
        
        # 8. GeoSite правила
        rules.append({
            "type": "field",
            "outboundTag": "direct",
            "domain": ["geosite:category-ru"]
        })
        
        return rules
    
    def get_proxy_domains(self) -> List[str]:
        """
        Получение списка доменов для VPN.
        
        Returns:
            Список доменов
        """
        domains = set()
        
        # Домены из категорий blacklist
        for category in self.config.blacklist_categories:
            if category in self.DEFAULT_CATEGORIES:
                domains.update(self.DEFAULT_CATEGORIES[category])
        
        # Кастомные домены
        domains.update(self.config.custom_proxy_domains)
        
        # Исключение прямых доменов
        domains -= set(self.config.custom_direct_domains)
        
        return sorted(list(domains))
    
    def get_direct_domains(self) -> List[str]:
        """
        Получение списка доменов для прямого подключения.
        
        Returns:
            Список доменов
        """
        domains = set()
        
        # Домены из категорий whitelist
        for category in self.config.whitelist_categories:
            if category in self.DEFAULT_CATEGORIES:
                domains.update(self.DEFAULT_CATEGORIES[category])
        
        # Кастомные домены
        domains.update(self.config.custom_direct_domains)
        
        # Исключение прокси доменов
        domains -= set(self.config.custom_proxy_domains)
        
        return sorted(list(domains))
    
    def check_domain(self, domain: str) -> RouteAction:
        """
        Проверка домена и определение маршрута.
        
        Args:
            domain: Домен для проверки
        
        Returns:
            Действие маршрутизации
        """
        domain = domain.lower().strip('.')
        
        # Проверка кастомных правил
        for d in self.config.custom_proxy_domains:
            if domain == d or domain.endswith('.' + d):
                return RouteAction.PROXY
        
        for d in self.config.custom_direct_domains:
            if domain == d or domain.endswith('.' + d):
                return RouteAction.DIRECT
        
        # Проверка категорий
        for category in self.config.blacklist_categories:
            if category in self.DEFAULT_CATEGORIES:
                for d in self.DEFAULT_CATEGORIES[category]:
                    if domain == d or domain.endswith('.' + d):
                        return RouteAction.PROXY
        
        for category in self.config.whitelist_categories:
            if category in self.DEFAULT_CATEGORIES:
                for d in self.DEFAULT_CATEGORIES[category]:
                    if domain == d or domain.endswith('.' + d):
                        return RouteAction.DIRECT
        
        # По умолчанию - напрямую
        return RouteAction.DIRECT
    
    def check_ip(self, ip: str) -> RouteAction:
        """
        Проверка IP адреса и определение маршрута.
        
        Args:
            ip: IP адрес для проверки
        
        Returns:
            Действие маршрутизации
        """
        # Проверка кастомных IP
        if ip in self.config.custom_proxy_ips:
            return RouteAction.PROXY
        
        if ip in self.config.custom_direct_ips:
            return RouteAction.DIRECT
        
        # Проверка частных IP
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return RouteAction.DIRECT if not self.config.block_private_ips else RouteAction.BLOCK
        except ValueError:
            pass
        
        # По умолчанию - напрямую
        return RouteAction.DIRECT
    
    def add_custom_proxy_domain(self, domain: str):
        """
        Добавление кастомного домена для VPN.
        
        Args:
            domain: Домен
        """
        if domain not in self.config.custom_proxy_domains:
            self.config.custom_proxy_domains.append(domain)
            self._load_domain_lists()
    
    def add_custom_direct_domain(self, domain: str):
        """
        Добавление кастомного домена для прямого подключения.
        
        Args:
            domain: Домен
        """
        if domain not in self.config.custom_direct_domains:
            self.config.custom_direct_domains.append(domain)
            self._load_domain_lists()
    
    def remove_custom_proxy_domain(self, domain: str):
        """
        Удаление кастомного домена из VPN.
        
        Args:
            domain: Домен
        """
        if domain in self.config.custom_proxy_domains:
            self.config.custom_proxy_domains.remove(domain)
            self._load_domain_lists()
    
    def remove_custom_direct_domain(self, domain: str):
        """
        Удаление кастомного домена из прямого подключения.
        
        Args:
            domain: Домен
        """
        if domain in self.config.custom_direct_domains:
            self.config.custom_direct_domains.remove(domain)
            self._load_domain_lists()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики split-tunneling.
        
        Returns:
            Статистика
        """
        return {
            'enabled': self.config.enabled,
            'proxy_domains_count': len(self.get_proxy_domains()),
            'direct_domains_count': len(self.get_direct_domains()),
            'custom_proxy_domains': len(self.config.custom_proxy_domains),
            'custom_direct_domains': len(self.config.custom_direct_ips),
            'blacklist_categories': self.config.blacklist_categories,
            'whitelist_categories': self.config.whitelist_categories,
            'block_bittorrent': self.config.block_bittorrent,
            'block_private_ips': self.config.block_private_ips
        }
    
    def export_rules(self, file_path: Path) -> bool:
        """
        Экспорт правил маршрутизации в файл.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если экспорт успешен
        """
        try:
            rules = self.generate_routing_rules()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def import_rules(self, file_path: Path) -> bool:
        """
        Импорт правил маршрутизации из файла.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если импорт успешен
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            # Парсинг правил
            for rule in rules:
                if rule.get('outboundTag') == 'proxy':
                    if 'domain' in rule:
                        self.config.custom_proxy_domains.extend(rule['domain'])
                    if 'ip' in rule:
                        self.config.custom_proxy_ips.extend(rule['ip'])
                elif rule.get('outboundTag') == 'direct':
                    if 'domain' in rule:
                        self.config.custom_direct_domains.extend(rule['domain'])
                    if 'ip' in rule:
                        self.config.custom_direct_ips.extend(rule['ip'])
            
            self._load_domain_lists()
            return True
        except (IOError, json.JSONDecodeError):
            return False
    
    # ==========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _load_domain_lists(self):
        """Загрузка списков доменов из файлов"""
        data_file = Path.home() / "vpn-client-aggregator" / "data" / "domain-lists.json"
        
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    lists = json.load(f)
                
                # Обновление категорий по умолчанию
                for category, domains in lists.items():
                    if category in self.DEFAULT_CATEGORIES:
                        self.DEFAULT_CATEGORIES[category] = list(set(
                            self.DEFAULT_CATEGORIES[category] + domains
                        ))
            except:
                pass
    
    def _group_domains_for_xray(self, domains: List[str]) -> List[str]:
        """
        Группировка доменов для Xray (оптимизация правил).
        
        Args:
            domains: Список доменов
        
        Returns:
            Оптимизированный список правил
        """
        # Используем full: для точного совпадения и keyword: для частичного
        rules = []
        
        for domain in domains:
            if domain.startswith('full:') or domain.startswith('keyword:') or domain.startswith('domain:'):
                rules.append(domain)
            elif domain.startswith('.'):
                rules.append(f"domain:{domain[1:]}")
            else:
                rules.append(f"domain:{domain}")
        
        return rules
    
    def _normalize_ips(self, ips: List[str]) -> List[str]:
        """
        Нормализация IP адресов (добавление CIDR если нужно).
        
        Args:
            ips: Список IP адресов
        
        Returns:
            Нормализованный список
        """
        normalized = []
        
        for ip in ips:
            if '/' in ip:
                # Уже CIDR
                normalized.append(ip)
            else:
                # Одиночный IP
                normalized.append(ip)
        
        return normalized
    
    def _parse_domain_pattern(self, pattern: str) -> Tuple[str, str]:
        """
        Парсинг шаблона домена.
        
        Args:
            pattern: Шаблон (domain:, keyword:, full:, regex:)
        
        Returns:
            Кортеж (type, value)
        """
        if pattern.startswith('domain:'):
            return ('domain', pattern[7:])
        elif pattern.startswith('keyword:'):
            return ('keyword', pattern[8:])
        elif pattern.startswith('full:'):
            return ('full', pattern[5:])
        elif pattern.startswith('regex:'):
            return ('regex', pattern[6:])
        else:
            return ('domain', pattern)


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование SplitTunnelManager...")
    
    # Создание менеджера
    manager = SplitTunnelManager(SplitTunnelConfig(
        enabled=True,
        blacklist_categories=['social', 'video', 'ai'],
        whitelist_categories=['russian_services'],
        block_bittorrent=True,
        block_private_ips=False
    ))
    
    # Генерация правил
    print("\n📋 Правила маршрутизации:")
    rules = manager.generate_routing_rules()
    print(f"   Всего правил: {len(rules)}")
    
    for i, rule in enumerate(rules[:5]):
        print(f"   {i+1}. {rule.get('outboundTag')}: {rule.get('domain', rule.get('ip', ['N/A']))[0] if rule.get('domain') or rule.get('ip') else rule.get('protocol', 'N/A')}")
    
    if len(rules) > 5:
        print(f"   ... и ещё {len(rules) - 5} правил")
    
    # Проверка доменов
    print("\n🌐 Проверка доменов:")
    test_domains = [
        "youtube.com",
        "vk.com",
        "chatgpt.com",
        "google.com",
        "lovable.dev"
    ]
    
    for domain in test_domains:
        action = manager.check_domain(domain)
        print(f"   {domain}: {action.value}")
    
    # Статистика
    print("\n📊 Статистика:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ SplitTunnelManager готов к работе!")
