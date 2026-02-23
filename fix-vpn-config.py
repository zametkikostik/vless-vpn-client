#!/usr/bin/env python3
"""Исправление конфига VPN"""
import json

# Загрузить серверы
with open('/home/kostik/vpn-client/data/servers.json') as f:
    servers = json.load(f)

# Найти онлайн с UUID (НЕ chatgpt.com!)
online = [s for s in servers if s.get('status') == 'online' and s.get('uuid') and 'chatgpt' not in s.get('host', '').lower()]
print(f'Найдено серверов (без chatgpt): {len(online)}')

if online:
    # Выбрать лучший (не chatgpt.com!)
    best = min(online, key=lambda x: x.get('latency', 9999))
    print(f"\n✅ Лучший сервер:")
    print(f"  Хост: {best['host']}")
    print(f"  Порт: {best['port']}")
    print(f"  UUID: {best['uuid'][:20]}...")
    print(f"  Пинг: {best.get('latency', 'N/A')} мс")
    
    # Создать правильный конфиг
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}},
            {"port": 10809, "protocol": "http"}
        ],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": best['host'],
                    "port": best['port'],
                    "users": [{"id": best['uuid'], "encryption": "none", "flow": ""}]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "tls",
                "tlsSettings": {
                    "serverName": best.get('sni', best['host']),
                    "alpn": ["h2", "http/1.1"],
                    "fingerprint": "chrome"
                }
            }
        }]
    }
    
    # Сохранить
    with open('/home/kostik/vpn-client/config/config.json', 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Конфиг обновлён!")
    print(f"Теперь запускайте XRay!")
else:
    print("❌ Нет серверов с UUID!")
