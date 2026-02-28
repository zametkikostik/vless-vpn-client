#!/usr/bin/env python3
"""Поиск рабочего HTTPS сервера"""

import json
import subprocess
import time
from pathlib import Path

DATA_FILE = Path("/home/kostik/vless-vpn-client/data/servers.json")
CONFIG_FILE = Path("/home/kostik/vless-vpn-client/config/config.json")

def test_https_server(server: dict) -> bool:
    """Тест HTTPS подключения"""
    security = server.get('security', 'tls')
    
    # Создаем конфиг
    config = {
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
                "security": security,
                "sockopt": {"tcpNoDelay": True}
            }
        }]
    }
    
    # Добавляем TLS/Reality настройки
    if security == "tls":
        config["outbounds"][0]["streamSettings"]["tlsSettings"] = {
            "serverName": server.get("sni", "www.google.com"),
            "fingerprint": "chrome"
        }
    elif security == "reality":
        config["outbounds"][0]["streamSettings"]["realitySettings"] = {
            "dest": server.get("sni", "www.speedtest.net") + ":443",
            "serverNames": [server.get("sni", "www.speedtest.net")],
            "fingerprint": "chrome",
            "publicKey": server.get("pbk", ""),
            "shortId": server.get("sid", ""),
            "spiderX": "/"
        }
    
    # Сохраняем
    test_file = Path("/tmp/test-https.json")
    with open(test_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Запускаем XRay
    try:
        proc = subprocess.Popen(
            ["/home/kostik/vpn-client/bin/xray", "run", "-c", str(test_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(4)
        
        # Тест HTTPS
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "--socks5", "127.0.0.1:10808", "https://www.google.com"],
            capture_output=True,
            timeout=7
        )
        
        proc.terminate()
        proc.wait(timeout=2)
        
        if result.returncode == 0 and len(result.stdout) > 100:
            return True
        return False
    except:
        try:
            proc.terminate()
        except:
            pass
        return False

def find_working_https():
    """Поиск рабочего HTTPS сервера"""
    with open(DATA_FILE, 'r') as f:
        servers = json.load(f)
    
    # Reality серверы с правильным SNI
    reality_servers = [s for s in servers 
                       if s.get('security') == 'reality'
                       and s.get('is_working')
                       and s.get('sni') in ['www.speedtest.net', 'www.cloudflare.com', 'www.microsoft.com']
                       and s.get('latency', 9999) < 30]
    
    reality_servers.sort(key=lambda x: x.get('latency', 9999))
    
    print(f"📊 Найдено Reality серверов: {len(reality_servers)}")
    print("🔍 Тестируем HTTPS подключение...\n")
    
    for i, server in enumerate(reality_servers[:15]):
        print(f"{i+1}. {server['host']}:{server['port']} - {server.get('sni')} - {server.get('latency')}ms")
        
        if test_https_server(server):
            print(f"   ✅ РАБОТАЕТ HTTPS!\n")
            
            # Сохраняем рабочий сервер
            with open("/home/kostik/vless-vpn-client/data/working_server.json", 'w') as f:
                json.dump(server, f, indent=2, ensure_ascii=False)
            
            return server
        else:
            print(f"   ❌ Не работает\n")
    
    print("❌ Нет рабочих HTTPS серверов!")
    return None

if __name__ == "__main__":
    server = find_working_https()
    if server:
        print(f"💾 Сохранено: working_server.json")
        print(f"📡 Сервер: {server['host']}:{server['port']}")
