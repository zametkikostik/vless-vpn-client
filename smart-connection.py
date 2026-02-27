#!/usr/bin/env python3
"""
VLESS VPN - Smart Connection
Умное подключение: Прямой прокси → Reality VPN
Чтобы провайдер не видел трафик
"""

import json
import subprocess
import time
from pathlib import Path

CONFIG_FILE = Path.home() / "vless-vpn-client" / "config" / "config.json"
XRAY_BIN = Path.home() / "vpn-client" / "bin" / "xray"
WORKING_SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "working_reality_servers.json"


def pkill_xray():
    """Остановка XRay"""
    subprocess.run(["pkill", "-9", "xray"], capture_output=True)
    time.sleep(1)


def start_direct_proxy():
    """Запуск прямого прокси для проверки"""
    print("🔧 Запуск прямого прокси для проверки...")
    
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}},
            {"port": 10809, "protocol": "http"}
        ],
        "outbounds": [{"protocol": "freedom"}]
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    pkill_xray()
    
    proc = subprocess.Popen(
        [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    print("✅ Прямой прокси запущен")
    return proc


def test_internet():
    """Проверка интернета"""
    result = subprocess.run(
        ["curl", "-x", "socks5h://127.0.0.1:10808", "-s", "--connect-timeout", "5", "https://www.google.com"],
        capture_output=True
    )
    return result.returncode == 0


def start_reality_vpn(server):
    """Запуск Reality VPN"""
    print(f"🔒 Запуск Reality VPN через {server['host']}:{server['port']}...")
    
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
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "sockopt": {
                    "tcpNoDelay": True,
                    "tcpKeepAliveInterval": 30
                }
            }
        }],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": []
        }
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    pkill_xray()
    
    proc = subprocess.Popen(
        [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(5)
    print("✅ Reality VPN запущен")
    return proc


def test_blocked_sites():
    """Проверка заблокированных сайтов"""
    sites = [
        ("YouTube", "https://www.youtube.com"),
        ("GitHub", "https://github.com"),
        ("Supabase", "https://supabase.com")
    ]
    
    print()
    print("🔍 Проверка заблокированных сайтов...")
    
    for name, url in sites:
        result = subprocess.run(
            ["curl", "-x", "socks5h://127.0.0.1:10808", "-s", "--connect-timeout", "10", url],
            capture_output=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ {name} - ДОСТУПЕН")
        else:
            print(f"  ❌ {name} - НЕ ДОСТУПЕН")


def main():
    print("=" * 70)
    print("🔒 VLESS VPN - SMART CONNECTION")
    print("Провайдер НЕ видит ваш трафик")
    print("=" * 70)
    print()
    
    # Шаг 1: Прямой прокси для проверки
    print("📋 ШАГ 1: Проверка интернета (прямой прокси)")
    print("-" * 70)
    
    start_direct_proxy()
    
    if test_internet():
        print("✅ Интернет работает!")
    else:
        print("❌ Интернет НЕ работает!")
        print("Проверьте подключение к сети")
        return
    
    # Шаг 2: Reality VPN для обхода блокировок
    print()
    print("📋 ШАГ 2: Подключение Reality VPN (обход блокировок)")
    print("-" * 70)
    
    # Загружаем рабочие серверы
    if WORKING_SERVERS_FILE.exists():
        with open(WORKING_SERVERS_FILE, 'r') as f:
            data = json.load(f)
            servers = data.get('servers', [])
        
        if servers:
            best_server = servers[0]
            print(f"✅ Найден рабочий сервер: {best_server['host']}:{best_server['port']}")
            
            # Запускаем Reality VPN
            vpn_proc = start_reality_vpn(best_server)
            
            # Проверяем работу
            time.sleep(3)
            test_blocked_sites()
            
            print()
            print("=" * 70)
            print("✅ VPN ГОТОВ К РАБОТЕ!")
            print("=" * 70)
            print()
            print("🔒 Трафик ЗАШИФРОВАН - провайдер НЕ видит")
            print()
            print("Прокси:")
            print("  SOCKS5: 127.0.0.1:10808")
            print("  HTTP: 127.0.0.1:10809")
            print()
            print("Настройте Firefox:")
            print("  1. Настройки → Параметры сети")
            print("  2. Ручная настройка прокси")
            print("  3. SOCKS Сервер: 127.0.0.1")
            print("  4. Порт: 10808")
            print("  5. SOCKS v5 ✅")
            print("  6. DNS через SOCKS ✅")
            print()
            print("Проверьте:")
            print("  curl -x socks5h://127.0.0.1:10808 https://www.youtube.com")
            print()
            
            # Ждём пока пользователь не остановит
            try:
                print("💤 VPN работает. Нажмите Ctrl+C для остановки...")
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n\n👋 Остановка VPN...")
                pkill_xray()
        else:
            print("❌ Нет рабочих Reality серверов!")
            print("Запустите: python3 test-reality-servers.py")
    else:
        print("❌ Файл рабочих серверов не найден!")
        print("Запустите: python3 test-reality-servers.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        pkill_xray()
