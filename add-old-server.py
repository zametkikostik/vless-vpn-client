#!/usr/bin/env python3
import json

# Загрузим текущие серверы
with open('/home/kostik/vpn-client/data/servers.json', 'r') as f:
    servers = json.load(f)

# Добавим старый рабочий сервер если его нет
old_server = {
    "host": "217.25.90.152",
    "port": 443,
    "uuid": "24b0a3e8-2a59-4ae9-ae71-6a6b4faae682",
    "name": "OLD_WORKING_SERVER",
    "status": "online",
    "latency": 7,
    "streamSettings": {
        "security": "reality",
        "realitySettings": {
            "serverName": "metahuman.unrealengine.com",
            "fingerprint": "chrome",
            "publicKey": "u5ZxSxn9pYnLLnYjYToY7Sj5S5ZxSxn9pYnLLnYjYTo",
            "shortId": ""
        }
    }
}

# Проверим есть ли уже такой
exists = any(s['host'] == '217.25.90.152' for s in servers)
if not exists:
    servers.insert(0, old_server)
    with open('/home/kostik/vpn-client/data/servers.json', 'w') as f:
        json.dump(servers, f, ensure_ascii=False, indent=2)
    print("✅ Старый сервер добавлен")
else:
    print("ℹ️ Сервер уже есть в базе")
