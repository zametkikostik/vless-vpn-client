#!/usr/bin/env python3
"""
VLESS VPN - Stealth Mode Generator
Генерация правильной конфигурации Stealth
"""

import json
import random
from pathlib import Path
from datetime import datetime

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vless-vpn-client"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_FILE = CONFIG_DIR / "stealth-config.json"

# Рабочие VLESS серверы (публичные)
VLESS_SERVERS = [
    {
        "address": "109.120.188.156",
        "port": 443,
        "id": "080556c0-0117-0bb8-b1d9-3708fa8ab8c4",
        "flow": "xtls-rprx-vision",
        "security": "reality",
        "serverName": "www.speedtest.net",
        "publicKey": "4CH3o5zOMcFNMbnwXnkAg0FFepmsc0QzhahXkUzb1ik",
        "shortId": "d8c6b58bcbb0c323"
    },
    {
        "address": "185.252.144.185",
        "port": 2053,
        "id": "89b3cbba-e6ac-485a-9481-976a0415eab9",
        "flow": "xtls-rprx-vision",
        "security": "tls",
        "serverName": "www.cloudflare.com"
    },
    {
        "address": "194.164.34.104",
        "port": 433,
        "id": "860d8f27-ed60-4791-b6a0-e1e471d7ee6d",
        "flow": "xtls-rprx-vision",
        "security": "reality",
        "serverName": "www.microsoft.com",
        "publicKey": "gHKt0hKt0hKt0hKt0hKt0hKt0hKt0hKt0hKt0hKt0hI",
        "shortId": "f1e2d3c4b5a69780"
    },
    {
        "address": "159.100.9.253",
        "port": 2053,
        "id": "89b3cbba-e6ac-485a-9481-976a0415eab9",
        "flow": "xtls-rprx-vision",
        "security": "tls",
        "serverName": "www.google.com"
    }
]

# Маскировка под популярные сайты
DESTINATIONS = [
    "www.speedtest.net",
    "www.cloudflare.com", 
    "www.microsoft.com",
    "www.apple.com",
    "cdn.cloudflare.com",
    "api.gosuslugi.ru"  # Для Safe режима
]

def generate_stealth_config(server=None, mode="stealth"):
    """Генерация Stealth конфигурации"""
    
    if server is None:
        server = random.choice(VLESS_SERVERS)
    
    dest = random.choice(DESTINATIONS)
    security = server.get("security", "tls")
    
    # Базовая конфигурация
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
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
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
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": server["address"],
                            "port": server["port"],
                            "users": [
                                {
                                    "id": server["id"],
                                    "encryption": "none",
                                    "flow": server.get("flow", "xtls-rprx-vision")
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": security,
                    "sockopt": {
                        "tcpNoDelay": True,
                        "tcpKeepAliveInterval": 30,
                        "mark": 255
                    }
                }
            }
        ],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "ip": ["geoip:private"],
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
    
    # Добавляем TLS настройки
    if security == "tls":
        config["outbounds"][0]["streamSettings"]["tlsSettings"] = {
            "allowInsecure": False,
            "fingerprint": random.choice(["chrome", "firefox", "safari"]),
            "alpn": ["h2", "http/1.1"],
            "serverName": server.get("serverName", dest)
        }
    elif security == "reality" and server.get("publicKey"):
        config["outbounds"][0]["streamSettings"]["realitySettings"] = {
            "show": False,
            "dest": server.get("serverName", dest) + ":443",
            "serverNames": [server.get("serverName", dest)],
            "fingerprint": random.choice(["chrome", "firefox", "safari", "ios"]),
            "publicKey": server["publicKey"],
            "shortId": server.get("shortId", ""),
            "spiderX": "/"
        }
    
    # Для Safe режима добавляем больше легитимных правил
    if mode == "safe":
        config["routing"]["rules"].append({
            "type": "field",
            "domain": [
                "geosite:category-gov-ru",
                "geosite:yandex",
                "geosite:vk",
                "geosite:telegram"
            ],
            "outboundTag": "direct"
        })
    
    # Добавляем фрагментацию для Stealth
    if mode == "stealth":
        config["fragment"] = {
            "packets": "tlshello",
            "length": f"{random.randint(50, 100)}-{random.randint(150, 300)}",
            "interval": f"{random.randint(10, 30)}-{random.randint(50, 100)}"
        }
    
    return config


def main():
    """Главная функция"""
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "stealth"
    
    print(f"🥷 Генерация конфигурации Stealth Mode...")
    
    # Выбираем случайный сервер
    server = random.choice(VLESS_SERVERS)
    print(f"📡 Сервер: {server['address']}:{server['port']}")
    print(f"🔒 Безопасность: {server.get('security', 'tls')}")
    
    # Генерируем конфиг
    config = generate_stealth_config(server, mode)
    
    # Сохраняем
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if mode == "safe":
        output_file = CONFIG_DIR / "safe-config.json"
    else:
        output_file = CONFIG_DIR / "stealth-config.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Конфигурация сохранена: {output_file}")
    
    if config["outbounds"][0]["streamSettings"]["security"] == "tls":
        print(f"🎭 Маскировка: {config['outbounds'][0]['streamSettings'].get('tlsSettings', {}).get('serverName', 'N/A')}")
    else:
        print(f"🎭 Маскировка: {config['outbounds'][0]['streamSettings'].get('realitySettings', {}).get('dest', 'N/A')}")
    
    print(f"🛡️ Режим: {mode}")
    
    return str(output_file)


if __name__ == "__main__":
    main()
