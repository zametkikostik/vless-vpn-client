#!/usr/bin/env python3
"""
Выбор лучшего сервера для подключения
"""

import json
from pathlib import Path

DATA_FILE = Path("/home/kostik/vless-vpn-client/data/servers.json")
OUTPUT_FILE = Path("/home/kostik/vless-vpn-client/data/best_server.json")

def select_best_server():
    """Выбор лучшего сервера"""
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        servers = json.load(f)
    
    # Приоритет: TLS > Reality с правильным SNI
    tls_servers = [s for s in servers if s.get('security') == 'tls' and s.get('is_working')]
    reality_servers = [s for s in servers 
                       if s.get('security') == 'reality' 
                       and s.get('is_working')
                       and s.get('sni') in ['www.speedtest.net', 'www.cloudflare.com', 'www.microsoft.com']]
    
    print(f"TLS серверов: {len(tls_servers)}")
    print(f"Reality серверов: {len(reality_servers)}")
    
    # Выбираем лучший TLS
    if tls_servers:
        best = min(tls_servers, key=lambda s: s.get('latency', 9999))
        print(f"\n✅ Лучший сервер: {best['host']}:{best['port']}")
        print(f"   Тип: TLS")
        print(f"   Страна: {best.get('country', '🌍')}")
        print(f"   Задержка: {best.get('latency', 'N/A')}ms")
        
        # Сохраняем
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(best, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Сохранено: {OUTPUT_FILE}")
        return best
    
    # Если нет TLS, берем Reality
    if reality_servers:
        best = reality_servers[0]
        print(f"\n✅ Лучший сервер: {best['host']}:{best['port']}")
        print(f"   Тип: Reality")
        print(f"   SNI: {best.get('sni', 'N/A')}")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(best, f, indent=2, ensure_ascii=False)
        
        return best
    
    print("❌ Нет рабочих серверов!")
    return None

if __name__ == "__main__":
    select_best_server()
