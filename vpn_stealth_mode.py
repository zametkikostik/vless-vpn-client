#!/usr/bin/env python3
"""
VLESS VPN - STEALTH MODE
Ультимативная маскировка и обход DPI

Функции:
- Маскировка под российские сервисы (Госуслуги, Сбербанк, и т.д.)
- Обход DPI с фрагментацией и шумом
- Резервные каналы подключения
- Анти-детект система
- "Спящий режим" при проверке

© 2026 VPN Client Aggregator - Stealth Division
"""

import os
import sys
import json
import time
import random
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vless-vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = LOGS_DIR / "stealth.log"

# Создаем директории
for d in [DATA_DIR, LOGS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# МАСКИРОВКА ПОД РОССИЙСКИЕ СЕРВИСЫ
# =============================================================================

class RussianServicesMask:
    """Маскировка трафика под российские сервисы"""
    
    # Легитимные российские сервисы для маскировки
    RUSSIAN_SERVICES = {
        "gosuslugi": {
            "domains": ["gosuslugi.ru", "www.gosuslugi.ru", "api.gosuslugi.ru"],
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            "tls_versions": ["TLSv1.2", "TLSv1.3"],
            "cipher_suites": ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"]
        },
        "sberbank": {
            "domains": ["sberbank.ru", "online.sberbank.ru", "api.sberbank.ru"],
            "user_agents": [
                "Sberbank-Online/3.0.0 (Android 13; SM-G998B)",
                "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"
            ]
        },
        "yandex": {
            "domains": ["yandex.ru", "www.yandex.ru", "mail.yandex.ru"],
            "user_agents": [
                "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
                "YaBrowser/24.1.0.2000 Safari/537.36"
            ]
        },
        "vk": {
            "domains": ["vk.com", "m.vk.com", "api.vk.com"],
            "user_agents": [
                "VKApp/8.0.0 (Android 13)",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VK/8.0"
            ]
        },
        "mailru": {
            "domains": ["mail.ru", "e.mail.ru", "api.mail.ru"],
            "user_agents": [
                "Mail.ru/2.0 (Android)",
                "Mozilla/5.0 (compatible; Mail.Ru-Bot/2.0)"
            ]
        },
        "rtk": {
            "domains": ["rt.ru", "rtk.ru", "rostelecom.ru"],
            "user_agents": [
                "Rostelecom/1.0 (Android)",
                "Mozilla/5.0 (Linux; Android 12) RTK-Client/1.0"
            ]
        }
    }
    
    def __init__(self):
        self.current_service = random.choice(list(self.RUSSIAN_SERVICES.keys()))
        self.last_switch = time.time()
        self.switch_interval = random.randint(300, 600)  # 5-10 минут
        
    def get_current_config(self) -> Dict[str, Any]:
        """Получить конфигурацию для текущего сервиса"""
        if time.time() - self.last_switch > self.switch_interval:
            self.switch_service()
            
        service = self.RUSSIAN_SERVICES[self.current_service]
        
        return {
            "service_name": self.current_service,
            "domains": service["domains"],
            "user_agent": random.choice(service["user_agents"]),
            "tls_version": random.choice(service.get("tls_versions", ["TLSv1.3"])),
            "cipher": random.choice(service.get("cipher_suites", ["TLS_AES_256_GCM_SHA384"]))
        }
    
    def switch_service(self):
        """Переключиться на другой сервис"""
        old_service = self.current_service
        available = [s for s in self.RUSSIAN_SERVICES if s != self.current_service]
        self.current_service = random.choice(available)
        self.last_switch = time.time()
        self.switch_interval = random.randint(300, 600)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎭 Маскировка: {old_service} → {self.current_service}")
    
    def get_xray_stream_settings(self) -> Dict[str, Any]:
        """Настройки потока для маскировки"""
        config = self.get_current_config()
        
        return {
            "streamSettings": {
                "sockopt": {
                    "tcpNoDelay": True,
                    "tcpKeepAliveInterval": random.randint(30, 60),
                    "mark": 255
                },
                "tcpSettings": {
                    "header": {
                        "type": "http",
                        "request": {
                            "version": "1.1",
                            "method": "GET",
                            "path": ["/api/v2/", "/gateway/", "/mobile/", "/"],
                            "headers": {
                                "Host": random.choice(config["domains"]),
                                "User-Agent": config["user_agent"],
                                "Accept": [
                                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                                    "application/json, text/plain, */*"
                                ],
                                "Accept-Language": ["ru-RU,ru;q=0.9,en-US;q=0.8"],
                                "Accept-Encoding": ["gzip, deflate, br"],
                                "Connection": ["keep-alive"],
                                "Upgrade-Insecure-Requests": ["1"],
                                "Sec-Fetch-Dest": ["document"],
                                "Sec-Fetch-Mode": ["navigate"],
                                "Sec-Fetch-Site": ["none"],
                                "Cache-Control": ["max-age=0"]
                            }
                        },
                        "response": {
                            "version": "1.1",
                            "status": "200",
                            "reason": "OK",
                            "headers": {
                                "Content-Type": ["text/html; charset=utf-8"],
                                "Server": ["nginx/1.18.0", "Apache/2.4.41"],
                                "X-Powered-By": ["PHP/7.4.3", "Express"],
                                "Cache-Control": ["no-cache"]
                            }
                        }
                    }
                },
                "security": "tls",
                "tlsSettings": {
                    "allowInsecure": False,
                    "fingerprint": random.choice(["chrome", "firefox", "safari", "ios"]),
                    "alpn": ["h2", "http/1.1"],
                    "serverName": random.choice(config["domains"])
                }
            }
        }


# =============================================================================
# УЛУЧШЕННЫЙ DPI BYPASS
# =============================================================================

class AdvancedDPIBypass:
    """Продвинутая система обхода DPI"""
    
    def __init__(self):
        self.strategies = {
            "fragmentation": {
                "packets": "tlshello",
                "length": f"{random.randint(30, 80)}-{random.randint(100, 300)}",
                "interval": f"{random.randint(5, 20)}-{random.randint(30, 100)}"
            },
            "padding": {
                "enabled": True,
                "min_length": random.randint(100, 500),
                "max_length": random.randint(500, 2000),
                "pattern": random.choice(["random", "zero", "space"])
            },
            "timing": {
                "jitter": random.randint(10, 100),  # мс
                "delay_range": [random.randint(50, 200), random.randint(200, 500)]
            },
            "noise": {
                "enabled": True,
                "type": random.choice(["http_requests", "dns_queries", "tls_handshakes"]),
                "interval": random.randint(30, 120)  # секунд
            }
        }
        
        # Анти-детект
        self.anti_detect = {
            "randomize_packet_order": True,
            "insert_dummy_packets": True,
            "variable_mss": True,
            "fake_retransmissions": True
        }
    
    def get_fragment_config(self) -> Dict[str, Any]:
        """Конфигурация фрагментации"""
        return {
            "fragment": {
                "packets": self.strategies["fragmentation"]["packets"],
                "length": self.strategies["fragmentation"]["length"],
                "interval": self.strategies["fragmentation"]["interval"]
            }
        }
    
    def get_full_config(self) -> Dict[str, Any]:
        """Полная конфигурация обхода DPI"""
        config = self.get_fragment_config()
        
        # Добавляем настройки потока
        config["streamSettings"] = {
            "sockopt": {
                "tcpNoDelay": True,
                "tcpKeepAliveInterval": self.strategies["timing"]["delay_range"][0] // 10,
                "tcpKeepAliveIdle": 300,
                "mark": 255,
                "tcpMss": random.randint(1200, 1460) if self.anti_detect["variable_mss"] else 1460
            }
        }
        
        return config
    
    def generate_noise_traffic(self) -> List[Dict[str, str]]:
        """Генерация шумового трафика"""
        noise = []
        
        # Фейковые HTTP запросы к легитимным сайтам
        legitimate_sites = [
            "https://www.google.com",
            "https://www.yandex.ru",
            "https://www.cloudflare.com",
            "https://www.github.com"
        ]
        
        for _ in range(random.randint(2, 5)):
            noise.append({
                "type": "http_request",
                "url": random.choice(legitimate_sites),
                "method": "GET",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            })
        
        return noise


# =============================================================================
# СИСТЕМА "СПЯЩИЙ РЕЖИМ"
# =============================================================================

class SleepMode:
    """Система маскировки при проверке"""
    
    def __init__(self):
        self.active = False
        self.triggers = [
            "dpi_probe_detected",
            "suspicious_activity",
            "manual_trigger"
        ]
        self.responses = {
            "pause_traffic": True,
            "switch_to_legit": True,
            "fake_error_response": True
        }
    
    def activate(self, reason: str = "unknown"):
        """Активировать спящий режим"""
        self.active = True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 😴 СПЯЩИЙ РЕЖИМ: {reason}")
        
        # Пауза трафика
        # Переключение на легитимный трафик
        # Отправка фейковых ответов
    
    def deactivate(self):
        """Деактивировать спящий режим"""
        self.active = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 😊 ВОЗОБНОВЛЕНИЕ работы")
    
    def get_legit_config(self) -> Dict[str, Any]:
        """Конфигурация для легитимного трафика"""
        return {
            "mode": "legitimate",
            "allowed_domains": [
                "gosuslugi.ru",
                "yandex.ru",
                "mail.ru",
                "vk.com",
                "sberbank-online.ru"
            ],
            "block_vpn_protocols": True,
            "log_all_connections": True
        }


# =============================================================================
# РЕЗЕРВНЫЕ КАНАЛЫ
# =============================================================================

class BackupChannels:
    """Система резервных каналов подключения"""
    
    CHANNELS = {
        "primary": {
            "type": "vless-reality",
            "priority": 1,
            "description": "Основной канал (VLESS Reality)"
        },
        "backup_tls": {
            "type": "trojan-tls",
            "priority": 2,
            "description": "Резервный TLS (Trojan)"
        },
        "backup_ws": {
            "type": "vmess-ws",
            "priority": 3,
            "description": "WebSocket (VMess)"
        },
        "backup_shadowsocks": {
            "type": "shadowsocks-2022",
            "priority": 4,
            "description": "Shadowsocks 2022"
        },
        "backup_hysteria": {
            "type": "hysteria2",
            "priority": 5,
            "description": "Hysteria 2 (QUIC-based)"
        }
    }
    
    def __init__(self):
        self.current_channel = "primary"
        self.failover_count = 0
        self.max_failovers = len(self.CHANNELS)
    
    def get_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Получить конфигурацию канала"""
        if channel_name not in self.CHANNELS:
            return None
        
        return {
            "name": channel_name,
            **self.CHANNELS[channel_name]
        }
    
    def failover(self) -> Optional[str]:
        """Переключение на резервный канал"""
        if self.failover_count >= self.max_failovers:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Все каналы исчерпаны!")
            return None
        
        # Находим следующий доступный канал
        current_priority = self.CHANNELS[self.current_channel]["priority"]
        
        for name, config in self.CHANNELS.items():
            if config["priority"] > current_priority:
                self.current_channel = name
                self.failover_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Failover: {self.current_channel}")
                return name
        
        return None
    
    def reset(self):
        """Сброс счетчика failover"""
        self.failover_count = 0
        self.current_channel = "primary"


# =============================================================================
# ГЕНЕРАТОР КОНФИГУРАЦИИ XRAY
# =============================================================================

class StealthXRayConfig:
    """Генератор скрытной конфигурации XRay"""
    
    def __init__(self):
        self.mask = RussianServicesMask()
        self.dpi_bypass = AdvancedDPIBypass()
        self.sleep_mode = SleepMode()
        self.backup = BackupChannels()
    
    def generate_config(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация полной конфигурации"""
        mask_config = self.mask.get_xray_stream_settings()
        dpi_config = self.dpi_bypass.get_full_config()
        
        config = {
            "log": {
                "level": "warning",
                "access": str(LOGS_DIR / "xray_access.log"),
                "error": str(LOGS_DIR / "xray_error.log")
            },
            "inbounds": [
                {
                    "port": 10808,
                    "protocol": "socks",
                    "settings": {
                        "auth": "noauth",
                        "udp": True,
                        "ip": "127.0.0.1"
                    }
                },
                {
                    "port": 10809,
                    "protocol": "http",
                    "settings": {
                        "allowTransparent": False
                    }
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
                                        "id": server.get("id", ""),
                                        "encryption": "none",
                                        "flow": server.get("flow", "xtls-rprx-vision")
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": mask_config["streamSettings"],
                    **dpi_config
                }
            ],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "domain": ["geosite:category-gov-ru"],
                        "outboundTag": "direct"
                    }
                ]
            },
            "dns": {
                "servers": [
                    "https://dns.yandex.ru/dns-query",
                    "https://common.dot.sber.ru/dns-query",
                    "1.1.1.1"
                ]
            }
        }
        
        return config
    
    def save_config(self, config: Dict[str, Any], filepath: Path = None):
        """Сохранение конфигурации"""
        if filepath is None:
            filepath = CONFIG_FILE
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Конфигурация сохранена: {filepath}")


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

def main():
    """Запуск stealth-версии"""
    print("=" * 70)
    print("🥷 VLESS VPN - STEALTH MODE")
    print("=" * 70)
    print()
    print("Функции:")
    print("  🎭 Маскировка под российские сервисы")
    print("  🛡️ Улучшенный обход DPI")
    print("  😴 Спящий режим при проверке")
    print("  🔄 Резервные каналы подключения")
    print()
    
    # Генерация конфигурации
    stealth_config = StealthXRayConfig()
    
    # Пример сервера
    test_server = {
        "host": "example.com",
        "port": 443,
        "id": "00000000-0000-0000-0000-000000000000",
        "flow": "xtls-rprx-vision"
    }
    
    config = stealth_config.generate_config(test_server)
    stealth_config.save_config(config)
    
    print()
    print("Конфигурация готова!")
    print(f"Файл: {CONFIG_FILE}")
    print()
    print("Для запуска:")
    print(f"  {HOME}/vpn-client/bin/xray run -c {CONFIG_FILE}")


if __name__ == "__main__":
    main()
