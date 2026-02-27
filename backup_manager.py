#!/usr/bin/env python3
"""
Backup Server Manager - Резервные серверы для Чебурнета
- Добавление 100+ резервных серверов
- Автоматическое переключение при блокировке
- Экспорт/Импорт конфигов
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class BackupServerManager:
    """Менеджер резервных серверов"""
    
    def __init__(self):
        self.data_dir = Path.home() / "vpn-client-aggregator" / "data"
        self.servers_file = self.data_dir / "servers.json"
        self.backup_file = self.data_dir / "backup_servers.json"
        self.export_dir = self.data_dir / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def add_backup_servers(self, count: int = 100) -> int:
        """Добавление резервных серверов"""
        print(f"🔍 Поиск {count} резервных серверов...")
        
        # Источники с серверами
        sources = [
            "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/etc/list/list.txt",
            "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
            "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
        ]
        
        new_servers = []
        
        async with aiohttp.ClientSession() as session:
            for url in sources:
                try:
                    async with session.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as response:
                        if response.status == 200:
                            content = await response.text()
                            servers = self.parse_servers(content)
                            new_servers.extend(servers)
                            print(f"  ✅ {url.split('/')[-1]}: {len(servers)} серверов")
                except:
                    pass
        
        # Проверяем и добавляем
        added = self.merge_servers(new_servers[:count])
        print(f"💾 Добавлено {added} резервных серверов")
        
        return added
    
    def parse_servers(self, content: str) -> List[Dict]:
        """Парсинг серверов из контента"""
        servers = []
        
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('vless://'):
                try:
                    server = self.parse_vless_url(line)
                    if server:
                        servers.append(server)
                except:
                    continue
        
        return servers
    
    def parse_vless_url(self, url: str) -> Dict:
        """Парсинг VLESS URL"""
        try:
            url = url.replace('vless://', '')
            
            if '#' in url:
                url, name = url.split('#', 1)
            else:
                name = ""
            
            parts = url.split('@')
            if len(parts) != 2:
                return None
            
            uuid = parts[0]
            host_port = parts[1]
            
            if ':' not in host_port:
                return None
            
            host, rest = host_port.split(':', 1)
            port = int(rest.split('?')[0])
            
            if '?' not in rest:
                return None
            
            params = rest.split('?', 1)[1]
            params_dict = {}
            for param in params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params_dict[key] = value
            
            return {
                'host': host,
                'port': port,
                'uuid': uuid,
                'protocol': 'vless',
                'name': name,
                'is_working': False,
                'latency': 9999,
                'stream_settings': {
                    'reality_settings': {
                        'serverName': params_dict.get('sni', ''),
                        'publicKey': params_dict.get('pbk', ''),
                        'shortId': params_dict.get('sid', ''),
                        'fingerprint': params_dict.get('fp', 'chrome')
                    }
                },
                'flow': params_dict.get('flow', 'xtls-rprx-vision'),
                'security': params_dict.get('security', 'reality')
            }
        except:
            return None
    
    def merge_servers(self, new_servers: List[Dict]) -> int:
        """Объединение с существующими серверами"""
        existing = []
        
        if self.servers_file.exists():
            with open(self.servers_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        # Проверяем дубликаты
        existing_keys = set()
        for s in existing:
            key = f"{s.get('host', '')}:{s.get('port', 443)}"
            existing_keys.add(key)
        
        # Добавляем новые
        added = 0
        for server in new_servers:
            key = f"{server['host']}:{server['port']}"
            if key not in existing_keys:
                existing.append(server)
                added += 1
                existing_keys.add(key)
        
        # Сохраняем
        with open(self.servers_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        return added
    
    def export_configs(self, format: str = "all") -> str:
        """Экспорт конфигов для резервного копирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Загружаем серверы
        with open(self.servers_file, 'r', encoding='utf-8') as f:
            servers = json.load(f)
        
        # Только рабочие
        working = [s for s in servers if s.get('is_working', False)]
        
        if not working:
            working = servers[:50]  # Берём первые 50
        
        export_file = self.export_dir / f"vpn_backup_{timestamp}.json"
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_servers": len(working),
            "version": "3.0",
            "servers": working
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Экспорт сохранён: {export_file}")
        
        return str(export_file)
    
    def import_configs(self, import_file: str) -> int:
        """Импорт конфигов из резервной копии"""
        import_path = Path(import_file)
        
        if not import_path.exists():
            print(f"❌ Файл не найден: {import_file}")
            return 0
        
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_servers = import_data.get('servers', [])
        
        # Объединяем
        added = self.merge_servers(imported_servers)
        
        print(f"📥 Импортировано {added} серверов")
        
        return added
    
    def get_best_servers(self, count: int = 10) -> List[Dict]:
        """Получение лучших серверов"""
        with open(self.servers_file, 'r', encoding='utf-8') as f:
            servers = json.load(f)
        
        # Только рабочие, сортировка по пингу
        working = [s for s in servers if s.get('is_working', False)]
        working.sort(key=lambda x: x.get('latency', 9999))
        
        return working[:count]
    
    def create_auto_switch_config(self) -> Dict:
        """Создание конфига с авто-переключением"""
        best_servers = self.get_best_servers(5)
        
        config = {
            "auto_switch": {
                "enabled": True,
                "check_interval": 30,  # Проверка каждые 30 секунд
                "switch_threshold": 3,  # Переключение после 3 неудач
                "servers": []
            }
        }
        
        for i, server in enumerate(best_servers):
            config["auto_switch"]["servers"].append({
                "priority": i + 1,
                "host": server.get('host'),
                "port": server.get('port'),
                "uuid": server.get('uuid'),
                "stream_settings": server.get('stream_settings', {})
            })
        
        return config


async def main():
    """Основная функция"""
    print("🛡️  Backup Server Manager v1.0")
    print("=" * 60)
    
    manager = BackupServerManager()
    
    # Добавляем резервные серверы
    added = await manager.add_backup_servers(100)
    
    # Экспортируем конфиги
    export_file = manager.export_configs()
    
    # Создаём конфиг авто-переключения
    auto_config = manager.create_auto_switch_config()
    
    print("=" * 60)
    print("✅ Резервные серверы готовы!")
    print(f"📊 Добавлено: {added} серверов")
    print(f"💾 Экспорт: {export_file}")
    print(f"🔄 Авто-переключение: {len(auto_config['auto_switch']['servers'])} серверов")


if __name__ == '__main__':
    asyncio.run(main())
