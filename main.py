#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Main - Точка входа приложения

© 2026 VPN Client Aggregator
"""

import sys
import os
from pathlib import Path

# Добавление пути к модулям
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# =============================================================================
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# =============================================================================

def check_dependencies():
    """Проверка необходимых зависимостей"""
    errors = []
    
    # Проверка Python
    if sys.version_info < (3, 8):
        errors.append("Требуется Python 3.8 или выше")
    
    # Проверка PyQt5
    try:
        import PyQt5
    except ImportError:
        errors.append("PyQt5 не установлен. Установите: pip3 install PyQt5")
    
    # Проверка aiohttp
    try:
        import aiohttp
    except ImportError:
        errors.append("aiohttp не установлен. Установите: pip3 install aiohttp")
    
    # Проверка Xray
    xray_installed = False
    xray_paths = ["/usr/local/bin/xray", "/usr/bin/xray", str(Path.home() / ".local/bin/xray")]
    for path in xray_paths:
        if Path(path).exists():
            xray_installed = True
            break
    
    if not xray_installed:
        # Проверка через command -v
        import subprocess
        try:
            result = subprocess.run(["command", "-v", "xray"], capture_output=True)
            if result.returncode == 0:
                xray_installed = True
        except:
            pass
    
    if not xray_installed:
        errors.append("Xray не установлен. Установите: bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\"")
    
    return errors


# =============================================================================
# ТОЧКИ ВХОДА
# =============================================================================

def run_gui():
    """Запуск GUI приложения"""
    errors = check_dependencies()
    
    if errors:
        print("❌ Ошибки зависимостей:")
        for error in errors:
            print(f"   - {error}")
        print("\nУстановите зависимости и попробуйте снова.")
        sys.exit(1)
    
    from vpn_gui import main
    main()


def run_console():
    """Запуск консольного интерфейса"""
    from vpn_controller import main as console_main
    console_main()


def print_help():
    """Вывод справки"""
    print("""
🛡️ VPN Client Aggregator v5.0

Использование:
  python3 main.py gui      - Запуск GUI интерфейса
  python3 main.py console  - Запуск консольного интерфейса
  python3 main.py check    - Проверка зависимостей
  python3 main.py help     - Показать эту справку

Примеры:
  python3 main.py gui
  python3 main.py console
  python3 main.py check
""")


def main():
    """Основная точка входа"""
    if len(sys.argv) < 2:
        # По умолчанию запуск GUI
        run_gui()
        return
    
    command = sys.argv[1].lower()
    
    if command == "gui":
        run_gui()
    elif command == "console":
        run_console()
    elif command == "check":
        errors = check_dependencies()
        if errors:
            print("❌ Ошибки зависимостей:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
        else:
            print("✅ Все зависимости установлены")
    elif command == "help":
        print_help()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
