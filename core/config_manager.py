#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager - Управление конфигурацией приложения
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading


class ConfigManager:
    """Менеджер конфигурации (Singleton)"""
    
    _instance = None
    _lock = threading.Lock()
    
    # Источники конфигураций по умолчанию (31 источник)
    DEFAULT_SOURCES = [
        {"name": "sakha1370/OpenRay", "url": "https://raw.githubusercontent.com/sakha1370/OpenRay/main/subscription.txt", "enabled": True},
        {"name": "sevcator/5ubscrpt10n", "url": "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/subscription.txt", "enabled": True},
        {"name": "yitong2333/proxy-minging", "url": "https://raw.githubusercontent.com/yitong2333/proxy-minging/main/subscription.txt", "enabled": True},
        {"name": "acyzm/AutoVPN", "url": "https://raw.githubusercontent.com/acyzm/AutoVPN/main/subscription.txt", "enabled": True},
        {"name": "miladtahanian/V2RayCFGDumper", "url": "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/main/subscription.txt", "enabled": True},
        {"name": "roosterkid/openproxylist", "url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/subscription.txt", "enabled": True},
        {"name": "Epodonios/v2ray-configs", "url": "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/subscription.txt", "enabled": True},
        {"name": "CidVpn/cid-vpn-config", "url": "https://raw.githubusercontent.com/CidVpn/cid-vpn-config/main/subscription.txt", "enabled": True},
        {"name": "mohamadfg-dev/telegram-v2ray-configs-collector", "url": "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/main/subscription.txt", "enabled": True},
        {"name": "mheidari98/.proxy", "url": "https://raw.githubusercontent.com/mheidari98/.proxy/main/subscription.txt", "enabled": True},
        {"name": "youfoundamin/V2rayCollector", "url": "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/subscription.txt", "enabled": True},
        {"name": "expressalaki/ExpressVPN", "url": "https://raw.githubusercontent.com/expressalaki/ExpressVPN/main/subscription.txt", "enabled": True},
        {"name": "MahsaNetConfigTopic/config", "url": "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/main/subscription.txt", "enabled": True},
        {"name": "LalatinaHub/Mineral", "url": "https://raw.githubusercontent.com/LalatinaHub/Mineral/main/subscription.txt", "enabled": True},
        {"name": "miladtahanian/Config-Collector", "url": "https://raw.githubusercontent.com/miladtahanian/Config-Collector/main/subscription.txt", "enabled": True},
        {"name": "Pawdroid/Free-servers", "url": "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/subscription.txt", "enabled": True},
        {"name": "MhdiTaheri/V2rayCollector_Py", "url": "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/subscription.txt", "enabled": True},
        {"name": "free18/v2ray", "url": "https://raw.githubusercontent.com/free18/v2ray/main/subscription.txt", "enabled": True},
        {"name": "MhdiTaheri/V2rayCollector", "url": "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/main/subscription.txt", "enabled": True},
        {"name": "Argh94/Proxy-List", "url": "https://raw.githubusercontent.com/Argh94/Proxy-List/main/subscription.txt", "enabled": True},
        {"name": "shabane/kamaji", "url": "https://raw.githubusercontent.com/shabane/kamaji/main/subscription.txt", "enabled": True},
        {"name": "wuqb2i4f/xray-config-toolkit", "url": "https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/subscription.txt", "enabled": True},
        {"name": "Delta-Kronecker/V2ray-Config", "url": "https://raw.githubusercontent.com/Delta-Kronecker/V2ray-Config/main/subscription.txt", "enabled": True},
        {"name": "STR97/STRUGOV", "url": "https://raw.githubusercontent.com/STR97/STRUGOV/main/subscription.txt", "enabled": True},
        {"name": "V2RayRoot/V2RayConfig", "url": "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/subscription.txt", "enabled": True},
        {"name": "AvenCores/goida-vpn-configs", "url": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/subscription.txt", "enabled": True},
        # Igareck - VLESS Reality + White Lists
        {"name": "igareck/Vless-Reality-Rus-Mobile", "url": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt", "enabled": True},
        {"name": "igareck/Vless-Reality-Rus-Mobile-2", "url": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt", "enabled": True},
        # Igareck - White CIDR/SNI списки для маршрутизации
        {"name": "igareck/WHITE-CIDR-RU-all", "url": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt", "enabled": True},
        {"name": "igareck/WHITE-CIDR-RU-checked", "url": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt", "enabled": True},
        {"name": "igareck/WHITE-SNI-RU-all", "url": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt", "enabled": True},
    ]
    
    # Настройки по умолчанию
    DEFAULT_CONFIG = {
        "auto_connect": False,
        "auto_update_hours": 6,
        "smart_routing": True,
        "anti_dpi": True,
        "system_proxy": True,
        "tun_mode": False,
        "proxy_port": 10808,
        "socks_port": 10809,
        "api_port": 8080,
        "sources": DEFAULT_SOURCES,
        "blocked_services": [
            "youtube.com",
            "instagram.com",
            "facebook.com",
            "twitter.com",
            "openai.com",
            "tiktok.com"
        ],
        "ru_domains": [".ru", ".рф", ".su"],
        "last_update": None,
        "selected_server": None
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Инициализация менеджера конфигурации"""
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Путь по умолчанию: ~/.anticensor/config.json
            home = Path.home()
            config_dir = home / ".anticensor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"
        
        self.config: Dict[str, Any] = {}
        self.is_loaded = False
    
    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> 'ConfigManager':
        """Получить экземпляр (Singleton)"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config_path)
            return cls._instance
    
    def load(self) -> bool:
        """Загрузить конфигурацию из файла"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Обновляем значения по умолчанию
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self.save()
            
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.DEFAULT_CONFIG.copy()
            return False
    
    def save(self) -> bool:
        """Сохранить конфигурацию в файл"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение конфигурации"""
        self.config[key] = value
    
    def update_last_update(self) -> None:
        """Обновить время последнего обновления"""
        self.config["last_update"] = datetime.now().isoformat()
        self.save()
    
    def needs_update(self) -> bool:
        """Проверить, нужно ли обновление конфигураций"""
        last_update = self.config.get("last_update")
        if not last_update:
            return True
        
        try:
            last = datetime.fromisoformat(last_update)
            hours = self.config.get("auto_update_hours", 6)
            delta = datetime.now() - last
            return delta.total_seconds() >= hours * 3600
        except:
            return True
    
    def get_sources(self) -> List[Dict]:
        """Получить список источников"""
        sources = self.config.get("sources", [])
        return [s for s in sources if s.get("enabled", True)]
    
    def get_routing_config(self) -> Dict:
        """Получить настройки маршрутизации"""
        return {
            "smart_routing": self.config.get("smart_routing", True),
            "blocked_services": self.config.get("blocked_services", []),
            "ru_domains": self.config.get("ru_domains", [])
        }
