#!/usr/bin/env python3
"""Тест подключения к VPN без GUI"""
import asyncio
from pathlib import Path
import sys

# Добавляем путь
sys.path.insert(0, str(Path(__file__).parent))

from vpn_controller import VPNController

async def main():
    print("🔧 Инициализация контроллера...")
    controller = VPNController()
    controller.initialize()
    
    print("📂 Загрузка конфигурации...")
    config = controller.config_manager.load_config()
    server = config.get('server', {})
    
    print(f"✅ Сервер: {server.get('address', 'N/A')}:{server.get('port', 'N/A')}")
    print(f"✅ UUID: {server.get('uuid', 'N/A')[:8] if server.get('uuid') else 'N/A'}...")
    print(f"✅ SNI: {server.get('sni', 'N/A')}")
    
    print("\n🔄 Попытка подключения...")
    try:
        result = await controller.start()
        if result:
            print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")
        else:
            print("❌ Подключение не удалось")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    # Ждём 5 секунд и отключаемся
    await asyncio.sleep(5)
    
    print("\n🔄 Отключение...")
    try:
        await controller.stop()
        print("✅ Отключено")
    except Exception as e:
        print(f"❌ Ошибка отключения: {e}")

if __name__ == '__main__':
    asyncio.run(main())
