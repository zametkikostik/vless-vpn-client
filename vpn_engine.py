#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
VPN Engine - ядро VPN клиента (управление Xray)

© 2026 VPN Client Aggregator
"""

import asyncio
import subprocess
import json
import signal
import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# Импорты локальных модулей
from config_manager import ConfigManager
from dpi_bypass import DPIBypass
from split_tunnel import SplitTunnelManager, SplitTunnelConfig
from domain_lists import DomainListsLoader
from connection_monitor import ConnectionMonitor, MonitorConfig, ConnectionState


class EngineState(Enum):
    """Состояния VPN двигателя"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class EngineConfig:
    """Конфигурация VPN двигателя"""
    auto_start: bool = False
    auto_reconnect: bool = True
    log_level: str = "warning"
    config_dir: Path = field(default_factory=lambda: Path.home() / "vpn-client-aggregator" / "config")
    data_dir: Path = field(default_factory=lambda: Path.home() / "vpn-client-aggregator" / "data")
    logs_dir: Path = field(default_factory=lambda: Path.home() / "vpn-client-aggregator" / "logs")


class VPNEngine:
    """
    Ядро VPN клиента.
    
    Объединяет все компоненты:
    - ConfigManager (конфигурации)
    - DPIBypass (обход DPI)
    - SplitTunnelManager (split-tunneling)
    - DomainListsLoader (списки доменов)
    - ConnectionMonitor (автопереподключение)
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Инициализация VPN двигателя.
        
        Args:
            config: Конфигурация двигателя
        """
        self.config = config or EngineConfig()
        
        # Создание директорий
        for d in [self.config.config_dir, self.config.data_dir, self.config.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Инициализация компонентов
        self.config_manager = ConfigManager(self.config.config_dir)
        self.dpi_bypass = DPIBypass()
        self.split_tunnel = SplitTunnelManager()
        self.domain_loader = DomainListsLoader(self.config.data_dir)
        
        # Монитор подключения (создаётся позже)
        self.connection_monitor: Optional[ConnectionMonitor] = None
        
        # Состояние
        self.state = EngineState.STOPPED
        self._xray_process: Optional[subprocess.Popen] = None
        self._xray_pid: Optional[int] = None
        
        # Callbacks
        self._on_state_change: Optional[Callable[[EngineState], None]] = None
        self._log_callback: Optional[Callable[[str], None]] = None
        
        # Статистика
        self.stats = {
            'start_time': None,
            'stop_time': None,
            'total_connections': 0,
            'total_disconnections': 0,
            'errors': []
        }
    
    # ==========================================================================
    # MAIN METHODS
    # ==========================================================================
    
    async def start(self) -> bool:
        """
        Запуск VPN двигателя.
        
        Returns:
            True если запуск успешен
        """
        if self.state != EngineState.STOPPED:
            self._log(f"Двигатель уже запущен (состояние: {self.state.value})")
            return False
        
        self._set_state(EngineState.STARTING)
        self._log("🚀 Запуск VPN двигателя...")
        
        try:
            # 1. Загрузка конфигурации
            self._log("📋 Загрузка конфигурации...")
            config = self.config_manager.load_config()
            
            # 2. Проверка настроек сервера
            if not config.get('server', {}).get('address'):
                raise Exception("Сервер не настроен. Укажите IP адрес сервера.")
            
            if not config.get('server', {}).get('uuid'):
                raise Exception("UUID не настроен. Сгенерируйте или укажите UUID.")
            
            # 3. Обновление списков доменов
            self._log("📥 Загрузка списков доменов...")
            if self.domain_loader.should_update():
                try:
                    await self.domain_loader.update_all_lists()
                except Exception as e:
                    self._log(f"⚠️ Не удалось обновить списки: {e}")
            
            # 4. Генерация конфигурации Xray
            self._log("⚙️ Генерация конфигурации Xray...")
            xray_config = self._generate_xray_config()
            
            # Сохранение конфигурации
            config_file = self.config.config_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(xray_config, f, indent=2, ensure_ascii=False)
            
            # 5. Создание монитора подключения
            self.connection_monitor = self._create_connection_monitor()
            self.connection_monitor.set_log_callback(self._log)
            
            # 6. Запуск Xray
            self._log("🔧 Запуск Xray...")
            if await self._start_xray(config_file):
                self._set_state(EngineState.RUNNING)
                self.stats['start_time'] = datetime.now()
                self.stats['total_connections'] += 1
                
                self._log("✅ VPN двигатель запущен")
                
                # Запуск монитора
                if self.config.auto_reconnect:
                    await self.connection_monitor.start()
                
                return True
            else:
                raise Exception("Не удалось запустить Xray")
                
        except Exception as e:
            self._set_state(EngineState.ERROR)
            self.stats['errors'].append(str(e))
            self._log(f"❌ Ошибка запуска: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Остановка VPN двигателя.
        
        Returns:
            True если остановка успешна
        """
        if self.state == EngineState.STOPPED:
            return True
        
        self._set_state(EngineState.STOPPING)
        self._log("⏹️ Остановка VPN двигателя...")
        
        try:
            # Остановка монитора подключения
            if self.connection_monitor:
                await self.connection_monitor.stop()
            
            # Остановка Xray
            await self._stop_xray()
            
            self._set_state(EngineState.STOPPED)
            self.stats['stop_time'] = datetime.now()
            self.stats['total_disconnections'] += 1
            
            self._log("✅ VPN двигатель остановлен")
            return True
            
        except Exception as e:
            self._set_state(EngineState.ERROR)
            self.stats['errors'].append(str(e))
            self._log(f"❌ Ошибка остановки: {e}")
            return False
    
    async def restart(self) -> bool:
        """
        Перезапуск VPN двигателя.
        
        Returns:
            True если перезапуск успешен
        """
        self._log("🔄 Перезапуск VPN двигателя...")
        
        await self.stop()
        await asyncio.sleep(2)
        
        return await self.start()
    
    def is_connected(self) -> bool:
        """
        Проверка подключения.
        
        Returns:
            True если подключено
        """
        if self.connection_monitor:
            return self.connection_monitor.is_connected()
        return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Получение информации о подключении.
        
        Returns:
            Информация о подключении
        """
        info = {
            'state': self.state.value,
            'connected': self.is_connected(),
            'stats': self.stats
        }
        
        if self.connection_monitor:
            info['monitor'] = self.connection_monitor.get_stats()
        
        if self.state == EngineState.RUNNING:
            uptime = self.get_uptime()
            info['uptime'] = uptime
            info['uptime_formatted'] = self._format_uptime(uptime)
        
        return info
    
    def get_uptime(self) -> float:
        """
        Получение времени работы.
        
        Returns:
            Время в секундах
        """
        if not self.stats['start_time']:
            return 0.0
        
        if self.state == EngineState.RUNNING:
            return (datetime.now() - self.stats['start_time']).total_seconds()
        elif self.stats['stop_time']:
            return (self.stats['stop_time'] - self.stats['start_time']).total_seconds()
        
        return 0.0
    
    def update_server_config(self, address: str, port: int = 443, uuid: str = "", 
                            sni: str = "google.com", flow: str = "xtls-rprx-vision") -> bool:
        """
        Обновление конфигурации сервера.
        
        Args:
            address: IP адрес или домен сервера
            port: Порт
            uuid: UUID клиента
            sni: SNI (домен маскировки)
            flow: Flow (xtls-rprx-vision)
        
        Returns:
            True если обновление успешно
        """
        updates = {
            'server': {
                'address': address,
                'port': port,
                'uuid': uuid,
                'sni': sni,
                'flow': flow
            }
        }
        
        return self.config_manager.update_config(updates)
    
    def update_split_tunnel_config(self, enabled: bool = True,
                                   blacklist: Optional[List[str]] = None,
                                   whitelist: Optional[List[str]] = None) -> bool:
        """
        Обновление конфигурации split-tunneling.
        
        Args:
            enabled: Включить split-tunneling
            blacklist: Категории для VPN
            whitelist: Категории для прямого подключения
        
        Returns:
            True если обновление успешно
        """
        updates = {
            'split_tunnel': {
                'enabled': enabled
            }
        }
        
        if blacklist:
            updates['split_tunnel']['blacklist_categories'] = blacklist
        
        if whitelist:
            updates['split_tunnel']['whitelist_categories'] = whitelist
        
        return self.config_manager.update_config(updates)
    
    def set_callbacks(self, on_state_change: Optional[Callable[[EngineState], None]] = None,
                     log_callback: Optional[Callable[[str], None]] = None):
        """
        Установка callback функций.
        
        Args:
            on_state_change: Callback при изменении состояния
            log_callback: Callback для логов
        """
        self._on_state_change = on_state_change
        self._log_callback = log_callback
        
        if self.connection_monitor:
            self.connection_monitor.set_log_callback(log_callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики двигателя.
        
        Returns:
            # Statistics
        """
        return {
            'state': self.state.value,
            'connected': self.is_connected(),
            'uptime': self.get_uptime(),
            'config_manager': self.config_manager.get_stats(),
            'split_tunnel': self.split_tunnel.get_stats(),
            'domain_loader': self.domain_loader.get_stats(),
            'dpi_bypass': self.dpi_bypass.get_stats(),
            'stats': self.stats
        }
    
    # ==========================================================================
    # PRIVATE METHODS
    # ==========================================================================
    
    def _set_state(self, state: EngineState):
        """Установка состояния"""
        old_state = self.state
        self.state = state
        
        self._log(f"Состояние: {old_state.value} → {state.value}")
        
        if self._on_state_change:
            self._on_state_change(state)
    
    def _generate_xray_config(self) -> Dict[str, Any]:
        """Генерация конфигурации Xray"""
        # Получение базовой конфигурации
        config = self.config_manager.load_config()
        
        # Генерация через ConfigManager
        xray_config = self.config_manager.generate_xray_config()
        
        # Применение DPI bypass
        if config.get('dpi_bypass', {}).get('enabled', True):
            dpi_config = self.dpi_bypass.get_xray_config()
            if 'streamSettings' in dpi_config:
                for outbound in xray_config.get('outbounds', []):
                    if outbound.get('tag') == 'proxy':
                        if 'streamSettings' not in outbound:
                            outbound['streamSettings'] = {}
                        # Обновляем только sockopt, не заменяя весь streamSettings
                        if 'sockopt' in dpi_config['streamSettings']:
                            outbound['streamSettings']['sockopt'] = dpi_config['streamSettings']['sockopt']
                        if 'fragment' in dpi_config:
                            outbound['streamSettings']['fragment'] = dpi_config['fragment']
        
        return xray_config
    
    def _create_connection_monitor(self) -> ConnectionMonitor:
        """Создание монитора подключения"""
        config = self.config_manager.load_config()
        
        monitor_config = MonitorConfig(
            enabled=config.get('auto_reconnect', {}).get('enabled', True),
            max_reconnect_attempts=config.get('auto_reconnect', {}).get('max_attempts', 10),
            reconnect_delay_seconds=config.get('auto_reconnect', {}).get('delay_seconds', 5),
            health_check_interval_seconds=config.get('auto_reconnect', {}).get('health_check_interval', 30),
            health_check_url=config.get('auto_reconnect', {}).get('health_check_url', "https://www.google.com/generate_204"),
            exponential_backoff=True,
            notify_on_reconnect=True
        )
        
        return ConnectionMonitor(
            config=monitor_config,
            on_connect=self._on_connected,
            on_disconnect=self._on_disconnected,
            on_reconnect=self._on_reconnecting
        )
    
    async def _start_xray(self, config_file: Path) -> bool:
        """Запуск процесса Xray"""
        try:
            # Поиск Xray
            xray_path = self._find_xray()
            if not xray_path:
                raise Exception("Xray не найден. Установите Xray-core.")
            
            self._log(f"Xray найден: {xray_path}")
            
            # Запуск процесса
            self._xray_process = subprocess.Popen(
                [xray_path, "run", "-c", str(config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            self._xray_pid = self._xray_process.pid
            
            self._log(f"Xray запущен (PID: {self._xray_pid})")
            
            # Проверка запуска
            await asyncio.sleep(3)
            
            if self._xray_process.poll() is not None:
                # Процесс завершился
                stdout, stderr = self._xray_process.communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Неизвестная ошибка"
                self._log(f"❌ Xray завершился: {error_msg}")
                return False
            
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка запуска Xray: {e}")
            return False
    
    async def _stop_xray(self) -> bool:
        """Остановка процесса Xray"""
        if not self._xray_pid:
            return True
        
        try:
            self._log(f"Остановка Xray (PID: {self._xray_pid})...")
            
            # SIGTERM
            os.killpg(os.getpgid(self._xray_pid), signal.SIGTERM)
            
            # Ожидание завершения
            for _ in range(10):
                if self._xray_process.poll() is not None:
                    break
                await asyncio.sleep(0.5)
            
            # Если не завершился - SIGKILL
            if self._xray_process.poll() is None:
                os.killpg(os.getpgid(self._xray_pid), signal.SIGKILL)
            
            self._xray_process = None
            self._xray_pid = None
            
            self._log("Xray остановлен")
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка остановки Xray: {e}")
            return False
    
    def _find_xray(self) -> Optional[str]:
        """Поиск исполняемого файла Xray"""
        paths = [
            "/usr/local/bin/xray",
            "/usr/bin/xray",
            str(Path.home() / "bin" / "xray"),
            str(Path.home() / ".local" / "bin" / "xray"),
            "xray"
        ]
        
        for path in paths:
            try:
                if path == "xray":
                    result = subprocess.run(
                        ["command", "-v", "xray"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return result.stdout.strip() or path
                else:
                    if Path(path).exists() and os.access(path, os.X_OK):
                        return path
            except:
                pass
        
        # Проверка через xray version
        try:
            result = subprocess.run(["xray", "version"], capture_output=True)
            if result.returncode == 0:
                return "xray"
        except:
            pass
        
        return None
    
    def _log(self, message: str):
        """Логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self._log_callback:
            self._log_callback(log_message)
        else:
            print(log_message)
    
    def _format_uptime(self, seconds: float) -> str:
        """Форматирование uptime"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # Callbacks от монитора подключения
    def _on_connected(self):
        self._log("✅ Подключение установлено")
    
    def _on_disconnected(self):
        self._log("⏹️ Подключение разорвано")
    
    def _on_reconnecting(self, attempt: int):
        self._log(f"🔄 Переподключение (попытка {attempt})...")


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование VPNEngine...")
    
    # Создание двигателя
    engine = VPNEngine()
    
    # Callback для логов
    def log_callback(message: str):
        print(f"   {message}")
    
    engine.set_callbacks(log_callback=log_callback)
    
    # Статистика
    print("\n📊 Статистика:")
    stats = engine.get_stats()
    print(f"   Состояние: {stats['state']}")
    print(f"   Конфигурация: {stats['config_manager']}")
    
    # Проверка Xray
    print("\n🔍 Проверка Xray...")
    xray_path = engine._find_xray()
    print(f"   Путь: {xray_path if xray_path else 'Не найден'}")
    
    print("\n✅ VPNEngine готов к работе!")
