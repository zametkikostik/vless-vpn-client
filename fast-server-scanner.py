#!/usr/bin/env python3
"""
VLESS VPN - Fast Server Scanner
Быстрый поиск серверов с низким пингом
"""

import json
import asyncio
import socket
from pathlib import Path
from datetime import datetime
from typing import List, Dict

SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "servers.json"
FAST_SERVERS_FILE = Path.home() / "vless-vpn-client" / "data" / "fast_servers.json"


async def test_ping(host: str, port: int, timeout: int = 3) -> int:
    """Проверка пинга сервера"""
    try:
        start = asyncio.get_event_loop().time()
        
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        
        end = asyncio.get_event_loop().time()
        latency = int((end - start) * 1000)
        
        writer.close()
        await writer.wait_closed()
        
        return latency
    except:
        return 9999


async def scan_servers(servers: List[Dict], max_concurrent: int = 50) -> List[Dict]:
    """Сканирование серверов"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scan_with_semaphore(server):
        async with semaphore:
            latency = await test_ping(server['host'], server['port'])
            server['latency'] = latency
            server['is_fast'] = latency < 100
            return server
    
    tasks = [scan_with_semaphore(server) for server in servers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r for r in results if isinstance(r, dict)]


def load_servers() -> List[Dict]:
    """Загрузка серверов"""
    if not SERVERS_FILE.exists():
        print("❌ Файл серверов не найден!")
        print("Запустите: vless-vpn-ultimate update")
        return []
    
    with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_fast_servers(servers: List[Dict]):
    """Сохранение быстрых серверов"""
    # Сортировка по пингу
    servers.sort(key=lambda x: x.get('latency', 9999))
    
    # Сохраняем топ 50
    fast_servers = servers[:50]
    
    with open(FAST_SERVERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'scanned_at': datetime.now().isoformat(),
            'total': len(servers),
            'fast_count': len(fast_servers),
            'servers': fast_servers
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Сохранено {len(fast_servers)} быстрых серверов")


def show_top_servers(servers: List[Dict], top: int = 20):
    """Показать топ серверов"""
    print("\n" + "=" * 70)
    print(f"🏆 ТОП-{top} БЫСТРЫХ СЕРВЕРОВ")
    print("=" * 70)
    
    for i, server in enumerate(servers[:top], 1):
        latency = server.get('latency', 9999)
        country = server.get('country', '🌍')
        host = server.get('host', '')
        port = server.get('port', 443)
        name = server.get('name', '')
        
        # Индикатор качества
        if latency < 50:
            quality = "🟢 ОТЛИЧНО"
        elif latency < 100:
            quality = "🟡 ХОРОШО"
        elif latency < 200:
            quality = "🟠 НОРМАЛЬНО"
        else:
            quality = "🔴 МЕДЛЕННО"
        
        print(f"{i:2}. {country} {host}:{port}")
        print(f"    Пинг: {latency}ms | {quality}")
        if name:
            print(f"    Название: {name}")
        print()


def main():
    """Основная функция"""
    print("=" * 70)
    print("🚀 БЫСТРЫЙ ПОИСК СЕРВЕРОВ")
    print("=" * 70)
    print()
    
    # Загрузка серверов
    print("📥 Загрузка серверов...")
    servers = load_servers()
    
    if not servers:
        return
    
    print(f"✅ Загружено {len(servers)} серверов")
    
    # Фильтрация reality серверов
    reality_servers = [
        s for s in servers
        if s.get('security') == 'reality'
        and s.get('host')
        and s.get('port')
    ]
    
    print(f"📊 Reality серверов: {len(reality_servers)}")
    print()
    
    # Сканирование
    print("🔍 Сканирование серверов...")
    print("⏳ Это может занять несколько секунд...")
    print()
    
    fast_servers = asyncio.run(scan_servers(reality_servers))
    
    # Статистика
    total = len(fast_servers)
    fast = sum(1 for s in fast_servers if s.get('latency', 9999) < 100)
    medium = sum(1 for s in fast_servers if 100 <= s.get('latency', 9999) < 200)
    slow = sum(1 for s in fast_servers if s.get('latency', 9999) >= 200)
    
    print()
    print("=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"Всего проверено: {total}")
    print(f"🟢 Быстрые (<100ms): {fast}")
    print(f"🟡 Средние (100-200ms): {medium}")
    print(f"🔴 Медленные (>200ms): {slow}")
    print()
    
    # Показать лучшие
    show_top_servers(fast_servers)
    
    # Сохранение
    save_fast_servers(fast_servers)
    
    print("=" * 70)
    print("✅ СКАНИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 70)
    print()
    print("📁 Быстрые серверы сохранены в:")
    print(f"   {FAST_SERVERS_FILE}")
    print()
    print("🔌 Для подключения к быстрому серверу:")
    print("   vless-vpn-ultimate start")
    print()


if __name__ == "__main__":
    main()
