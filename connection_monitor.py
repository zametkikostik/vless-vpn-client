#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Connection Monitor - мониторинг подключения и автопереподключение

© 2026 VPN Client Aggregator
"""

import asyncio
import subprocess
import os
import time
import socket
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp


class ConnectionState(Enum):
    """Состояния подключения"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionStats:
    """Статистика подключения"""
    state: ConnectionState = ConnectionState.DISCONNECTED
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    reconnect_attempts: int = 0
    last_reconnect_at: Optional[datetime] = None
    total_uptime_seconds: float = 0.0
    total_downtime_seconds: float = 0.0
    health_checks_passed: int = 0
    health_checks_failed: int = 0
    last_error: Optional[str] = None


@dataclass
class MonitorConfig:
    """Конфигурация монитора подключения"""
    enabled: bool = True
    max_reconnect_attempts: int = 10
    reconnect_delay_seconds: int = 5
    reconnect_delay_max_seconds: int = 60
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    health_check_url: str = "https://www.google.com/generate_204"
    check_local_connectivity: bool = True
    exponential_backoff: bool = True
    notify_on_reconnect: bool = True


class ConnectionMonitor:
    """
    Монитор подключения с функцией автопереподключения.
    
    Обеспечивает устойчивое соединение без обрывов:
    1. Постоянный мониторинг состояния VPN
    2. Проверка доступности интернета через VPN
    3. Автоматическое переподключение при обрыве
    4. Экспоненциальная задержка между попытками
    5. Уведомления о событиях
    """
    
    def __init__(
        self,
        config: Optional[MonitorConfig] = None,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_reconnect: Optional[Callable] = None
    ):
        """
        Инициализация монитора подключения.
        
        Args:
            config: Конфигурация монитора
            on_connect: Callback при подключении
            on_disconnect: Callback при отключении
            on_reconnect: Callback при переподключении
        """
        self.config = config or MonitorConfig()
        
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_reconnect = on_reconnect
        
        self.stats = ConnectionStats()
        
        # Флаги управления
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._reconnect_lock = asyncio.Lock()
        
        # Xray процесс
        self._xray_process: Optional[subprocess.Popen] = None
        self._xray_pid: Optional[int] = None
        
        # Таймеры
        self._last_health_check: Optional[datetime] = None
        self._consecutive_failures = 0
        
        # Callbacks для логирования
        self._log_callback: Optional[Callable[[str], None]] = None
    
    # ==========================================================================
    # MAIN METHODS
    # ==========================================================================
    
    async def start(self):
        """
        Запуск монитора подключения.
        """
        if self._running:
            self._log("Монитор уже запущен")
            return
        
        self._running = True
        self._log("Запуск монитора подключения...")
        
        # Запуск фонового мониторинга
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        # Попытка подключения
        await self._connect()
    
    async def stop(self):
        """
        Остановка монитора подключения.
        """
        if not self._running:
            return
        
        self._log("Остановка монитора...")
        self._running = False
        
        # Отмена задачи мониторинга
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Отключение VPN
        await self._disconnect()
        
        self._log("Монитор остановлен")
    
    async def restart(self):
        """
        Перезапуск подключения.
        """
        self._log("Перезапуск подключения...")
        await self._disconnect()
        await asyncio.sleep(2)
        await self._connect()
    
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            True если подключено
        """
        return self.stats.state == ConnectionState.CONNECTED
    
    def get_connection_uptime(self) -> float:
        """
        Получение времени бесперебойной работы.
        
        Returns:
            Время в секундах
        """
        if self.stats.state != ConnectionState.CONNECTED or not self.stats.connected_at:
            return 0.0
        
        return (datetime.now() - self.stats.connected_at).total_seconds()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики подключения.
        
        Returns:
            # Statistics
        """
        return {
            'state': self.stats.state.value,
            'connected_at': self.stats.connected_at.isoformat() if self.stats.connected_at else None,
            'uptime_seconds': self.get_connection_uptime(),
            'reconnect_attempts': self.stats.reconnect_attempts,
            'health_checks_passed': self.stats.health_checks_passed,
            'health_checks_failed': self.stats.health_checks_failed,
            'last_error': self.stats.last_error,
            'xray_pid': self._xray_pid
        }
    
    def set_log_callback(self, callback: Callable[[str], None]):
        """
        Установка callback для логирования.
        
        Args:
            callback: Функция для логов
        """
        self._log_callback = callback
    
    # ==========================================================================
    # ПРИВАТНЫЕ # METHODS - ПОДКЛЮЧЕНИЕ
    # ==========================================================================
    
    async def _connect(self):
        """Попытка подключения к VPN"""
        if self.stats.state == ConnectionState.CONNECTED:
            return
        
        self.stats.state = ConnectionState.CONNECTING
        self._log("🔄 Подключение к VPN...")
        
        try:
            # Запуск Xray
            config_file = Path.home() / "vpn-client-aggregator" / "config" / "config.json"
            
            if not config_file.exists():
                raise Exception("Файл конфигурации не найден")
            
            # Проверка Xray
            xray_path = self._find_xray()
            if not xray_path:
                raise Exception("Xray не найден")
            
            # Запуск процесса
            self._xray_process = subprocess.Popen(
                [xray_path, "run", "-c", str(config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            self._xray_pid = self._xray_process.pid
            
            self._log(f"Xray запущен (PID: {self._xray_pid})")
            
            # Ожидание запуска
            await asyncio.sleep(3)
            
            # Проверка процесса
            if self._xray_process.poll() is not None:
                # Процесс завершился
                stdout, stderr = self._xray_process.communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Неизвестная ошибка"
                raise Exception(f"Xray завершился с ошибкой: {error_msg}")
            
            # Успешное подключение
            self.stats.state = ConnectionState.CONNECTED
            self.stats.connected_at = datetime.now()
            self.stats.disconnected_at = None
            self.stats.last_error = None
            
            self._log("✅ VPN подключён")
            
            if self.on_connect:
                self.on_connect()
            
        except Exception as e:
            self.stats.state = ConnectionState.FAILED
            self.stats.last_error = str(e)
            self._log(f"❌ Ошибка подключения: {e}")
            
            if self.on_disconnect:
                self.on_disconnect()
    
    async def _disconnect(self):
        """Отключение от VPN"""
        self._log("⏹️ Отключение VPN...")
        
        # Остановка Xray процесса
        if self._xray_process:
            try:
                import os
                os.killpg(os.getpgid(self._xray_process.pid), 15)  # SIGTERM
                self._xray_process.wait(timeout=5)
            except:
                # Принудительная остановка
                try:
                    import os
                    os.killpg(os.getpgid(self._xray_process.pid), 9)  # SIGKILL
                except:
                    pass
        
        self._xray_process = None
        self._xray_pid = None
        
        # Обновление состояния
        self.stats.state = ConnectionState.DISCONNECTED
        self.stats.disconnected_at = datetime.now()
        
        if self.stats.connected_at:
            uptime = (self.stats.disconnected_at - self.stats.connected_at).total_seconds()
            self.stats.total_uptime_seconds += uptime
        
        self._log("VPN отключён")
        
        if self.on_disconnect:
            self.on_disconnect()
    
    # ==========================================================================
    # PRIVATE METHODS - MONITORING
    # ==========================================================================
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                
                if self.stats.state == ConnectionState.CONNECTED:
                    # Проверка подключения
                    is_healthy = await self._health_check()
                    
                    if not is_healthy:
                        self._consecutive_failures += 1
                        self._log(f"⚠️ Проверка не пройдена ({self._consecutive_failures})")
                        
                        # Если несколько проверок не пройдены - переподключение
                        if self._consecutive_failures >= 2:
                            await self._reconnect()
                    else:
                        self._consecutive_failures = 0
                        self.stats.health_checks_passed += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Ошибка мониторинга: {e}")
    
    async def _health_check(self) -> bool:
        """
        Проверка здоровья подключения.
        
        Returns:
            True если подключение активно
        """
        self._last_health_check = datetime.now()
        
        try:
            # 1. Проверка процесса Xray
            if not self._check_xray_process():
                return False
            
            # 2. Проверка локальной связности
            if self.config.check_local_connectivity:
                if not self._check_local_connectivity():
                    return False
            
            # 3. Проверка доступа в интернет через VPN
            if not await self._check_internet_access():
                return False
            
            return True
            
        except Exception as e:
            self.stats.last_error = str(e)
            self.stats.health_checks_failed += 1
            return False
    
    def _check_xray_process(self) -> bool:
        """Проверка процесса Xray"""
        if self._xray_pid is None:
            return False
        
        try:
            # Проверка существования процесса
            import os
            os.kill(self._xray_pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            self._log("⚠️ Процесс Xray не найден")
            return False
        except:
            return False
    
    def _check_local_connectivity(self) -> bool:
        """Проверка локальной связности (SOCKS прокси)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', 10808))
            sock.close()
            return result == 0
        except:
            return False
    
    async def _check_internet_access(self) -> bool:
        """Проверка доступа в интернет через VPN"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config.health_check_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.health_check_timeout_seconds),
                    proxy="http://127.0.0.1:10809"
                ) as response:
                    return response.status == 204
        except:
            return False
    
    # ==========================================================================
    # PRIVATE METHODS - RECONNECT
    # ==========================================================================
    
    async def _reconnect(self):
        """Переподключение к VPN"""
        async with self._reconnect_lock:
            if self.stats.reconnect_attempts >= self.config.max_reconnect_attempts:
                self._log("❌ Превышено максимальное количество попыток переподключения")
                self.stats.state = ConnectionState.FAILED
                return
            
            self.stats.state = ConnectionState.RECONNECTING
            self.stats.reconnect_attempts += 1
            self.stats.last_reconnect_at = datetime.now()
            
            self._log(f"🔄 Переподключение (попытка {self.stats.reconnect_attempts}/{self.config.max_reconnect_attempts})...")
            
            if self.config.notify_on_reconnect and self.on_reconnect:
                self.on_reconnect(self.stats.reconnect_attempts)
            
            # Отключение
            await self._disconnect()
            
            # Экспоненциальная задержка
            if self.config.exponential_backoff:
                delay = min(
                    self.config.reconnect_delay_seconds * (2 ** (self.stats.reconnect_attempts - 1)),
                    self.config.reconnect_delay_max_seconds
                )
            else:
                delay = self.config.reconnect_delay_seconds
            
            self._log(f"⏳ Пауза {delay} секунд перед переподключением...")
            await asyncio.sleep(delay)
            
            # Подключение
            await self._connect()
    
    # ==========================================================================
    # UTILITIES
    # ==========================================================================
    
    def _find_xray(self) -> Optional[str]:
        """
        Поиск исполняемого файла Xray.
        
        Returns:
            Путь к Xray или None
        """
        paths = [
            "/usr/local/bin/xray",
            "/usr/bin/xray",
            str(Path.home() / "bin" / "xray"),
            str(Path.home() / ".local" / "bin" / "xray"),
            "xray"
        ]
        
        for path in paths:
            try:
                result = subprocess.run(
                    ["which", path] if path != "xray" else ["command", "-v", "xray"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip() or path
            except:
                if Path(path).exists():
                    return path
        
        # Последняя попытка
        try:
            result = subprocess.run(["xray", "version"], capture_output=True)
            if result.returncode == 0:
                return "xray"
        except:
            pass
        
        return None
    
    def _log(self, message: str):
        """
        Логирование сообщения.
        
        Args:
            message: Сообщение
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self._log_callback:
            self._log_callback(log_message)
        else:
            print(log_message)
    
    def _format_uptime(self, seconds: float) -> str:
        """
        Форматирование времени бесперебойной работы.
        
        Args:
            seconds: Время в секундах
        
        Returns:
            Форматированная строка
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование ConnectionMonitor...")
    
    # Создание монитора
    monitor = ConnectionMonitor(MonitorConfig(
        enabled=True,
        max_reconnect_attempts=5,
        reconnect_delay_seconds=3,
        health_check_interval_seconds=10
    ))
    
    # Установка callback для логов
    def log_callback(message: str):
        print(f"   {message}")
    
    monitor.set_log_callback(log_callback)
    
    # Статистика
    print("\n📊 Начальная статистика:")
    stats = monitor.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Проверка поиска Xray
    print("\n🔍 Поиск Xray...")
    xray_path = monitor._find_xray()
    print(f"   Путь: {xray_path if xray_path else 'Не найден'}")
    
    # Форматирование uptime
    print("\n⏱️ Форматирование времени:")
    test_seconds = [60, 3661, 86400]
    for secs in test_seconds:
        print(f"   {secs} сек → {monitor._format_uptime(secs)}")
    
    print("\n✅ ConnectionMonitor готов к работе!")
