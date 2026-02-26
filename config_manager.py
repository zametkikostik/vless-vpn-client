#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Менеджер конфигураций - управление настройками клиента

© 2026 VPN Client Aggregator
"""

import json
import secrets
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """
    Менеджер конфигураций VPN клиента.
    Отвечает за загрузку, сохранение и валидацию настроек.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Инициализация менеджера конфигураций.
        
        Args:
            config_dir: Директория для хранения конфигураций.
                       По умолчанию: ~/vpn-client-aggregator/config
        """
        if config_dir is None:
            self.config_dir = Path.home() / "vpn-client-aggregator" / "config"
        else:
            self.config_dir = config_dir
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "client.json"
        self.servers_file = self.config_dir / "servers.json"
        self.rules_file = self.config_dir / "rules.json"
        
        self._config: Optional[Dict[str, Any]] = None
    
    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла.
        
        Returns:
            Словарь с конфигурацией
        """
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # Валидация и дополнение значениями по умолчанию
                self._config = self._merge_with_defaults(self._config)
                return self._config
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
                self._config = self._default_config()
                return self._config
        else:
            self._config = self._default_config()
            return self._config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохранение конфигурации в файл.
        
        Args:
            config: Конфигурация для сохранения. Если None, сохраняется текущая.
        
        Returns:
            True если сохранение успешно
        """
        if config is not None:
            self._config = config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Обновление части конфигурации.
        
        Args:
            updates: Словарь с обновлениями
        
        Returns:
            True если обновление успешно
        """
        config = self.load_config()
        
        # Рекурсивное обновление
        self._recursive_update(config, updates)
        
        return self.save_config(config)
    
    # ==========================================================================
    # ГЕНЕРАЦИЯ КОНФИГУРАЦИИ XRAY
    # ==========================================================================
    
    def generate_xray_config(self, split_tunnel_rules: Optional[list] = None) -> Dict[str, Any]:
        """
        Генерация конфигурации для Xray-core.
        
        Args:
            split_tunnel_rules: Правила для split-tunneling
        
        Returns:
            Конфигурация Xray в формате JSON
        """
        config = self.load_config()
        server = config.get('server', {})
        
        xray_config = {
            "log": {
                "loglevel": "warning",
                "access": str(Path.home() / "vpn-client-aggregator" / "logs" / "access.log"),
                "error": str(Path.home() / "vpn-client-aggregator" / "logs" / "error.log")
            },
            "inbounds": [
                {
                    "port": 10808,
                    "protocol": "socks",
                    "settings": {
                        "auth": "noauth",
                        "udp": True,
                        "userLevel": 8
                    },
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls", "quic"],
                        "routeOnly": True,
                        "metadataOnly": False
                    }
                },
                {
                    "port": 10809,
                    "protocol": "http",
                    "settings": {
                        "userLevel": 8
                    }
                }
            ],
            "outbounds": [
                {
                    "tag": "proxy",
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": server.get('address', '127.0.0.1'),
                                "port": server.get('port', 443),
                                "users": [
                                    {
                                        "id": server.get('uuid', ''),
                                        "flow": server.get('flow', 'xtls-rprx-vision'),
                                        "encryption": "none",
                                        "level": 8
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": self._generate_stream_settings(server),
                    "mux": {
                        "enabled": True,
                        "concurrency": 8,
                        "xudpConcurrency": 16,
                        "xudpProxyUDP443": "reject"
                    }
                },
                {
                    "tag": "direct",
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "AsIs",
                        "redirect": "",
                        "noises": []
                    }
                },
                {
                    "tag": "block",
                    "protocol": "blackhole",
                    "settings": {
                        "response": {
                            "type": "http"
                        }
                    }
                }
            ],
            "routing": self._generate_routing(split_tunnel_rules),
            "observatory": {
                "subjectSelector": ["proxy", "direct"],
                "probeUrl": "https://www.google.com/generate_204",
                "probeInterval": "30s",
                "enableConcurrency": True
            },
            "policy": {
                "levels": {
                    "8": {
                        "connIdle": 300,
                        "downlinkOnly": 1,
                        "handshake": 4,
                        "uplinkOnly": 1
                    }
                },
                "system": {
                    "statsOutboundUplink": True,
                    "statsOutboundDownlink": True
                }
            }
        }
        
        # DPI bypass настройки
        if config.get('dpi_bypass', {}).get('enabled', True):
            xray_config = self._apply_dpi_bypass(xray_config, config['dpi_bypass'])
        
        return xray_config
    
    # ==========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            "version": "5.0",
            "created_at": datetime.now().isoformat(),
            "server": {
                "address": "",
                "port": 443,
                "uuid": "",
                "flow": "xtls-rprx-vision",
                "sni": "google.com",
                "alpn": ["h2", "http/1.1"],
                "fingerprint": "chrome",
                "reality": {
                    "enabled": True,
                    "show": False,
                    "short_id": "",
                    "spider_x": ""
                }
            },
            "split_tunnel": {
                "enabled": True,
                "blacklist_categories": ["social", "video", "ai", "blocked_media"],
                "whitelist_categories": ["russian_services", "local_network"],
                "custom_domains": []
            },
            "dpi_bypass": {
                "enabled": True,
                "fragment_packets": True,
                "fragment_size_min": 50,
                "fragment_size_max": 200,
                "fragment_interval_min": 10,
                "fragment_interval_max": 50,
                "padding_enabled": True,
                "padding_min": 100,
                "padding_max": 500
            },
            "auto_reconnect": {
                "enabled": True,
                "max_attempts": 10,
                "delay_seconds": 5,
                "health_check_interval": 30,
                "health_check_url": "https://www.google.com/generate_204"
            },
            "connection": {
                "tcp_keep_alive": 30,
                "tcp_no_delay": True,
                "multipath": False
            },
            "auto_start": False,
            "kill_switch": False,
            "log_level": "warning"
        }
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Слияние конфигурации со значениями по умолчанию"""
        defaults = self._default_config()
        self._recursive_update(defaults, config)
        return defaults
    
    def _recursive_update(self, base: Dict[str, Any], updates: Dict[str, Any]):
        """Рекурсивное обновление словаря"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._recursive_update(base[key], value)
            else:
                base[key] = value
    
    def _generate_stream_settings(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация настроек потока"""
        reality = server.get('reality', {})
        
        return {
            "network": "tcp",
            "security": "reality" if reality.get('enabled', True) else "none",
            "realitySettings": {
                "show": reality.get('show', False),
                "fingerprint": server.get('fingerprint', 'chrome'),
                "serverName": server.get('sni', 'google.com'),
                "shortId": reality.get('short_id', ''),
                "spiderX": reality.get('spider_x', ''),
                "publicKey": ""  # Будет установлен при подключении
            },
            "tcpSettings": {
                "acceptProxyProtocol": False,
                "header": {
                    "type": "none"
                }
            },
            "sockopt": {
                "tcpNoDelay": True,
                "tcpKeepAliveInterval": 30,
                "tcpKeepAliveIdle": 300,
                "mark": 255,
                "tproxy": "off"
            }
        }
    
    def _generate_routing(self, split_tunnel_rules: Optional[list] = None) -> Dict[str, Any]:
        """Генерация правил маршрутизации"""
        routing = {
            "domainStrategy": "IPIfNonMatch",
            "domainMatcher": "hybrid",
            "rules": [
                {
                    "type": "field",
                    "outboundTag": "block",
                    "ip": ["geoip:private"]
                }
            ]
        }
        
        if split_tunnel_rules:
            # Правила для VPN
            routing["rules"].append({
                "type": "field",
                "outboundTag": "proxy",
                "domain": split_tunnel_rules
            })
        else:
            # Правила по умолчанию
            routing["rules"].append({
                "type": "field",
                "outboundTag": "direct",
                "domain": ["geosite:category-ru"]
            })
            routing["rules"].append({
                "type": "field",
                "outboundTag": "proxy",
                "domain": [
                    "geosite:youtube",
                    "geosite:facebook",
                    "geosite:twitter",
                    "geosite:instagram",
                    "geosite:telegram",
                    "geosite:openai",
                    "geosite:anthropic"
                ]
            })
        
        return routing
    
    def _apply_dpi_bypass(self, config: Dict[str, Any], dpi_config: Dict[str, Any]) -> Dict[str, Any]:
        """Применение настроек обхода DPI"""
        # Добавляем fragment настройки
        if dpi_config.get('fragment_packets', True):
            # Fragment применяется на уровне stream settings
            for outbound in config.get('outbounds', []):
                if outbound.get('tag') == 'proxy':
                    if 'streamSettings' not in outbound:
                        outbound['streamSettings'] = {}
                    
                    # Добавляем fragment
                    outbound['streamSettings']['sockopt'] = outbound['streamSettings'].get('sockopt', {})
                    outbound['streamSettings']['sockopt'].update({
                        "tcpNoDelay": True,
                        "tcpKeepAliveInterval": dpi_config.get('fragment_interval_min', 10),
                        "mark": 255
                    })
        
        return config
    
    # ==========================================================================
    # УТИЛИТЫ
    # ==========================================================================
    
    @staticmethod
    def validate_uuid(uuid: str) -> bool:
        """
        Проверка валидности UUID.
        
        Args:
            uuid: UUID для проверки
        
        Returns:
            True если UUID валиден
        """
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid.lower()))
    
    @staticmethod
    def generate_uuid() -> str:
        """
        Генерация безопасного UUID v4.
        
        Returns:
            Новый UUID
        """
        return str(secrets.uuid4())
    
    @staticmethod
    def validate_server_ip(ip: str) -> bool:
        """
        Проверка IP адреса сервера.
        
        Args:
            ip: IP адрес для проверки
        
        Returns:
            True если IP валиден
        """
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not bool(re.match(pattern, ip)):
            return False
        
        # Проверка диапазона октетов
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """
        Проверка доменного имени.
        
        Args:
            domain: Домен для проверки
        
        Returns:
            True если домен валиден
        """
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """
        Хеширование чувствительных данных (SHA-256).
        
        Args:
            data: Данные для хеширования
        
        Returns:
            SHA-256 хеш
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики конфигурации.
        
        Returns:
            Статистика
        """
        config = self.load_config()
        
        return {
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
            "server_configured": bool(config.get('server', {}).get('address')),
            "split_tunnel_enabled": config.get('split_tunnel', {}).get('enabled', False),
            "dpi_bypass_enabled": config.get('dpi_bypass', {}).get('enabled', False),
            "auto_reconnect_enabled": config.get('auto_reconnect', {}).get('enabled', False),
            "version": config.get('version', 'unknown')
        }


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование ConfigManager...")
    
    manager = ConfigManager()
    
    # Загрузка конфигурации
    config = manager.load_config()
    print(f"✅ Конфигурация загружена")
    print(f"   Версия: {config.get('version')}")
    print(f"   Split-tunneling: {config.get('split_tunnel', {}).get('enabled')}")
    print(f"   DPI bypass: {config.get('dpi_bypass', {}).get('enabled')}")
    print(f"   Auto-reconnect: {config.get('auto_reconnect', {}).get('enabled')}")
    
    # Генерация UUID
    new_uuid = manager.generate_uuid()
    print(f"\n✅ Сгенерирован UUID: {new_uuid}")
    print(f"   Валиден: {manager.validate_uuid(new_uuid)}")
    
    # Статистика
    stats = manager.get_stats()
    print(f"\n📊 Статистика:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ ConfigManager готов к работе!")
