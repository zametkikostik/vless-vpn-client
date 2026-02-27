#!/usr/bin/env python3
"""
Fix VPN - Проверка и выбор рабочего сервера
"""

import json
import socket
import subprocess
from pathlib import Path
from datetime import datetime

SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "servers.json"
CONFIG_FILE = Path.home() / "vless-vpn-client" / "config" / "config.json"
XRAY_BIN = Path.home() / "vpn-client" / "bin" / "xray"

def test_server(host, port, timeout=3):
    """Проверка доступности сервера"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def generate_config(server):
    """Генерация конфига XRay"""
    stream = server.get('streamSettings', {})
    reality = stream.get('realitySettings', {})
    
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
    return config

def main():
    print("=" * 60)
    print("🔧 FIX VPN - Проверка и выбор рабочего сервера")
    print("=" * 60)
    
    # Загружаем серверы
    if not SERVERS_FILE.exists():
        print("❌ Файл серверов не найден!")
        print("Запустите: vless-vpn-ultimate update")
        return
    
    with open(SERVERS_FILE, 'r') as f:
        servers = json.load(f)
    
    print(f"✅ Загружено серверов: {len(servers)}")
    
    # Фильтруем reality серверы с UUID
    reality_servers = [
        s for s in servers
        if s.get('security') == 'reality'
        and s.get('uuid')
        and s.get('host')
    ]
    
    print(f"📊 Reality серверов: {len(reality_servers)}")
    
    # Тестируем первые 10 серверов
    print("\n🔍 Тестирование серверов...")
    working_servers = []
    
    for i, server in enumerate(reality_servers[:10]):
        host = server['host']
        port = server['port']
        print(f"  Проверка {i+1}/10: {host}:{port}...", end=" ")
        
        if test_server(host, port):
            print("✅")
            working_servers.append(server)
        else:
            print("❌")
    
    if not working_servers:
        print("\n❌ Нет доступных серверов!")
        print("Запустите: vless-vpn-ultimate update")
        return
    
    # Выбираем первый рабочий
    best_server = working_servers[0]
    print(f"\n✅ Выбран сервер: {best_server['host']}:{best_server['port']}")
    
    # Генерируем конфиг
    config = generate_config(best_server)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Конфиг создан: {CONFIG_FILE}")
    
    # Перезапускаем XRay
    print("\n🔄 Перезапуск XRay...")
    subprocess.run(["pkill", "-f", "xray"], capture_output=True)
    
    import time
    time.sleep(2)
    
    cmd = [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    # Проверяем работает ли
    result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
    if result.returncode == 0:
        print("✅ XRay запущен")
        print("\n" + "=" * 60)
        print("✅ VPN ГОТОВ К РАБОТЕ!")
        print("=" * 60)
        print("\nПрокси:")
        print("  SOCKS5: 127.0.0.1:10808")
        print("  HTTP: 127.0.0.1:10809")
        print("\nПроверьте:")
        print("  curl -x socks5h://127.0.0.1:10808 https://www.google.com")
    else:
        print("❌ XRay не запустился!")
        print("Проверьте логи:")
        print("  tail -50 ~/vless-vpn-client/logs/client.log")

if __name__ == "__main__":
    main()
