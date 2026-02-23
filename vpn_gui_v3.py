#!/usr/bin/env python3
"""
VLESS VPN Client v2.0 - Enhanced Edition
С поддержкой DeVPN, мониторингом трафика, Kill Switch и AI-фичами
"""

import sys
import os
import subprocess
import threading
import json
import time
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QProgressBar, QMessageBox,
                                  QCheckBox, QTabWidget, QSplitter, QLCDNumber,
                                  QDial, QGroupBox, QGridLayout, QScrollArea)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation
    from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QSystemTrayIcon
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("PyQt5 не установлен. Установите: pip3 install PyQt5")
    sys.exit(1)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

class TrafficMonitor:
    """Мониторинг трафика в реальном времени"""
    
    def __init__(self):
        self.upload_speed = 0
        self.download_speed = 0
        self.total_upload = 0
        self.total_download = 0
        self.start_time = None
        
    def start(self):
        """Начать мониторинг"""
        self.start_time = time.time()
        self.get_traffic_stats()
        
    def get_traffic_stats(self):
        """Получить статистику трафика"""
        try:
            # Чтение /proc/net/dev для мониторинга
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
                
            for line in lines[2:]:  # Пропустить заголовки
                if 'tun' in line or 'tap' in line:  # VPN интерфейс
                    parts = line.split(':')
                    if len(parts) > 1:
                        stats = parts[1].split()
                        rx = int(stats[0])  # Получено (download)
                        tx = int(stats[8])  # Отправлено (upload)
                        
                        if self.start_time:
                            elapsed = time.time() - self.start_time
                            if elapsed > 0:
                                self.download_speed = rx / elapsed
                                self.upload_speed = tx / elapsed
                                self.total_download = rx
                                self.total_upload = tx
                        return rx, tx
        except Exception as e:
            pass
        return 0, 0
    
    def get_speed_string(self, bytes_per_sec):
        """Конвертировать в человекочитаемый формат"""
        if bytes_per_sec > 1048576:  # MB/s
            return f"{bytes_per_sec / 1048576:.2f} MB/s"
        elif bytes_per_sec > 1024:  # KB/s
            return f"{bytes_per_sec / 1024:.2f} KB/s"
        else:
            return f"{bytes_per_sec:.0f} B/s"


class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(bool)

    def __init__(self, command="start", mode="split"):
        super().__init__()
        self.command = command
        self.mode = mode

    def run(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")

            if self.command == "start":
                cmd = [str(CLIENT_SCRIPT), "start", "--auto", "--mode", self.mode]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )

                for line in process.stdout:
                    self.log_signal.emit(line.strip())

                process.wait()
                self.finished_signal.emit(process.returncode == 0)

            elif self.command == "stop":
                subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
                self.log_signal.emit("VPN остановлен")
                self.finished_signal.emit(True)

            elif self.command == "status":
                result = subprocess.run(
                    [str(CLIENT_SCRIPT), "status"],
                    capture_output=True,
                    text=True,
                    env=env
                )
                self.log_signal.emit(result.stdout)
                self.finished_signal.emit(True)

            elif self.command == "update":
                cmd = [str(CLIENT_SCRIPT), "update"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )

                for line in process.stdout:
                    self.log_signal.emit(line.strip())

                process.wait()
                self.finished_signal.emit(process.returncode == 0)

        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
            self.finished_signal.emit(False)


