#!/usr/bin/env python3
"""
Автоматический выбор и проверка рабочих серверов
"""

import json
import subprocess
import time
from pathlib import Path

DATA_FILE = Path("/home/kostik/vless-vpn-client/data/servers.json")
CONFIG_FILE = Path("/home/kostik/vless-vpn-client/config/config.json")
TESTED_FILE = Path("/home/kostik/vless-vpn-client/data/tested_servers.json")

def test_server_connection(server: dict) -> bool:
    """Проверка сервера подключением"""
    # Создаем тестовый конфиг
    test_config = {
        "log": {"level": "error"},
        "inbounds": [
            {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}}
        ],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": server["host"],
                    "port": server["port"],
                    "users": [{"id": server.get("uuid", ""), "encryption": "none", "flow": "xtls-rprx-vision"}]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": server.get("security", "tls"),
                "tlsSettings": {
                    "serverName": server.get("sni", "www.google.com"),
                    "fingerprint": "chrome"
                } if server.get("security") == "tls" else None,
                "sockopt": {"tcpNoDelay": True}
            }
        }]
    }
    
    # Удаляем None поля
    if test_config["outbounds"][0]["streamSettings"]["tlsSettings"] is None:
        del test_config["outbounds"][0]["streamSettings"]["tlsSettings"]
    
    # Сохраняем тестовый конфиг
    test_file = Path("/tmp/test-xray-config.json")
    with open(test_file, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    # Запускаем XRay на 5 секунд
    try:
        proc = subprocess.Popen(
            ["/home/kostik/vpn-client/bin/xray", "run", "-c", str(test_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        
        # Проверяем HTTP запрос
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "3", "--socks5", "127.0.0.1:10808", "http://example.com"],
                capture_output=True,
                timeout=5
            )
            proc.terminate()
            
            if result.returncode == 0 and len(result.stdout) > 0:
                return True
        except:
            pass
        
        proc.terminate()
        return False
    except:
        return False

def find_working_server():
    """Поиск работающего сервера"""
    with open(DATA_FILE, 'r') as f:
        servers = json.load(f)
    
    # TLS серверы с низкой задержкой
    tls_servers = [s for s in servers 
                   if s.get('security') == 'tls' 
                   and s.get('is_working')
                   and s.get('latency', 9999) < 50]
    
    tls_servers.sort(key=lambda x: x.get('latency', 9999))
    
    print(f"📊 Найдено TLS серверов: {len(tls_servers)}")
    
    working_servers = []
    
    for i, server in enumerate(tls_servers[:10]):  # Тестируем первые 10
        print(f"\n🔍 Тест {i+1}/10: {server['host']}:{server['port']}")
        
        if test_server_connection(server):
            print(f"✅ РАБОТАЕТ!")
            working_servers.append(server)
        else:
            print(f"❌ Не работает")
        
        if len(working_servers) >= 3:  # Нашли 3 рабочих
            break
    
    if working_servers:
        # Выбираем лучший
        best = working_servers[0]
        print(f"\n✅ Лучший сервер: {best['host']}:{best['port']}")
        
        # Сохраняем
        with open(TESTED_FILE, 'w') as f:
            json.dump(best, f, indent=2, ensure_ascii=False)
        
        return best
    
    print("❌ Нет рабочих серверов!")
    return None

if __name__ == "__main__":
    server = find_working_server()
    if server:
        print(f"\n💾 Сохранено: {TESTED_FILE}")
