#!/usr/bin/env python3
"""
Исправление Reality серверов в базе данных
"""

import json
from pathlib import Path

DATA_FILE = Path("/home/kostik/vless-vpn-client/data/servers.json")

# Правильные SNI для Reality серверов
VALID_SNI = {
    "max.ru": "www.speedtest.net",  # Исправляем нерабочий
    "www.speedtest.net": "www.speedtest.net",
    "www.cloudflare.com": "www.cloudflare.com",
    "www.microsoft.com": "www.microsoft.com",
    "www.apple.com": "www.apple.com",
    "www.google.com": "www.google.com",
}

def fix_reality_servers():
    """Исправление Reality серверов"""
    
    if not DATA_FILE.exists():
        print(f"❌ Файл не найден: {DATA_FILE}")
        return
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        servers = json.load(f)
    
    print(f"📊 Всего серверов: {len(servers)}")
    
    fixed_count = 0
    for server in servers:
        if server.get('security') == 'reality':
            old_sni = server.get('sni', '')
            new_sni = VALID_SNI.get(old_sni)
            
            if new_sni and new_sni != old_sni:
                print(f"🔧 Исправлен: {server['host']}:{server['port']}")
                print(f"   {old_sni} → {new_sni}")
                
                server['sni'] = new_sni
                if 'streamSettings' in server:
                    server['streamSettings']['realitySettings']['serverName'] = new_sni
                
                fixed_count += 1
    
    # Сохраняем
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(servers, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Исправлено серверов: {fixed_count}")
    print(f"💾 Сохранено: {DATA_FILE}")

if __name__ == "__main__":
    fix_reality_servers()
