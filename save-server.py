#!/usr/bin/env python3
"""Сохранение первого сервера с Reality в конфиг"""
import json
from pathlib import Path
from config_manager import ConfigManager

# Пути
BASE_DIR = Path.home() / "vpn-client-aggregator"
SERVERS_FILE = BASE_DIR / "data" / "servers.json"

# Загружаем серверы
with open(SERVERS_FILE) as f:
    servers = json.load(f)

print(f"📊 Загружено серверов: {len(servers)}")

# Находим первый сервер с Reality и publicKey
selected_server = None
for server in servers:
    stream = server.get('stream_settings', {})
    reality = stream.get('reality_settings', {})
    if reality.get('publicKey'):
        selected_server = server
        break

if not selected_server:
    print("❌ Сервер с Reality не найден!")
    exit(1)

print("✅ Найден сервер:")
print(f"  Адрес: {selected_server.get('host')}:{selected_server.get('port')}")
print(f"  UUID: {selected_server.get('uuid')}")

# Получаем параметры Reality
stream = selected_server.get('stream_settings', {})
reality = stream.get('reality_settings', {})

# Сохраняем в конфиг
cm = ConfigManager(BASE_DIR)

updates = {
    'server': {
        'address': selected_server.get('host'),
        'port': selected_server.get('port'),
        'uuid': selected_server.get('uuid'),
        'sni': reality.get('serverName', 'google.com'),
        'flow': selected_server.get('flow', 'xtls-rprx-vision'),
        'fingerprint': selected_server.get('fingerprint', 'chrome'),
        'alpn': ['h2', 'http/1.1'],
        'reality': {
            'enabled': True,
            'show': False,
            'short_id': reality.get('shortId', ''),
            'spider_x': ''
        },
        'stream_settings': {
            'reality_settings': {
                'serverName': reality.get('serverName'),
                'publicKey': reality.get('publicKey'),
                'shortId': reality.get('shortId', ''),
                'fingerprint': selected_server.get('fingerprint', 'chrome')
            }
        }
    }
}

result = cm.update_config(updates)
if result:
    print("✅ Сервер сохранён в конфиг!")
    
    # Проверяем
    config = cm.load_config()
    server = config.get('server', {})
    stream_settings = cm._generate_stream_settings(server)
    
    print("\n=== Проверка конфига ===")
    print(f"Address: {server.get('address')}:{server.get('port')}")
    print(f"UUID: {server.get('uuid')[:8]}...")
    print(f"SNI: {server.get('sni')}")
    print(f"PublicKey: {stream_settings['realitySettings']['publicKey'][:20]}...")
    print(f"ShortId: {stream_settings['realitySettings']['shortId']}")
else:
    print("❌ Ошибка сохранения!")
