#!/usr/bin/env python3
"""
DeVPN Integration - Децентрализованные VPN сети
Поддержка Sentinel dVPN, Orchid, Mysterium
"""

import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Пути
HOME = Path.home()
DATA_DIR = HOME / "vpn-client" / "data"
DVPN_DIR = DATA_DIR / "dvpn"
DVPN_DIR.mkdir(parents=True, exist_ok=True)

# API публичных dVPN сетей
SENTINEL_API = "https://rest.sentinel.co"
MYSTERIUM_API = "https://api.mysterium.network/v1"

class DeVPNManager:
    """Менеджер децентрализованных VPN"""
    
    def __init__(self):
        self.dvpn_servers = []
        self.cache_file = DVPN_DIR / "dvpn_servers.json"
        
    def fetch_sentinel_nodes(self):
        """Получить узлы Sentinel dVPN"""
        try:
            print("📡 Запрос к Sentinel dVPN...")
            # Публичные ноды Sentinel (бесплатный tier)
            response = requests.get(
                f"{SENTINEL_API}/providers",
                params={"status": "active", "limit": 50},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                nodes = []
                for provider in data.get('providers', []):
                    if provider.get('free', False):  # Только бесплатные
                        nodes.append({
                            'network': 'Sentinel',
                            'address': provider.get('address'),
                            'country': provider.get('location', {}).get('country', 'Unknown'),
                            'city': provider.get('location', {}).get('city', 'Unknown'),
                            'bandwidth': provider.get('bandwidth', {}),
                            'price': 'FREE',
                            'latency': 9999
                        })
                print(f"✅ Найдено {len(nodes)} бесплатных узлов Sentinel")
                return nodes
        except Exception as e:
            print(f"⚠️ Ошибка Sentinel: {e}")
        return []
    
    def fetch_mysterium_nodes(self):
        """Получить узлы Mysterium Network"""
        try:
            print("📡 Запрос к Mysterium Network...")
            response = requests.get(
                f"{MYSTERIUM_API}/proposals",
                params={"access_policy": "open"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                nodes = []
                for proposal in data.get('proposals', [])[:50]:  # Первые 50
                    nodes.append({
                        'network': 'Mysterium',
                        'address': proposal.get('provider_id'),
                        'country': proposal.get('location', {}).get('country', 'Unknown'),
                        'city': proposal.get('location', {}).get('city', 'Unknown'),
                        'type': proposal.get('service_type'),
                        'price': 'FREE',
                        'latency': 9999
                    })
                print(f"✅ Найдено {len(nodes)} узлов Mysterium")
                return nodes
        except Exception as e:
            print(f"⚠️ Ошибка Mysterium: {e}")
        return []
    
    def fetch_all_dvpn(self):
        """Получить все dVPN узлы"""
        print("\n🌐 Поиск децентрализованных VPN узлов...")
        print("=" * 60)
        
        self.dvpn_servers = []
        
        # Sentinel
        sentinel = self.fetch_sentinel_nodes()
        self.dvpn_servers.extend(sentinel)
        
        # Mysterium
        mysterium = self.fetch_mysterium_nodes()
        self.dvpn_servers.extend(mysterium)
        
        # Кэширование
        self.save_cache()
        
        print("=" * 60)
        print(f"📊 Всего найдено dVPN узлов: {len(self.dvpn_servers)}")
        return self.dvpn_servers
    
    def save_cache(self):
        """Сохранить кэш"""
        with open(self.cache_file, 'w') as f:
            json.dump({
                'servers': self.dvpn_servers,
                'updated': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
    
    def load_cache(self):
        """Загрузить из кэша"""
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                data = json.load(f)
                self.dvpn_servers = data.get('servers', [])
                print(f"✅ Загружено {len(self.dvpn_servers)} узлов из кэша")
                return self.dvpn_servers
        return []
    
    def list_nodes(self, network=None):
        """Показать список узлов"""
        if not self.dvpn_servers:
            self.load_cache()
        
        if network:
            nodes = [n for n in self.dvpn_servers if n['network'] == network]
        else:
            nodes = self.dvpn_servers
        
        print(f"\n📋 Список dVPN узлов ({len(nodes)}):")
        print("=" * 80)
        print(f"{'Сеть':<12} {'Страна':<20} {'Город':<20} {'Тип':<15}")
        print("=" * 80)
        
        for node in nodes[:20]:  # Первые 20
            print(f"{node['network']:<12} {node['country']:<20} {node['city']:<20} {node.get('type', 'N/A'):<15}")
        
        if len(nodes) > 20:
            print(f"... и ещё {len(nodes) - 20} узлов")
    
    def connect_to_dvpn(self, node_address, network):
        """Подключиться к dVPN узлу"""
        print(f"\n🔌 Подключение к {network} узлу: {node_address}")
        
        if network == 'Sentinel':
            return self.connect_sentinel(node_address)
        elif network == 'Mysterium':
            return self.connect_mysterium(node_address)
        else:
            print(f"❌ Неизвестная сеть: {network}")
            return False
    
    def connect_sentinel(self, address):
        """Подключение к Sentinel"""
        try:
            # Создаём конфиг для Sentinel
            config = {
                'network': 'sentinel',
                'provider': address,
                'free': True
            }
            
            config_file = DVPN_DIR / "sentinel_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Конфиг Sentinel создан: {config_file}")
            print("💡 Для подключения используйте:")
            print(f"   sentinel-cli connect {address}")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def connect_mysterium(self, provider_id):
        """Подключение к Mysterium"""
        try:
            # Mysterium требует node ID
            config = {
                'network': 'mysterium',
                'provider': provider_id,
                'type': 'openvpn'
            }
            
            config_file = DVPN_DIR / "mysterium_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Конфиг Mysterium создан: {config_file}")
            print("💡 Для подключения используйте:")
            print(f"   mystcli connect --provider={provider_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False


def main():
    """Основная функция"""
    manager = DeVPNManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'fetch':
            manager.fetch_all_dvpn()
        elif command == 'list':
            network = sys.argv[2] if len(sys.argv) > 2 else None
            manager.list_nodes(network)
        elif command == 'connect':
            if len(sys.argv) < 4:
                print("Использование: dvpn connect <network> <address>")
                sys.exit(1)
            network = sys.argv[2]
            address = sys.argv[3]
            manager.connect_to_dvpn(address, network)
        else:
            print("Команды: fetch, list [network], connect <network> <address>")
    else:
        # По умолчанию - получить и показать
        manager.fetch_all_dvpn()
        manager.list_nodes()


if __name__ == "__main__":
    import sys
    main()
