#!/usr/bin/env python3
"""
VLESS VPN Controller - Выбор локаций и автозапуск
Работает в фоне, управление через простое меню
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Пути
BASE_DIR = Path.home() / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CURRENT_SERVER_FILE = DATA_DIR / "current_server.json"
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"

# Создаем директории
for d in [DATA_DIR, LOGS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class VPNController:
    """Контроллер для управления VPN с выбором локаций"""
    
    def __init__(self):
        self.servers: List[Dict[str, Any]] = []
        self.blacklist: set = set()
        self.load_data()
    
    def load_data(self):
        """Загружает серверы и blacklist"""
        if SERVERS_FILE.exists():
            with open(SERVERS_FILE) as f:
                self.servers = json.load(f)
        
        if BLACKLIST_FILE.exists():
            with open(BLACKLIST_FILE) as f:
                self.blacklist = set(line.strip() for line in f if line.strip())
    
    def get_countries(self) -> Dict[str, List[Dict[str, Any]]]:
        """Группирует серверы по странам"""
        countries = {}
        
        for server in self.servers:
            if server.get("status") != "online":
                continue
            if server["host"] in self.blacklist:
                continue
            
            # Определяем страну из имени сервера
            name = server.get("name", "")
            host = server["host"]
            
            # Флаги и страны
            country_map = {
                "🇩🇪": "Germany", "🇩🇪 Germany": "Germany", "Germany": "Germany",
                "🇳🇱": "Netherlands", "🇳🇱 Netherlands": "Netherlands", "Netherlands": "Netherlands",
                "🇺🇸": "USA", "🇺🇸 USA": "USA", "USA": "USA", "United States": "USA",
                "🇬🇧": "UK", "🇬🇧 UK": "UK", "UK": "UK", "United Kingdom": "UK",
                "🇫🇷": "France", "🇫🇷 France": "France", "France": "France",
                "🇪🇪": "Estonia", "🇪🇪 Estonia": "Estonia", "Estonia": "Estonia",
                "🇧🇾": "Belarus", "🇧🇾 Belarus": "Belarus", "Belarus": "Belarus",
                "🇵🇱": "Poland", "🇵🇱 Poland": "Poland", "Poland": "Poland",
                "🇺🇦": "Ukraine", "🇺🇦 Ukraine": "Ukraine", "Ukraine": "Ukraine",
                "🇰🇿": "Kazakhstan", "🇰🇿 Kazakhstan": "Kazakhstan", "Kazakhstan": "Kazakhstan",
                "🇫🇮": "Finland", "🇫🇮 Finland": "Finland", "Finland": "Finland",
                "🇸🇪": "Sweden", "🇸🇪 Sweden": "Sweden", "Sweden": "Sweden",
                "🇳🇴": "Norway", "🇳🇴 Norway": "Norway", "Norway": "Norway",
                "🇱🇻": "Latvia", "🇱🇻 Latvia": "Latvia", "Latvia": "Latvia",
                "🇱🇹": "Lithuania", "🇱🇹 Lithuania": "Lithuania", "Lithuania": "Lithuania",
            }
            
            country = "🌍 Other"
            for flag, cname in country_map.items():
                if flag in name or cname in name:
                    country = f"{flag} {cname}"
                    break
            
            if country not in countries:
                countries[country] = []
            
            countries[country].append({
                "host": host,
                "port": server["port"],
                "latency": server.get("latency", 9999),
                "name": name[:50],
                "raw_url": server.get("raw_url", "")
            })
        
        # Сортируем страны по количеству серверов
        countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))
        
        # Сортируем серверы по задержке внутри страны
        for country in countries:
            countries[country].sort(key=lambda x: x["latency"])
        
        return countries
    
    def get_best_server(self, country: str = None) -> Dict[str, Any]:
        """Возвращает лучший сервер для страны"""
        countries = self.get_countries()
        
        if not countries:
            return None
        
        if country and country in countries:
            servers = countries[country]
            if servers:
                return servers[0]  # Лучший по задержке
        
        # Если страна не найдена, возвращаем лучший из всех
        all_servers = []
        for servers in countries.values():
            all_servers.extend(servers)
        
        if all_servers:
            all_servers.sort(key=lambda x: x["latency"])
            return all_servers[0]
        
        return None
    
    def list_countries(self):
        """Выводит список стран"""
        countries = self.get_countries()
        
        print("\n" + "=" * 60)
        print("🌍 ДОСТУПНЫЕ ЛОКАЦИИ")
        print("=" * 60)
        
        for i, (country, servers) in enumerate(countries.items(), 1):
            print(f"\n{i}. {country} ({len(servers)} серверов)")
            # Показываем топ-3 сервера
            for j, s in enumerate(servers[:3], 1):
                print(f"   {j}. {s['host']}:{s['port']} - {s['latency']} мс")
        
        print("\n" + "=" * 60)
        return countries
    
    def select_country(self, country_num: int) -> bool:
        """Выбирает страну и подключается"""
        countries = self.get_countries()
        country_names = list(countries.keys())
        
        if country_num < 1 or country_num > len(country_names):
            print("❌ Неверный номер страны")
            return False
        
        country = country_names[country_num - 1]
        server = self.get_best_server(country)
        
        if not server:
            print("❌ Нет доступных серверов")
            return False
        
        print(f"\n✅ Выбор локации: {country}")
        print(f"   Сервер: {server['host']}:{server['port']}")
        print(f"   Задержка: {server['latency']} мс")
        
        # Сохраняем выбор
        with open(CURRENT_SERVER_FILE, "w") as f:
            json.dump({
                "country": country,
                "server": server,
                "selected_at": datetime.now().isoformat()
            }, f, indent=2)
        
        # Добавляем в blacklist все серверы кроме выбранного
        self.blacklist.clear()
        for c, servers in countries.items():
            if c != country:
                for s in servers:
                    self.blacklist.add(s["host"])
        
        with open(BLACKLIST_FILE, "w") as f:
            f.write("\n".join(sorted(self.blacklist)))
        
        # Перезапускаем VPN
        self.restart_vpn()
        
        return True
    
    def auto_select(self):
        """Автоматический выбор лучшего сервера"""
        server = self.get_best_server()
        
        if not server:
            print("❌ Нет доступных серверов")
            return False
        
        print(f"\n✅ Автоматический выбор:")
        print(f"   Сервер: {server['host']}:{server['port']}")
        print(f"   Задержка: {server['latency']} мс")
        
        # Очищаем blacklist
        self.blacklist.clear()
        with open(BLACKLIST_FILE, "w") as f:
            f.write("")
        
        # Сохраняем выбор
        with open(CURRENT_SERVER_FILE, "w") as f:
            json.dump({
                "country": "Auto",
                "server": server,
                "selected_at": datetime.now().isoformat()
            }, f, indent=2)
        
        # Перезапускаем VPN
        self.restart_vpn()
        
        return True
    
    def restart_vpn(self):
        """Перезапускает VPN"""
        print("🔄 Перезапуск VPN...")
        
        # Останавливаем
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True)
        time.sleep(2)
        
        # Запускаем
        env = os.environ.copy()
        env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
        
        log_file = LOGS_DIR / "vpn-controller.log"
        with open(log_file, "w") as f:
            subprocess.Popen(
                [str(Path.home() / ".local" / "bin" / "vless-vpn"), "start", "--auto", "--mode", "split"],
                stdout=f,
                stderr=f,
                env=env
            )
        
        # Ждём подключения
        time.sleep(15)
        
        # Проверяем статус
        self.check_status()
    
    def check_status(self):
        """Проверяет статус подключения"""
        print("\n📊 Статус подключения:")
        
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    if "Подключен" in line or "VPN подключен" in line:
                        print(f"   ✅ {line.strip()}")
                        return
        
        print("   ⏳ Подключение...")
    
    def show_status(self):
        """Показывает текущий статус"""
        print("\n" + "=" * 60)
        print("📊 СТАТУС VPN")
        print("=" * 60)
        
        if CURRENT_SERVER_FILE.exists():
            with open(CURRENT_SERVER_FILE) as f:
                data = json.load(f)
                print(f"Локация: {data.get('country', 'N/A')}")
                print(f"Сервер: {data.get('server', {}).get('host', 'N/A')}")
                print(f"Выбрано: {data.get('selected_at', 'N/A')}")
        else:
            print("Локация не выбрана")
        
        countries = self.get_countries()
        print(f"\nВсего локаций: {len(countries)}")
        print(f"Всего серверов: {sum(len(s) for s in countries.values())}")
        print("=" * 60)


def show_menu():
    """Показывает меню"""
    controller = VPNController()
    
    while True:
        print("\n" + "=" * 60)
        print("🔒 VLESS VPN - МЕНЮ")
        print("=" * 60)
        print("1. 🌍 Выбрать локацию")
        print("2. ⚡ Автовыбор (лучший сервер)")
        print("3. 📊 Показать статус")
        print("4. 🔄 Обновить список серверов")
        print("5. ❌ Выход")
        print("=" * 60)
        
        choice = input("\nВаш выбор (1-5): ").strip()
        
        if choice == "1":
            countries = controller.list_countries()
            try:
                num = int(input("\nНомер локации: ").strip())
                if controller.select_country(num):
                    print("\n✅ Подключено!")
            except ValueError:
                print("❌ Введите число")
        
        elif choice == "2":
            controller.auto_select()
        
        elif choice == "3":
            controller.show_status()
        
        elif choice == "4":
            print("🔄 Обновление списка серверов...")
            env = os.environ.copy()
            env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
            subprocess.run([str(Path.home() / ".local" / "bin" / "vless-vpn"), "update"], env=env)
            controller.load_data()
            print("✅ Обновлено!")
        
        elif choice == "5":
            print("👋 Выход")
            break
        
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        controller = VPNController()
        
        if command == "status":
            controller.show_status()
        elif command == "auto":
            controller.auto_select()
        elif command == "menu":
            show_menu()
        else:
            print(f"Неизвестная команда: {command}")
            print("Используйте: status, auto, menu")
    else:
        show_menu()
