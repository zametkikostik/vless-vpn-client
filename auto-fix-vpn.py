#!/usr/bin/env python3
"""
Автоматическая проверка и замена нерабочих серверов
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

DATA_FILE = Path("/home/kostik/vless-vpn-client/data/servers.json")
CONFIG_FILE = Path("/home/kostik/vless-vpn-client/config/config.json")
LOG_FILE = Path("/home/kostik/vless-vpn-client/logs/auto-fix.log")

# Тестовые URL для проверки
TEST_URLS = [
    "https://www.cloudflare.com",
    "https://www.google.com",
    "https://api.ipify.org?format=text"
]

def log(message):
    """Логирование"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    print(log_line, end="")
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def test_server(server: dict) -> bool:
    """Проверка сервера на работоспособность"""
    host = server.get('host', '')
    port = server.get('port', 0)
    
    # Проверяем доступность порта
    try:
        result = subprocess.run(
            ['timeout', '3', 'bash', '-c', f'echo > /dev/tcp/{host}/{port}'],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            return False
    except:
        return False
    
    # Для TLS серверов - простая проверка
    if server.get('security') == 'tls':
        return True
    
    # Для Reality - нужна дополнительная проверка
    return True

def get_working_server() -> dict:
    """Получить рабочий сервер"""
    if not DATA_FILE.exists():
        log("❌ Файл серверов не найден")
        return None
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        servers = json.load(f)
    
    # Приоритет: TLS > Reality
    tls_servers = [s for s in servers 
                   if s.get('security') == 'tls' 
                   and s.get('is_working')
                   and s.get('latency', 9999) < 100]
    
    if tls_servers:
        # Сортируем по задержке
        tls_servers.sort(key=lambda x: x.get('latency', 9999))
        log(f"✅ Найдено TLS серверов: {len(tls_servers)}")
        return tls_servers[0]
    
    # Если нет TLS, берем Reality с правильным SNI
    reality_servers = [s for s in servers 
                       if s.get('security') == 'reality'
                       and s.get('is_working')
                       and s.get('sni') in ['www.speedtest.net', 'www.cloudflare.com', 'www.microsoft.com']]
    
    if reality_servers:
        log(f"✅ Найдено Reality серверов: {len(reality_servers)}")
        return reality_servers[0]
    
    log("❌ Нет рабочих серверов!")
    return None

def generate_config(server: dict) -> dict:
    """Генерация конфигурации XRay"""
    security = server.get('security', 'tls')
    
    config = {
        "log": {
            "level": "warning"
        },
        "inbounds": [
            {
                "port": 10808,
                "protocol": "socks",
                "settings": {
                    "auth": "noauth",
                    "udp": True,
                    "ip": "127.0.0.1"
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            },
            {
                "port": 10809,
                "protocol": "http",
                "settings": {
                    "allowTransparent": False
                }
            }
        ],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": server['host'],
                            "port": server['port'],
                            "users": [
                                {
                                    "id": server.get('uuid', server.get('id', '')),
                                    "encryption": "none",
                                    "flow": server.get('flow', 'xtls-rprx-vision')
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": security,
                    "sockopt": {
                        "tcpNoDelay": True,
                        "tcpKeepAliveInterval": 30
                    }
                }
            }
        ],
        "fragment": {
            "packets": "tlshello",
            "length": "50-200",
            "interval": "10-50"
        }
    }
    
    # Добавляем TLS настройки
    if security == 'tls':
        config["outbounds"][0]["streamSettings"]["tlsSettings"] = {
            "allowInsecure": False,
            "fingerprint": "chrome",
            "alpn": ["h2", "http/1.1"],
            "serverName": server.get('sni', server.get('serverName', 'www.google.com'))
        }
    elif security == 'reality':
        config["outbounds"][0]["streamSettings"]["realitySettings"] = {
            "show": False,
            "dest": server.get('sni', 'www.speedtest.net') + ":443",
            "serverNames": [server.get('sni', 'www.speedtest.net')],
            "fingerprint": "chrome",
            "publicKey": server.get('pbk', server.get('publicKey', '')),
            "shortId": server.get('sid', server.get('shortId', '')),
            "spiderX": "/"
        }
    
    return config

def auto_fix():
    """Автоматическое исправление"""
    log("=" * 60)
    log("🔧 Автоматическое исправление VPN")
    log("=" * 60)
    
    # Получаем рабочий сервер
    server = get_working_server()
    if not server:
        log("❌ Не удалось получить рабочий сервер")
        return False
    
    log(f"📡 Выбран сервер: {server['host']}:{server['port']}")
    log(f"   Тип: {server.get('security', 'tls')}")
    log(f"   Страна: {server.get('country', '🌍')}")
    
    # Генерируем конфигурацию
    config = generate_config(server)
    
    # Сохраняем
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    log(f"✅ Конфигурация сохранена: {CONFIG_FILE}")
    
    # Перезапускаем VPN
    log("🔄 Перезапуск VPN...")
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'vless-vpn-ultimate'], 
                      capture_output=True, timeout=10)
        time.sleep(8)
        
        # Проверяем статус
        result = subprocess.run(['systemctl', 'is-active', 'vless-vpn-ultimate'],
                               capture_output=True, text=True, timeout=5)
        
        if result.stdout.strip() == 'active':
            log("✅ VPN перезапущен и активен")
            return True
        else:
            log("❌ VPN не активен")
            return False
    except Exception as e:
        log(f"❌ Ошибка перезапуска: {e}")
        return False

def test_connection() -> bool:
    """Проверка подключения"""
    log("🔍 Проверка подключения...")
    
    try:
        import requests
        session = requests.Session()
        session.proxies = {
            'http': 'socks5://127.0.0.1:10808',
            'https': 'socks5://127.0.0.1:10808'
        }
        
        # Пробуем HTTP (проще)
        r = session.get('http://example.com', timeout=10)
        if r.status_code == 200:
            log("✅ HTTP работает!")
            return True
        
        # Пробуем HTTPS
        r = session.get('https://api.ipify.org?format=text', timeout=10)
        if r.status_code == 200:
            log(f"✅ HTTPS работает! IP: {r.text.strip()}")
            return True
            
    except Exception as e:
        log(f"❌ Ошибка подключения: {str(e)[:60]}")
    
    return False

if __name__ == "__main__":
    # Автоматическое исправление
    if auto_fix():
        # Проверка подключения
        if test_connection():
            log("\n✅ ВСЁ РАБОТАЕТ!")
        else:
            log("\n⚠️ VPN запущен, но есть проблемы с подключением")
            log("   Попробуйте другой сервер или проверьте сеть")
    else:
        log("\n❌ Не удалось исправить автоматически")
        log("   Проверьте логи и попробуйте вручную")
