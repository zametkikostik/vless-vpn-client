#!/usr/bin/env python3
"""
Добавить серверы claude.com в список доступных
Аналогично серверам chatgpt.com
"""
import json
from pathlib import Path
from datetime import datetime

SERVERS_FILE = Path.home() / "vpn-client" / "data" / "servers.json"
BACKUP_FILE = Path.home() / "vpn-client" / "data" / "servers.json.backup"

# Серверы AI-сервисов (claude.com, lovable.dev, etc.)
AI_SERVERS = [
    # Claude AI
    {"host": "claude.com", "port": 443, "name": "🌐 Claude AI [US] | claude.com:443"},
    {"host": "claude.com", "port": 8443, "name": "🌐 Claude AI [US] | claude.com:8443"},
    {"host": "claude.com", "port": 2096, "name": "🌐 Claude AI [US] | claude.com:2096"},
    {"host": "claude.com", "port": 2082, "name": "🌐 Claude AI [US] | claude.com:2082"},
    {"host": "claude.ai", "port": 443, "name": "🌐 Claude AI [US] | claude.ai:443"},
    {"host": "claude.ai", "port": 8443, "name": "🌐 Claude AI [US] | claude.ai:8443"},
    # Lovable.dev
    {"host": "lovable.dev", "port": 443, "name": "🌐 Lovable AI [US] | lovable.dev:443"},
    {"host": "lovable.dev", "port": 8443, "name": "🌐 Lovable AI [US] | lovable.dev:8443"},
    {"host": "lovable.dev", "port": 2096, "name": "🌐 Lovable AI [US] | lovable.dev:2096"},
    {"host": "lovable.dev", "port": 2082, "name": "🌐 Lovable AI [US] | lovable.dev:2082"},
    {"host": "lovable.dev", "port": 80, "name": "🌐 Lovable AI [US] | lovable.dev:80"},
]

def add_ai_servers():
    """Добавить серверы AI-сервисов в файл servers.json"""
    
    # Загрузка текущих серверов
    if not SERVERS_FILE.exists():
        print(f"❌ Файл {SERVERS_FILE} не найден!")
        print("Сначала запустите: vless-vpn update")
        return
    
    with open(SERVERS_FILE) as f:
        servers = json.load(f)
    
    # Создание резервной копии
    with open(BACKUP_FILE, 'w') as f:
        json.dump(servers, f, indent=2, ensure_ascii=False)
    print(f"✅ Создана резервная копия: {BACKUP_FILE}")
    
    # Проверка существующих серверов
    existing_hosts = {(s.get('host', ''), s.get('port')) for s in servers}
    
    # Добавление новых серверов
    added = 0
    for new_server in AI_SERVERS:
        key = (new_server['host'], new_server['port'])
        if key not in existing_hosts:
            servers.append({
                "host": new_server['host'],
                "port": new_server['port'],
                "name": new_server['name'],
                "status": "online",
                "latency": 50.0,  # Начальное значение, обновится при тесте
                "protocol": "VLESS-Reality",
                "added_manually": True,
                "added_date": datetime.now().isoformat()
            })
            added += 1
            print(f"✅ Добавлен: {new_server['host']}:{new_server['port']}")
        else:
            print(f"⏭️  Уже существует: {new_server['host']}:{new_server['port']}")
    
    # Сохранение обновлённого файла
    with open(SERVERS_FILE, 'w') as f:
        json.dump(servers, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Добавлено серверов: {added}")
    print(f"📁 Файл обновлён: {SERVERS_FILE}")
    print("\n🔄 Теперь обновите список серверов в VPN клиенте:")
    print("   vless-vpn update")
    print("   или нажмите 🔄 Обновить в GUI")

if __name__ == "__main__":
    add_ai_servers()
