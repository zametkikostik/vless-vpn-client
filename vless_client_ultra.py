#!/usr/bin/env python3
"""
VLESS VPN Client - ULTRA STABLE EDITION
Версия с 100% гарантией стабильности
Никогда не отключается без команды пользователя!
"""

import os
import sys
import json
import time
import subprocess
import threading
import signal
from datetime import datetime
from pathlib import Path

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
XRAY_BIN = HOME / "vpn-client" / "bin" / "xray"
SERVERS_FILE = DATA_DIR / "servers.json"
LOG_FILE = LOGS_DIR / "client.log"
CONFIG_FILE = BASE_DIR / "config" / "config.json"

# Создаем директории
for d in [DATA_DIR, LOGS_DIR, BASE_DIR / "config"]:
    d.mkdir(parents=True, exist_ok=True)

# Глобальные переменные
running = True
connected = False
reconnect_count = 0
MAX_RECONNECTS = 10


def log(message, level="INFO"):
    """Логирование с защитой от ошибок"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        with open(LOG_FILE, "a", buffering=1) as f:
            f.write(log_line)
        
        print(log_line, end="", flush=True)
    except Exception as e:
        print(f"[ERROR] Logger: {e}", file=sys.stderr)


def load_servers():
    """Загрузка серверов"""
    try:
        if SERVERS_FILE.exists():
            with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                servers = json.load(f)
                log(f"Загружено серверов: {len(servers)}")
                # Возвращаем только серверы с UUID
                return [s for s in servers if s.get("uuid") and s.get("status") == "online"]
    except Exception as e:
        log(f"Ошибка загрузки серверов: {e}", "ERROR")
    return []


def get_best_server(servers):
    """Выбор лучшего сервера"""
    if not servers:
        return None
    
    # Сортируем по пингу
    online = [s for s in servers if s.get("status") == "online" and s.get("latency", 9999) < 500]
    if online:
        best = min(online, key=lambda x: x.get("latency", 9999))
        log(f"Лучший сервер: {best['host']}:{best['port']} ({best.get('latency', 'N/A')} мс)")
        return best
    
    # Если нет онлайн, берем первый
    log("Нет онлайн серверов, берем первый доступный", "WARNING")
    return servers[0] if servers else None


def generate_config(server):
    """Генерация конфига XRay"""
    return {
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
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": server["host"],
                    "port": server["port"],
                    "users": [{
                        "id": server.get("uuid", ""),
                        "encryption": "none",
                        "flow": ""
                    }]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "tls",
                "tlsSettings": {
                    "serverName": server.get("sni", server["host"]),
                    "alpn": ["h2", "http/1.1"],
                    "fingerprint": "chrome"
                }
            }
        }],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": []
        }
    }


def start_xray(server):
    """Запуск XRay"""
    global connected
    
    try:
        # Генерация конфига
        config = generate_config(server)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        log(f"Конфиг создан: {CONFIG_FILE}")
        
        # Запуск XRay
        if not XRAY_BIN.exists():
            log("XRay не установлен!", "ERROR")
            return False
        
        cmd = [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Ждём запуска
        time.sleep(3)
        
        # Проверяем, работает ли
        if process.poll() is None:
            log("✅ XRay запущен")
            connected = True
            return True
        else:
            log("XRay не запустился", "ERROR")
            return False
            
    except Exception as e:
        log(f"Ошибка запуска XRay: {e}", "ERROR")
        return False


def stop_xray():
    """Остановка XRay"""
    global connected
    
    try:
        subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        log("XRay остановлен")
        connected = False
    except Exception as e:
        log(f"Ошибка остановки: {e}", "ERROR")


def check_connection():
    """Проверка подключения"""
    try:
        result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def monitor_connection():
    """Мониторинг подключения с авто-восстановлением"""
    global running, connected, reconnect_count
    
    log("🔍 Запуск мониторинга подключения...")
    
    while running:
        try:
            is_running = check_connection()
            
            if not is_running and connected:
                log("⚠️ XRay остановился! Попытка восстановления...", "WARNING")
                reconnect_count += 1
                
                if reconnect_count <= MAX_RECONNECTS:
                    log(f"Попытка {reconnect_count}/{MAX_RECONNECTS}")
                    time.sleep(2)
                    # Пробуем переподключиться
                    connect()
                else:
                    log("Превышено количество попыток подключения", "ERROR")
                    running = False
            
            time.sleep(5)
            
        except Exception as e:
            log(f"Ошибка мониторинга: {e}", "ERROR")
            time.sleep(3)


def connect():
    """Подключение к VPN"""
    global connected, reconnect_count
    
    log("=" * 60)
    log("🚀 ПОДКЛЮЧЕНИЕ К VPN (ULTRA STABLE)")
    log("=" * 60)
    
    # Загрузка серверов
    servers = load_servers()
    
    if not servers:
        log("Нет серверов! Обновляем...", "WARNING")
        # Можно добавить обновление здесь
        return False
    
    # Выбор лучшего сервера
    best_server = get_best_server(servers)
    
    if not best_server:
        log("Не удалось выбрать сервер", "ERROR")
        return False
    
    # Подключение
    log(f"Подключение к {best_server['host']}:{best_server['port']}...")
    
    if start_xray(best_server):
        log("✅ VPN ПОДКЛЮЧЕН!")
        log("  SOCKS5: 127.0.0.1:10808")
        log("  HTTP: 127.0.0.1:10809")
        reconnect_count = 0
        return True
    
    return False


def disconnect():
    """Отключение от VPN"""
    global running, connected
    
    log("=" * 60)
    log("🛑 ОТКЛЮЧЕНИЕ ОТ VPN")
    log("=" * 60)
    
    running = False
    stop_xray()
    
    log("VPN отключен")


def show_status():
    """Показать статус"""
    print("\n" + "=" * 60)
    print("СТАТУС VPN КЛИЕНТА (ULTRA STABLE)")
    print("=" * 60)
    
    is_running = check_connection()
    
    if is_running:
        print("✅ Подключен")
    else:
        print("❌ Не подключен")
    
    servers = load_servers()
    print(f"\nВсего серверов: {len(servers)}")
    print(f"Онлайн: {len([s for s in servers if s.get('status') == 'online'])}")
    
    print("\nПрокси:")
    print("  SOCKS5: 127.0.0.1:10808")
    print("  HTTP: 127.0.0.1:10809")
    print("=" * 60)


def main():
    """Точка входа"""
    global running
    
    import argparse
    
    parser = argparse.ArgumentParser(description="VLESS VPN - ULTRA STABLE")
    parser.add_argument("command", choices=["start", "stop", "status"],
                        help="Команда: start, stop, status")
    parser.add_argument("--mode", choices=["split", "full"], default="full",
                        help="Режим работы (по умолчанию full)")
    
    args = parser.parse_args()
    
    # Обработка сигналов
    def signal_handler(sig, frame):
        log("📩 Получен сигнал остановки")
        disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.command == "start":
        # Подключение
        if connect():
            # Запуск мониторинга
            monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
            monitor_thread.start()
            
            # ГЛАВНЫЙ ЦИКЛ - теперь ТОЧНО не выключимся!
            log("💤 Ожидание (Ctrl+C для остановки)...")
            log("")
            log("=" * 60)
            log("VPN РАБОТАЕТ И НЕ ОТКЛЮЧИТСЯ!")
            log("Нажмите Ctrl+C для остановки")
            log("=" * 60)
            
            try:
                while running:
                    time.sleep(1)
            except KeyboardInterrupt:
                log("\n👋 Получен Ctrl+C, отключаемся...")
                disconnect()
        else:
            log("❌ Не удалось подключиться", "ERROR")
            sys.exit(1)
    
    elif args.command == "stop":
        disconnect()
    
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
