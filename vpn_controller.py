#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
VPN Controller - контроллер управления VPN

© 2026 VPN Client Aggregator
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# Импорты локальных модулей
from vpn_engine import VPNEngine, EngineState, EngineConfig
from config_manager import ConfigManager


class VPNController:
    """
    Контроллер управления VPN клиентом.
    
    Предоставляет единый интерфейс для:
    - Запуска/остановки VPN
    - Управления конфигурацией
    - Мониторинга состояния
    - Обработки команд
    """
    
    def __init__(self):
        """Инициализация контроллера"""
        self.engine: Optional[VPNEngine] = None
        self.config_manager: ConfigManager = ConfigManager()
        
        self._running = False
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Callbacks
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        self._on_log: Optional[Callable[[str], None]] = None
        
        # Статистика команд
        self.command_stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'last_command': None,
            'last_command_time': None
        }
    
    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def initialize(self) -> bool:
        """
        Инициализация контроллера.
        
        Returns:
            True если инициализация успешна
        """
        try:
            self._log("Инициализация VPN Controller...")
            
            # Создание двигателя
            self.engine = VPNEngine()
            
            # Установка callback
            self.engine.set_callbacks(
                on_state_change=self._on_engine_state_change,
                log_callback=self._log
            )
            
            self._log("✅ VPN Controller инициализирован")
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Запуск VPN.
        
        Returns:
            True если запуск успешен
        """
        self._record_command("start")
        
        if not self.engine:
            self._log("❌ Контроллер не инициализирован")
            return False
        
        if self.engine.is_connected():
            self._log("⚠️ VPN уже подключён")
            return True
        
        self._log("🚀 Запуск VPN...")
        
        try:
            result = await self.engine.start()
            
            if result:
                self._log("✅ VPN подключён")
                if self._on_connect:
                    self._on_connect()
                self._record_command("start", True)
            else:
                self._log("❌ Не удалось подключить VPN")
                self._record_command("start", False)
            
            return result
            
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
            if self._on_error:
                self._on_error(str(e))
            self._record_command("start", False)
            return False
    
    async def stop(self) -> bool:
        """
        Остановка VPN.
        
        Returns:
            True если остановка успешна
        """
        self._record_command("stop")
        
        if not self.engine:
            return False
        
        if not self.engine.is_connected():
            self._log("ℹ️ VPN не подключён")
            return True
        
        self._log("⏹️ Остановка VPN...")
        
        try:
            result = await self.engine.stop()
            
            if result:
                self._log("✅ VPN отключён")
                if self._on_disconnect:
                    self._on_disconnect()
                self._record_command("stop", True)
            else:
                self._log("❌ Не удалось отключить VPN")
                self._record_command("stop", False)
            
            return result
            
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
            self._record_command("stop", False)
            return False
    
    async def restart(self) -> bool:
        """
        Перезапуск VPN.
        
        Returns:
            True если перезапуск успешен
        """
        self._record_command("restart")
        self._log("🔄 Перезапуск VPN...")
        
        if not self.engine:
            return False
        
        try:
            result = await self.engine.restart()
            
            if result:
                self._log("✅ VPN перезапущен")
                self._record_command("restart", True)
            else:
                self._log("❌ Не удалось перезапустить VPN")
                self._record_command("restart", False)
            
            return result
            
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
            self._record_command("restart", False)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса VPN.
        
        Returns:
            Статус
        """
        if not self.engine:
            return {
                'initialized': False,
                'connected': False,
                'state': 'not_initialized'
            }
        
        info = self.engine.get_connection_info()
        info['initialized'] = True
        
        return info
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение полной статистики.
        
        Returns:
            Статистика
        """
        stats = {
            'controller': self.command_stats,
            'engine': self.engine.get_stats() if self.engine else None
        }
        return stats
    
    # ==========================================================================
    # УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ
    # ==========================================================================
    
    def configure_server(self, address: str, port: int = 443, uuid: str = "",
                        sni: str = "google.com", flow: str = "xtls-rprx-vision") -> bool:
        """
        Настройка сервера.
        
        Args:
            address: IP или домен сервера
            port: Порт
            uuid: UUID клиента
            sni: SNI (домен маскировки)
            flow: Flow
        
        Returns:
            True если настройка успешна
        """
        self._log(f"Настройка сервера: {address}:{port}")
        
        result = self.engine.update_server_config(
            address=address,
            port=port,
            uuid=uuid,
            sni=sni,
            flow=flow
        )
        
        if result:
            self._log("✅ Сервер настроен")
        else:
            self._log("❌ Ошибка настройки сервера")
        
        return result
    
    def configure_split_tunnel(self, enabled: bool = True,
                               blacklist: Optional[list] = None,
                               whitelist: Optional[list] = None) -> bool:
        """
        Настройка split-tunneling.
        
        Args:
            enabled: Включить
            blacklist: Категории для VPN
            whitelist: Категории для прямого подключения
        
        Returns:
            True если настройка успешна
        """
        self._log(f"Настройка split-tunneling: {'вкл' if enabled else 'выкл'}")
        
        result = self.engine.update_split_tunnel_config(
            enabled=enabled,
            blacklist=blacklist,
            whitelist=whitelist
        )
        
        if result:
            self._log("✅ Split-tunneling настроен")
        else:
            self._log("❌ Ошибка настройки split-tunneling")
        
        return result
    
    def load_config(self, config_file: Path) -> bool:
        """
        Загрузка конфигурации из файла.
        
        Args:
            config_file: Путь к файлу конфигурации
        
        Returns:
            True если загрузка успешна
        """
        self._log(f"Загрузка конфигурации: {config_file}")
        
        try:
            if not config_file.exists():
                raise FileNotFoundError(f"Файл не найден: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Применение конфигурации
            if 'server' in config:
                server = config['server']
                self.configure_server(
                    address=server.get('address', ''),
                    port=server.get('port', 443),
                    uuid=server.get('uuid', ''),
                    sni=server.get('sni', 'google.com'),
                    flow=server.get('flow', 'xtls-rprx-vision')
                )
            
            if 'split_tunnel' in config:
                st = config['split_tunnel']
                self.configure_split_tunnel(
                    enabled=st.get('enabled', True),
                    blacklist=st.get('blacklist_categories'),
                    whitelist=st.get('whitelist_categories')
                )
            
            self._log("✅ Конфигурация загружена")
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка загрузки конфигурации: {e}")
            return False
    
    def save_config(self, config_file: Path) -> bool:
        """
        Сохранение конфигурации в файл.
        
        Args:
            config_file: Путь к файлу
        
        Returns:
            True если сохранение успешно
        """
        self._log(f"Сохранение конфигурации: {config_file}")
        
        try:
            config = self.config_manager.load_config()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._log("✅ Конфигурация сохранена")
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка сохранения конфигурации: {e}")
            return False
    
    def generate_uuid(self) -> str:
        """
        Генерация UUID.
        
        Returns:
            Новый UUID
        """
        return self.config_manager.generate_uuid()
    
    # ==========================================================================
    # CALLBACKS
    # ==========================================================================
    
    def set_callbacks(self,
                     on_connect: Optional[Callable] = None,
                     on_disconnect: Optional[Callable] = None,
                     on_error: Optional[Callable] = None,
                     on_log: Optional[Callable[[str], None]] = None):
        """
        Установка callback функций.
        
        Args:
            on_connect: Вызывается при подключении
            on_disconnect: Вызывается при отключении
            on_error: Вызывается при ошибке
            on_log: Вызывается для логов
        """
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_error = on_error
        self._on_log = on_log
    
    # ==========================================================================
    ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _on_engine_state_change(self, state: EngineState):
        """Callback при изменении состояния двигателя"""
        self._log(f"Состояние двигателя: {state.value}")
    
    def _log(self, message: str):
        """Логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self._on_log:
            self._on_log(log_message)
        else:
            print(log_message)
    
    def _record_command(self, command: str, success: bool = False):
        """Запись статистики команды"""
        self.command_stats['total_commands'] += 1
        
        if success:
            self.command_stats['successful_commands'] += 1
        else:
            self.command_stats['failed_commands'] += 1
        
        self.command_stats['last_command'] = command
        self.command_stats['last_command_time'] = datetime.now().isoformat()
    
    def run_async(self, coro):
        """Запуск асинхронной функции"""
        if not self._event_loop:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
        
        return self._event_loop.run_until_complete(coro)


