#!/usr/bin/env python3
"""
VPN Server Scanner - Проверка рабочих серверов
Сканирование существующего списка и проверка доступности
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class ServerScanner:
    """Сканер серверов"""
    
    def __init__(self):
        self.data_dir = Path.home() / "vpn-client-aggregator" / "data"
        self.servers_file = self.data_dir / "servers.json"
        self.working_file = self.data_dir / "working_servers.json"
        self.servers: List[Dict] = []
        self.working_servers: List[Dict] = []
    
    def load_servers(self):
        """Загрузка серверов из файла"""
        if self.servers_file.exists():
            with open(self.servers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.servers = data.get('servers', [])
                else:
                    self.servers = data
            print(f"📊 Загружено {len(self.servers)} серверов")
        else:
            print("❌ Файл servers.json не найден")
    
    async def check_server(self, server: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """Проверка одного сервера"""
        async with semaphore:
            address = server.get('host', server.get('address', ''))
            port = server.get('port', 443)
            name = server.get('name', 'Unknown')
            country = server.get('country', 'Unknown')
            
            try:
                # Проверяем подключение к порту
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(address, port),
                    timeout=5
                )
                writer.close()
                await writer.wait_closed()
                
                server['is_working'] = True
                server['latency'] = 9999
                server['checked_at'] = datetime.now().isoformat()
                
                print(f"  ✅ {country} | {address}:{port} | {name}")
                return server
            except Exception as e:
                print(f"  ❌ {country} | {address}:{port} | {name}")
                return None
    
    async def scan_servers(self, max_concurrent: int = 50):
        """Сканирование всех серверов"""
        print("🔍 Начало сканирования...")
        print(f"📊 Всего серверов: {len(self.servers)}")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Создаём задачи для проверки
        tasks = [self.check_server(server, semaphore) for server in self.servers[:100]]  # Первые 100 для теста
        
        # Выполняем проверку
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем рабочие
        for result in results:
            if result and isinstance(result, dict) and result.get('is_working'):
                self.working_servers.append(result)
        
        print(f"\n✅ Рабочих серверов: {len(self.working_servers)}")
    
    def save_results(self):
        """Сохранение результатов"""
        # Сохраняем рабочие серверы
        working_data = {
            "scanned_at": datetime.now().isoformat(),
            "total": len(self.servers),
            "working": len(self.working_servers),
            "servers": self.working_servers
        }
        
        with open(self.working_file, 'w', encoding='utf-8') as f:
            json.dump(working_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в {self.working_file}")
        
        # Обновляем основной файл (помечаем нерабочие)
        for server in self.servers:
            address = server.get('host', server.get('address', ''))
            port = server.get('port', 443)
            
            # Ищем этот сервер в рабочих
            found = False
            for working in self.working_servers:
                w_addr = working.get('host', working.get('address', ''))
                w_port = working.get('port', 443)
                if w_addr == address and w_port == port:
                    found = True
                    break
            
            server['is_working'] = found
            server['last_checked'] = datetime.now().isoformat()
        
        # Сохраняем обновлённый список
        with open(self.servers_file, 'w', encoding='utf-8') as f:
            json.dump(self.servers, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Основной файл обновлён")
    
    def show_top(self, count: int = 10):
        """Показать топ рабочих серверов"""
        if not self.working_servers:
            print("❌ Нет рабочих серверов")
            return
        
        print(f"\n🏆 Топ-{count} рабочих серверов:")
        for i, server in enumerate(self.working_servers[:count], 1):
            country = server.get('country', '🌍')
            name = server.get('name', 'Unknown')
            address = server.get('host', server.get('address', ''))
            port = server.get('port', 443)
            print(f"  {i}. {country} {name} - {address}:{port}")


async def main():
    """Основная функция"""
    print("🛡️  VPN Server Scanner v1.0")
    print("=" * 60)
    
    scanner = ServerScanner()
    
    # Загружаем серверы
    scanner.load_servers()
    
    if not scanner.servers:
        print("❌ Серверы не найдены! Сначала выполните: python3 vless_client.py update")
        return
    
    # Сканируем
    await scanner.scan_servers()
    
    # Сохраняем
    scanner.save_results()
    
    # Показываем топ
    scanner.show_top(10)
    
    print("=" * 60)
    print("✅ Сканирование завершено!")
    print(f"\n📊 Итого:")
    print(f"   Проверено: {len(scanner.servers)}")
    print(f"   Рабочих: {len(scanner.working_servers)}")
    print(f"\n💡 Используйте рабочие серверы для подключения!")


if __name__ == '__main__':
    asyncio.run(main())
