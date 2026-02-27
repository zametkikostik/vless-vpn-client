#!/usr/bin/env python3
"""
Reality Server Tester - Поиск рабочих Reality серверов
"""

import json
import subprocess
import time
from pathlib import Path

SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "servers.json"
CONFIG_FILE = Path.home() / "vless-vpn-client" / "config" / "config.json"
XRAY_BIN = Path.home() / "vpn-client" / "bin" / "xray"
WORKING_SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "working_reality_servers.json"


def test_server(server):
    """Тестирование сервера"""
    # Создаём конфиг
    stream = server.get('streamSettings', {})
    reality = stream.get('realitySettings', {})
    
    config = {
        "log": {"loglevel": "error"},
        "inbounds": [
            {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}}
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
    
    # Сохраняем конфиг
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Запускаем XRay
    pkill_xray()
    time.sleep(1)
    
    proc = subprocess.Popen(
        [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    
    # Проверяем работает ли
    result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
    
    if result.returncode != 0:
        proc.terminate()
        return False
    
    # Проверяем интернет
    test_result = subprocess.run(
        ["curl", "-x", "socks5h://127.0.0.1:10808", "-s", "--connect-timeout", "5", "https://www.google.com"],
        capture_output=True,
        timeout=10
    )
    
    proc.terminate()
    time.sleep(1)
    
    return test_result.returncode == 0


def pkill_xray():
    """Остановка XRay"""
    subprocess.run(["pkill", "-9", "xray"], capture_output=True)


def main():
    print("=" * 70)
    print("🔍 ТЕСТирование Reality СЕРВЕРОВ")
    print("=" * 70)
    print()
    
    # Загружаем серверы
    if not SERVERS_FILE.exists():
        print("❌ Файл серверов не найден!")
        print("Запустите: vless-vpn-ultimate update")
        return
    
    with open(SERVERS_FILE, 'r') as f:
        servers = json.load(f)
    
    # Фильтруем reality
    reality_servers = [
        s for s in servers
        if s.get('security') == 'reality'
        and s.get('uuid')
        and s.get('host')
    ]
    
    print(f"📊 Reality серверов: {len(reality_servers)}")
    print()
    
    # Тестируем первые 20
    print("🔍 Тестирование первых 20 серверов...")
    print("⏳ Это займёт несколько минут...")
    print()
    
    working_servers = []
    
    for i, server in enumerate(reality_servers[:20]):
        print(f"  [{i+1}/20] {server['host']}:{server['port']}...", end=" ")
        
        if test_server(server):
            print("✅ РАБОТАЕТ")
            working_servers.append(server)
        else:
            print("❌ НЕ РАБОТАЕТ")
    
    print()
    print("=" * 70)
    print(f"✅ Найдено {len(working_servers)} рабочих серверов")
    print("=" * 70)
    
    if working_servers:
        # Сохраняем
        with open(WORKING_SERVERS_FILE, 'w') as f:
            json.dump({
                'tested_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tested': 20,
                'working_count': len(working_servers),
                'servers': working_servers
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Сохранено в: {WORKING_SERVERS_FILE}")
        print()
        
        # Запускаем лучший сервер
        best = working_servers[0]
        print(f"🔌 Подключение к лучшему серверу: {best['host']}:{best['port']}")
        
        # Создаём финальный конфиг
        stream = best.get('streamSettings', {})
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
                        "address": best["host"],
                        "port": best["port"],
                        "users": [{
                            "id": best.get("uuid", ""),
                            "encryption": "none",
                            "flow": "xtls-rprx-vision"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "serverName": reality.get("serverName", best["host"]),
                        "fingerprint": "chrome",
                        "publicKey": reality.get("publicKey", ""),
                        "shortId": reality.get("shortId", "")
                    }
                }
            }]
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Запускаем XRay
        pkill_xray()
        time.sleep(1)
        
        subprocess.Popen(
            [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(3)
        
        print()
        print("=" * 70)
        print("✅ VPN ЗАПУЩЕН С РАБОЧИМ СЕРВЕРОМ!")
        print("=" * 70)
        print()
        print("Прокси:")
        print("  SOCKS5: 127.0.0.1:10808")
        print("  HTTP: 127.0.0.1:10809")
        print()
        print("Проверьте:")
        print("  curl -x socks5h://127.0.0.1:10808 https://www.youtube.com")
        print()
    else:
        print()
        print("❌ Ни один сервер не работает!")
        print("Используйте прямой прокси:")
        print("  ./start-direct-proxy.sh")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем")
        pkill_xray()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        pkill_xray()