# =============================================================================
# КОНСОЛЬНЫЙ ИНТЕРФЕЙС
# =============================================================================

def print_help():
    """Вывод справки"""
    print("""
🛡️ VPN Controller v5.0 - Команды управления

Команды:
  start           - Подключить VPN
  stop            - Отключить VPN
  restart         - Перезапустить VPN
  status          - Показать статус
  stats           - Показать статистику
  
  config show     - Показать конфигурацию
  config save     - Сохранить конфигурацию
  config load     - Загрузить конфигурацию
  
  server set      - Настроить сервер
  uuid generate   - Сгенерировать UUID
  
  split on        - Включить split-tunneling
  split off       - Выключить split-tunneling
  
  help            - Показать эту справку
  quit / exit     - Выход

Примеры:
  server set 192.168.1.100 443 your-uuid-here
  split on social video ai
""")


def main():
    """Консольный интерфейс"""
    print("🛡️ VPN Controller v5.0")
    print("=" * 50)
    
    controller = VPNController()
    
    if not controller.initialize():
        print("❌ Не удалось инициализировать контроллер")
        sys.exit(1)
    
    print_help()
    print()
    
    while True:
        try:
            command = input("\n🔹 vpn> ").strip().lower()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0]
            args = parts[1:]
            
            if cmd in ['quit', 'exit', 'q']:
                print("Выход...")
                break
            
            elif cmd == 'help':
                print_help()
            
            elif cmd == 'start':
                result = controller.run_async(controller.start())
                print(f"{'✅ Успешно' if result else '❌ Ошибка'}")
            
            elif cmd == 'stop':
                result = controller.run_async(controller.stop())
                print(f"{'✅ Успешно' if result else '❌ Ошибка'}")
            
            elif cmd == 'restart':
                result = controller.run_async(controller.restart())
                print(f"{'✅ Успешно' if result else '❌ Ошибка'}")
            
            elif cmd == 'status':
                status = controller.get_status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
            
            elif cmd == 'stats':
                stats = controller.get_stats()
                print(json.dumps(stats, indent=2, ensure_ascii=False))
            
            elif cmd == 'uuid' and len(args) > 0 and args[0] == 'generate':
                uuid = controller.generate_uuid()
                print(f"UUID: {uuid}")
            
            elif cmd == 'server' and len(args) > 0 and args[0] == 'set':
                if len(args) >= 4:
                    address = args[1]
                    port = int(args[2])
                    uuid = args[3]
                    sni = args[4] if len(args) > 4 else "google.com"
                    flow = args[5] if len(args) > 5 else "xtls-rprx-vision"
                    
                    result = controller.configure_server(address, port, uuid, sni, flow)
                    print(f"{'✅ Сервер настроен' if result else '❌ Ошибка'}")
                else:
                    print("Использование: server set <address> <port> <uuid> [sni] [flow]")
            
            elif cmd == 'split' and len(args) > 0:
                if args[0] == 'on':
                    result = controller.configure_split_tunnel(True, args[1:] if len(args) > 1 else None)
                    print(f"{'✅ Split-tunneling включён' if result else '❌ Ошибка'}")
                elif args[0] == 'off':
                    result = controller.configure_split_tunnel(False)
                    print(f"{'✅ Split-tunneling выключен' if result else '❌ Ошибка'}")
                else:
                    print("Использование: split on|off")
            
            elif cmd == 'config' and len(args) > 0:
                if args[0] == 'show':
                    config = controller.config_manager.load_config()
                    print(json.dumps(config, indent=2, ensure_ascii=False))
                elif args[0] == 'save':
                    path = Path(args[1]) if len(args) > 1 else Path.home() / "vpn-client-aggregator" / "config" / "backup.json"
                    result = controller.save_config(path)
                    print(f"{'✅ Сохранено' if result else '❌ Ошибка'}")
                elif args[0] == 'load':
                    if len(args) > 1:
                        path = Path(args[1])
                        result = controller.load_config(path)
                        print(f"{'✅ Загружено' if result else '❌ Ошибка'}")
                    else:
                        print("Укажите путь к файлу: config load <path>")
            
            else:
                print(f"❌ Неизвестная команда: {cmd}")
                print("Введите 'help' для справки")
                
        except KeyboardInterrupt:
            print("\n\nПрерывание...")
            controller.run_async(controller.stop())
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