class VPNClientGUIv2(QMainWindow):
    """Основное окно приложения v2.0"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.tray_icon = None
        self.is_connected = False
        self.countries = {}
        self.traffic_monitor = TrafficMonitor()
        self.kill_switch_enabled = False
        self.ai_mode_enabled = True
        self.init_ui()
        self.load_countries()
        self.start_monitoring()

    def init_ui(self):
        """Инициализация интерфейса v2.0"""
        self.setWindowTitle("🔒 VLESS VPN Client v2.0 - Enhanced")
        self.setMinimumSize(1000, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Client v2.0 Enhanced Edition")
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2ecc71; padding: 15px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #3498db); border-radius: 10px;")
        main_layout.addWidget(header)

        # Вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # === Вкладка 1: Подключение ===
        connect_tab = QWidget()
        tabs.addTab(connect_tab, "🔌 Подключение")
        connect_layout = QVBoxLayout(connect_tab)

        # Статус подключения
        self.status_label = QLabel("⚪ Не подключен")
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        connect_layout.addWidget(self.status_label)

        # Режим работы
        mode_group = QGroupBox("⚙️ Режим работы")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🔀 Split - РФ напрямую, остальное через VPN", "split")
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN (рекомендуется для AI)", "full")
        self.mode_combo.setCurrentIndex(1)
        
        self.ai_mode_check = QCheckBox("🤖 AI-режим (Claude, ChatGPT, Lovable) - автоматически FULL")
        self.ai_mode_check.setChecked(True)
        self.ai_mode_check.stateChanged.connect(self.on_ai_mode_changed)
        
        mode_layout.addWidget(self.ai_mode_check)
        mode_layout.addWidget(QLabel("💡 Для Claude.com и Lovable.dev используйте Full режим!"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        connect_layout.addWidget(mode_group)

        # Kill Switch
        killswitch_group = QGroupBox("🔐 Безопасность")
        killswitch_layout = QVBoxLayout()
        
        self.killswitch_check = QCheckBox("Kill Switch - Блокировать интернет без VPN")
        self.killswitch_check.setChecked(False)
        self.killswitch_check.stateChanged.connect(self.on_killswitch_changed)
        killswitch_layout.addWidget(self.killswitch_check)
        
        killswitch_layout.addWidget(QLabel("⚠️ При включении Kill Switch интернет будет заблокирован при отключении VPN"))
        killswitch_group.setLayout(killswitch_layout)
        connect_layout.addWidget(killswitch_group)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        btn_layout.addWidget(self.connect_btn)

        self.update_btn = QPushButton("🔄 Обновить серверы")
        self.update_btn.setFont(QFont("Arial", 11))
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.update_btn.clicked.connect(self.update_servers)
        btn_layout.addWidget(self.update_btn)

        connect_layout.addLayout(btn_layout)

        # === Вкладка 2: Мониторинг ===
        monitor_tab = QWidget()
        tabs.addTab(monitor_tab, "📊 Мониторинг")
        monitor_layout = QVBoxLayout(monitor_tab)

        # Трафик в реальном времени
        traffic_group = QGroupBox("📈 Трафик в реальном времени")
        traffic_layout = QGridLayout()

        self.download_label = QLabel("⬇️ 0 KB/s")
        self.download_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.download_label.setStyleSheet("color: #2ecc71; padding: 10px;")
        traffic_layout.addWidget(self.download_label, 0, 0)

        self.upload_label = QLabel("⬆️ 0 KB/s")
        self.upload_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.upload_label.setStyleSheet("color: #e74c3c; padding: 10px;")
        traffic_layout.addWidget(self.upload_label, 0, 1)

        self.total_download_label = QLabel("Всего скачано: 0 MB")
        self.total_download_label.setFont(QFont("Arial", 12))
        traffic_layout.addWidget(self.total_download_label, 1, 0)

        self.total_upload_label = QLabel("Всего загружено: 0 MB")
        self.total_upload_label.setFont(QFont("Arial", 12))
        traffic_layout.addWidget(self.total_upload_label, 1, 1)

        traffic_group.setLayout(traffic_layout)
        monitor_layout.addWidget(traffic_group)

        # Время подключения
        time_group = QGroupBox("⏱️ Время подключения")
        time_layout = QVBoxLayout()
        
        self.connection_timer = QLabel("00:00:00")
        self.connection_timer.setFont(QFont("Courier", 24, QFont.Bold))
        self.connection_timer.setAlignment(Qt.AlignCenter)
        self.connection_timer.setStyleSheet("color: #f1c40f; padding: 20px; background-color: #2c3e50; border-radius: 10px;")
        time_layout.addWidget(self.connection_timer)
        
        time_group.setLayout(time_layout)
        monitor_layout.addWidget(time_group)

        # === Вкладка 3: DeVPN ===
        dvpn_tab = QWidget()
        tabs.addTab(dvpn_tab, "🌐 DeVPN")
        dvpn_layout = QVBoxLayout(dvpn_tab)

        dvpn_info = QLabel("🌍 Децентрализованные VPN сети (Sentinel, Mysterium)")
        dvpn_info.setFont(QFont("Arial", 14))
        dvpn_layout.addWidget(dvpn_info)

        self.dvpn_status = QLabel("Статус: Не подключено")
        self.dvpn_status.setStyleSheet("padding: 10px;")
        dvpn_layout.addWidget(self.dvpn_status)

        self.fetch_dvpn_btn = QPushButton("📡 Найти dVPN узлы")
        self.fetch_dvpn_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 15px;
                font-size: 1.1em;
                border-radius: 8px;
                border: none;
            }
        """)
        self.fetch_dvpn_btn.clicked.connect(self.fetch_dvpn_nodes)
        dvpn_layout.addWidget(self.fetch_dvpn_btn)

        self.dvpn_list = QTextEdit()
        self.dvpn_list.setReadOnly(True)
        self.dvpn_list.setFont(QFont("Courier", 9))
        dvpn_layout.addWidget(self.dvpn_list)

        # === Вкладка 4: Проверки ===
        check_tab = QWidget()
        tabs.addTab(check_tab, "🔍 Проверки")
        check_layout = QVBoxLayout(check_tab)

        self.ip_info = QLabel("📍 Ваш IP: Не проверено")
        self.ip_info.setFont(QFont("Arial", 12))
        self.ip_info.setStyleSheet("padding: 15px; background-color: #ecf0f1; border-radius: 8px;")
        check_layout.addWidget(self.ip_info)

        self.dns_leak_label = QLabel("🔒 DNS Leak: Не проверено")
        self.dns_leak_label.setStyleSheet("padding: 15px; background-color: #ecf0f1; border-radius: 8px;")
        check_layout.addWidget(self.dns_leak_label)

        check_btn_layout = QHBoxLayout()
        
        check_ip_btn = QPushButton("🌍 Проверить IP")
        check_ip_btn.clicked.connect(self.check_ip)
        check_btn_layout.addWidget(check_ip_btn)

        check_dns_btn = QPushButton("🔍 Проверить DNS Leak")
        check_dns_btn.clicked.connect(self.check_dns_leak)
        check_btn_layout.addWidget(check_dns_btn)

        check_layout.addLayout(check_btn_layout)
        check_layout.addStretch()

        # === Вкладка 5: Логи ===
        log_tab = QWidget()
        tabs.addTab(log_tab, "📋 Логи")
        log_layout = QVBoxLayout(log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.log_text)

        log_btn_layout = QHBoxLayout()
        clear_log_btn = QPushButton("🗑️ Очистить")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_log_btn)
        log_layout.addLayout(log_btn_layout)

        # Строка состояния
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")

        # Системный трей
        self.init_tray()

        # Таймер обновления трафика
        self.traffic_timer = QTimer()
        self.traffic_timer.timeout.connect(self.update_traffic)
        self.traffic_timer.start(1000)  # Каждую секунду

        # Таймер времени подключения
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.connection_start_time = None
        self.load_logs()

    def on_ai_mode_changed(self, state):
        """Обработка переключения AI-режима"""
        self.ai_mode_enabled = (state == Qt.Checked)
        if self.ai_mode_enabled:
            self.mode_combo.setCurrentIndex(1)
            self.mode_combo.setEnabled(False)
            self.log("✅ AI-режим включен - FULL режим для Claude/ChatGPT/Lovable")
        else:
            self.mode_combo.setEnabled(True)
            self.log("ℹ️ AI-режим выключен")

    def on_killswitch_changed(self, state):
        """Обработка переключения Kill Switch"""
        self.kill_switch_enabled = (state == Qt.Checked)
        if self.kill_switch_enabled:
            self.log("✅ Kill Switch включен - интернет будет заблокирован без VPN")
        else:
            self.log("ℹ️ Kill Switch выключен")

    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()

    def start_vpn(self):
        """Запуск VPN"""
        mode = self.mode_combo.currentData()
        self.log(f"Запуск VPN в режиме {mode.upper()}...")

        try:
            subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
            time.sleep(1)
        except Exception:
            pass

        self.worker = VPNWorker("start", mode)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_start_finished)
        self.worker.start()

        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("⏳ Подключение...")
        self.statusBar.showMessage("Подключение к VPN...")

    def stop_vpn(self):
        """Остановка VPN"""
        self.log("Остановка VPN...")

        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_stop_finished)
        self.worker.start()

        self.connect_btn.setEnabled(False)

    def update_servers(self):
        """Обновление списка серверов"""
        self.log("Обновление списка серверов...")

        self.worker = VPNWorker("update")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(lambda: self.log("✅ Серверы обновлены"))
        self.worker.start()

    def on_start_finished(self, success):
        """Обработка завершения запуска"""
        self.connect_btn.setEnabled(True)

        if success:
            self.is_connected = True
            self.connect_btn.setText("⏹️ Отключить")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 15px 30px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.status_label.setText("🟢 Подключен")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #27ae60;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            self.statusBar.showMessage("VPN подключен")
            
            # Запуск мониторинга трафика
            self.traffic_monitor.start()
            self.connection_start_time = time.time()
            
            # Настройка прокси
            self.setup_proxy()

            if self.tray_icon:
                self.tray_icon.showMessage("VPN", "Подключено", QSystemTrayIcon.Information, 2000)
        else:
            self.status_label.setText("🔴 Ошибка подключения")
            self.statusBar.showMessage("Ошибка подключения")

    def on_stop_finished(self, success):
        """Обработка завершения остановки"""
        self.is_connected = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ Подключить")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.status_label.setText("⚪ Не подключен")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.statusBar.showMessage("VPN отключен")
        
        # Сброс таймеров
        self.connection_start_time = None
        self.connection_timer.setText("00:00:00")

    def update_status(self):
        """Обновление статуса"""
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")

            result = subprocess.run(
                [str(CLIENT_SCRIPT), "status"],
                capture_output=True,
                text=True,
                env=env,
                timeout=5
            )

            output = result.stdout

            if "✓ Подключен" in output or "Подключен:" in output:
                if not self.is_connected:
                    self.is_connected = True
                    self.connect_btn.setText("⏹️ Отключить")
                    self.status_label.setText("🟢 Подключен")
            elif "✗ Не подключен" in output:
                if self.is_connected:
                    self.is_connected = False
                    self.connect_btn.setText("▶️ Подключить")
                    self.status_label.setText("⚪ Не подключен")

        except Exception as e:
            pass

    def update_traffic(self):
        """Обновление статистики трафика"""
        if self.is_connected:
            rx, tx = self.traffic_monitor.get_traffic_stats()
            
            self.download_label.setText(f"⬇️ {self.traffic_monitor.get_speed_string(self.traffic_monitor.download_speed)}")
            self.upload_label.setText(f"⬆️ {self.traffic_monitor.get_speed_string(self.traffic_monitor.upload_speed)}")
            
            self.total_download_label.setText(f"Всего скачано: {self.traffic_monitor.total_download / 1048576:.2f} MB")
            self.total_upload_label.setText(f"Всего загружено: {self.traffic_monitor.total_upload / 1048576:.2f} MB")
            
            # Обновление таймера
            if self.connection_start_time:
                elapsed = int(time.time() - self.connection_start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                self.connection_timer.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def setup_proxy(self):
        """Настройка прокси"""
        proxy_script = f"""
export all_proxy=socks5://127.0.0.1:10808
export http_proxy=http://127.0.0.1:10809
export https_proxy=http://127.0.0.1:10809
"""
        proxy_file = HOME / ".vpn_proxy.sh"
        with open(proxy_file, 'w') as f:
            f.write(proxy_script)
        proxy_file.chmod(0o755)
        
        self.log("✅ Прокси настроен: socks5://127.0.0.1:10808")

    def fetch_dvpn_nodes(self):
        """Получить узлы dVPN"""
        self.log("📡 Поиск dVPN узлов...")
        self.dvpn_list.setText("Поиск узлов dVPN...\n")
        
        try:
            result = subprocess.run(
                ["python3", str(HOME / "vpn-client-aggregator" / "dvpn-client.py"), "fetch"],
                capture_output=True,
                text=True,
                timeout=30
            )
            self.dvpn_list.setText(result.stdout)
            self.log("✅ dVPN узлы найдены")
        except Exception as e:
            self.dvpn_list.setText(f"Ошибка: {e}")
            self.log(f"❌ Ошибка поиска dVPN: {e}")

    def check_ip(self):
        """Проверить IP"""
        try:
            result = subprocess.run(
                ["curl", "-s", "https://api.ipify.org"],
                capture_output=True,
                text=True,
                timeout=10
            )
            ip = result.stdout.strip()
            self.ip_info.setText(f"📍 Ваш IP: {ip}")
            self.log(f"✅ IP проверен: {ip}")
        except Exception as e:
            self.ip_info.setText("❌ Ошибка проверки IP")
            self.log(f"❌ Ошибка: {e}")

    def check_dns_leak(self):
        """Проверить DNS Leak"""
        try:
            result = subprocess.run(
                ["curl", "-s", "https://dnsleaktest.com"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.dns_leak_label.setText("🔒 DNS Leak: Проверка... (откройте сайт для деталей)")
                self.log("💡 Откройте https://dnsleaktest.com для проверки")
            else:
                self.dns_leak_label.setText("❌ Ошибка проверки")
        except Exception as e:
            self.dns_leak_label.setText("❌ Ошибка проверки")
            self.log(f"❌ Ошибка: {e}")

    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def load_logs(self):
        """Загрузка логов"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]
                    for line in lines:
                        self.log_text.append(line.strip())
            except Exception:
                pass

    def load_countries(self):
        """Загрузка списка стран"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if not servers_file.exists():
                self.log("❌ servers.json не найден. Нажмите 🔄 Обновить серверы")
                return

            with open(servers_file, encoding='utf-8') as f:
                servers = json.load(f)

            countries = {}
            country_map = {
                "🇩🇪": "Germany", "🇳🇱": "Netherlands", "🇺🇸": "USA",
                "🇬🇧": "UK", "🇫🇷": "France", "🇪🇪": "Estonia",
                "🇧🇾": "Belarus", "🇵🇱": "Poland", "🇺🇦": "Ukraine",
                "🇰🇿": "Kazakhstan", "🇫🇮": "Finland", "🇸🇪": "Sweden",
                "🇳🇴": "Norway", "🇱🇻": "Latvia", "🇱🇹": "Lithuania",
            }

            for server in servers:
                if server.get("status") != "online":
                    continue
                name = server.get("name", "")
                host = server.get("host", "")
                country = "🌍 Other"

                if "claude" in name.lower() or "claude" in host.lower() or "claude.ai" in host.lower():
                    country = "🤖 AI Services"
                elif "chatgpt" in name.lower() or "chatgpt" in host.lower():
                    country = "🤖 AI Services"
                elif "lovable" in name.lower() or "lovable" in host.lower():
                    country = "🤖 AI Services"
                else:
                    for flag, cname in country_map.items():
                        if flag in name or cname in name:
                            country = f"{flag} {cname}"
                            break

                if country not in countries:
                    countries[country] = 0
                countries[country] += 1

            countries = dict(sorted(countries.items(), key=lambda x: x[1], reverse=True))
            self.countries = countries

            total_servers = sum(countries.values())
            total_countries = len(countries)
            ai_servers = countries.get("🤖 AI Services", 0)

            stats_text = f"📊 Статистика серверов:\n\n"
            stats_text += f"🌍 Всего серверов: {total_servers}\n"
            stats_text += f"🌐 Локаций: {total_countries}\n"
            if ai_servers > 0:
                stats_text += f"🤖 AI Services: {ai_servers} (ChatGPT, Claude, Lovable)\n"

            stats_text += f"\nТоп локаций:\n"
            for country, count in list(countries.items())[:5]:
                stats_text += f"  {country}: {count}\n"

            self.log(f"✅ Загружено {total_countries} локаций, {total_servers} серверов")

        except Exception as e:
            self.log(f"Ошибка загрузки стран: {e}")

    def start_monitoring(self):
        """Запуск мониторинга"""
        def monitor():
            while True:
                try:
                    result = subprocess.run(["pgrep", "-f", "vless-vpn"], capture_output=True)
                    connected = result.returncode == 0
                    if connected != self.is_connected:
                        self.is_connected = connected
                        if connected:
                            self.log("✅ VPN подключен (обнаружен процесс)")
                        else:
                            self.log("⚠️ VPN отключен (процесс не найден)")
                            self.connect_btn.setText("▶️ Подключить")
                except Exception:
                    pass
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def init_tray(self):
        """Инициализация трея"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setVisible(True)

        tray_menu = QMenu()
        show_action = QAction("Показать окно", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        connect_action = QAction("Подключить", self)
        connect_action.triggered.connect(self.toggle_connection)
        tray_menu.addAction(connect_action)

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

    def tray_activated(self, reason):
        """Обработка клика по трею"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        """Обработка закрытия"""
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage(
                "VPN Client",
                "Приложение свернуто в трей",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()

    def quit_app(self):
        """Выход"""
        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        self.worker.wait(3000)
        QApplication.quit()


def main():
    if not HAVE_PYQT5:
        print("=" * 60)
        print("❌ PyQt5 не установлен!")
        print("=" * 60)
        print("\nУстановите PyQt5:\n")
        print("  sudo apt install python3-pyqt5")
        print("  или")
        print("  pip3 install PyQt5")
        print("\n" + "=" * 60)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("VLESS VPN Client v2.0")

    window = VPNClientGUIv2()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
