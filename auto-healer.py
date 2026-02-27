#!/usr/bin/env python3
"""
VLESS VPN - Auto Healer
Автоматически находит и переключается на рабочие серверы
"""

import json
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "servers.json"
CONFIG_FILE = Path.home() / "vless-vpn-client" / "config" / "config.json"
XRAY_BIN = Path.home() / "vpn-client" / "bin" / "xray"
WORKING_SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "working_reality_servers.json"
LOG_FILE = Path.home() / "vless-vpn-client" / "logs" / "auto-heal.log"

xray_process = None
current_server = None


def log(message):
    """Логирование"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')


def pkill_xray():
    """Остановка XRay"""
    global xray_process
    subprocess.run(["pkill", "-9", "xray"], capture_output=True)
    if xray_process:
        try:
            xray_process.terminate()
        except:
            pass
    xray_process = None
    time.sleep(2)


def test_server_quick(server):
    """Быстрый тест сервера"""
    stream = server.get('streamSettings', {})
    reality = stream.get('realitySettings', {})
    
    config = {
        "log": {"loglevel": "error"},
        "inbounds": [{"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}}],
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
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    proc = subprocess.Popen(
        [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    
    # Проверка
    result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
    if result.returncode != 0:
        proc.terminate()
        return False
    
    # Тест интернета
    test = subprocess.run(
        ["curl", "-x", "socks5h://127.0.0.1:10808", "-s", "--connect-timeout", "5", "https://www.google.com"],
        capture_output=True,
        timeout=10
    )
    
    proc.terminate()
    time.sleep(1)
    
    return test.returncode == 0


def find_working_server():
    """Поиск рабочего сервера"""
    log("🔍 Поиск рабочего сервера...")
    
    if not SERVERS_FILE.exists():
        log("❌ Файл серверов не найден!")
        return None
    
    with open(SERVERS_FILE, 'r') as f:
        servers = json.load(f)
    
    reality_servers = [s for s in servers if s.get('security') == 'reality' and s.get('uuid')]
    log(f"📊 Reality серверов: {len(reality_servers)}")
    
    # Тестируем первые 30
    for i, server in enumerate(reality_servers[:30]):
        log(f"  [{i+1}/30] {server['host']}:{server['port']}...", end=" ")
        
        if test_server_quick(server):
            log("✅ РАБОТАЕТ")
            return server
        else:
            log("❌")
    
    return None


def start_vpn(server):
    """Запуск VPN"""
    global xray_process, current_server
    
    stream = server.get('streamSettings', {})
    reality = stream.get('realitySettings', {})
    
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
                    "address": server["host"],
                    "port": server["port"],
                    "users": [{"id": server.get("uuid", ""), "encryption": "none", "flow": "xtls-rprx-vision"}]
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
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    pkill_xray()
    
    xray_process = subprocess.Popen(
        [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    current_server = server
    time.sleep(5)
    
    log(f"✅ VPN запущен на {server['host']}:{server['port']}")


def check_connection():
    """Проверка подключения"""
    result = subprocess.run(
        ["curl", "-x", "socks5h://127.0.0.1:10808", "-s", "--connect-timeout", "5", "https://www.google.com"],
        capture_output=True
    )
    return result.returncode == 0


def main():
    log("=" * 70)
    log("🔒 VLESS VPN - AUTO HEALER")
    log("Автоматический поиск и переключение на рабочие серверы")
    log("=" * 70)
    
    while True:
        try:
            # Проверка подключения
            if current_server and check_connection():
                log(f"✅ VPN работает ({current_server['host']}:{current_server['port']})")
            else:
                log("❌ VPN НЕ работает")
                log("🔍 Поиск нового сервера...")
                
                server = find_working_server()
                
                if server:
                    start_vpn(server)
                    
                    # Сохранение
                    if check_connection():
                        with open(WORKING_SERVERS_FILE, 'w') as f:
                            json.dump({
                                'updated_at': datetime.now().isoformat(),
                                'servers': [server]
                            }, f, indent=2, ensure_ascii=False)
                        log(f"💾 Сохранён рабочий сервер: {server['host']}:{server['port']}")
                    else:
                        log("❌ Не удалось подключиться")
                else:
                    log("❌ Нет рабочих серверов!")
            
            # Ждём 5 минут
            time.sleep(300)
            
        except KeyboardInterrupt:
            log("\n👋 Остановка...")
            pkill_xray()
            sys.exit(0)
        except Exception as e:
            log(f"❌ Ошибка: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
