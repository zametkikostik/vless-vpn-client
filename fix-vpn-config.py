#!/usr/bin/env python3
"""
Быстрое исправление VPN - Пересоздание конфига
"""

import json
from pathlib import Path

SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "servers.json"
CONFIG_FILE = Path.home() / "vless-vpn-client" / "config" / "config.json"

# Загружаем серверы
with open(SERVERS_FILE, 'r') as f:
    servers = json.load(f)

# Выбираем первый рабочий сервер
server = None
for s in servers:
    if s.get('status') == 'online' and s.get('security') == 'reality':
        server = s
        break

if not server:
    print("❌ Нет рабочих серверов!")
    exit(1)

print(f"✅ Выбран сервер: {server['host']}:{server['port']}")

# Создаём простой конфиг БЕЗ fragment
reality = server.get('streamSettings', {}).get('realitySettings', {})

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
                    "flow": "xtls-rprx-vision"
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

# Сохраняем
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✅ Конфиг создан: {CONFIG_FILE}")
print("Теперь перезапустите VPN:")
print("  vless-vpn-ultimate stop")
print("  vless-vpn-ultimate start")
