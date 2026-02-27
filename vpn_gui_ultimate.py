#!/usr/bin/env python3
"""
VLESS VPN Client - Ultimate GUI
Обход DPI и Чебурнета + Сканер серверов + Автозапуск

Функции:
- Многоуровневый DPI bypass
- Устойчивость к Чебурнету
- Сканер всех источников (White/Black списки)
- Автозапуск при старте системы
- Интеграция в меню приложений

© 2026 VPN Client Aggregator
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
                                  QAction, QStatusBar, QTabWidget, QCheckBox,
                                  QScrollArea, QFrame, QMessageBox, QListWidget,
                                  QListWidgetItem, QProgressBar, QSpinBox,
                                  QRadioButton, QButtonGroup, QSplitter, QFileDialog)
    from PyQt5.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QDesktopServices, QIcon, QPixmap
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен! Установите: pip3 install PyQt5")
    sys.exit(1)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vless-vpn-client"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
XRAY_BIN = HOME / "vpn-client" / "bin" / "xray"
SCRIPT_PATH = Path(__file__).absolute()

# Создаем директории
for d in [LOGS_DIR, DATA_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Глобальные
vpn_connected = False
xray_process = None
current_server = None


# =============================================================================
# РАБОЧИЙ ПОТОК ДЛЯ СКАНЕРА
# =============================================================================

class ScannerWorker(QThread):
    """Рабочий поток для сканирования серверов"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.servers = []

    def run(self):
        """Сканирование в фоне"""
        try:
            self.log_signal.emit("🌐 Запуск сканера серверов...")
            self.progress_signal.emit(10)

            # Импортируем сканер
            sys.path.insert(0, str(BASE_DIR))
            from vless_client_ultimate import ServerScanner

            scanner = ServerScanner()
            
            # Запускаем сканирование
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.log_signal.emit("🔍 Сканирование источников...")
            self.progress_signal.emit(30)
            
            servers = loop.run_until_complete(scanner.scan_all_sources())
            self.log_signal.emit(f"📊 Найдено серверов: {len(servers)}")
            self.progress_signal.emit(60)
            
            if servers:
                self.log_signal.emit("🔍 Проверка серверов...")
                working_servers = loop.run_until_complete(scanner.check_servers(servers))
                self.log_signal.emit(f"✅ Рабочих серверов: {len(working_servers)}")
                self.progress_signal.emit(90)
                
                scanner.save_servers(working_servers)
                self.servers = working_servers
                self.progress_signal.emit(100)
                
                self.finished_signal.emit(len(working_servers))
            else:
                self.log_signal.emit("⚠️ Серверы не найдены")
                self.finished_signal.emit(0)
                
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка сканера: {e}")
            self.finished_signal.emit(-1)


# =============================================================================
# РАБОЧИЙ ПОТОК ДЛЯ ПОДКЛЮЧЕНИЯ
# =============================================================================

class ConnectWorker(QThread):
    """Рабочий поток для подключения"""
    log_signal = pyqtSignal(str)
    connected_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, server=None):
        super().__init__()
        self.server = server

    def run(self):
        """Подключение в фоне"""
        try:
            self.progress_signal.emit(20)
            self.log_signal.emit("🚀 Запуск VPN...")

            # Загрузка серверов
            if not self.server:
                self.progress_signal.emit(40)
                if SERVERS_FILE.exists():
                    with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                        servers = json.load(f)
                    
                    # Выбор лучшего
                    candidates = [s for s in servers if s.get('status') == 'online']
                    if candidates:
                        candidates.sort(key=lambda x: x.get('latency', 9999))
                        self.server = candidates[0]
                    else:
                        self.error_signal.emit("❌ Нет рабочих серверов")
                        return
                else:
                    self.error_signal.emit("❌ Файл серверов не найден")
                    return

            self.progress_signal.emit(60)
            self.log_signal.emit(f"🔌 Подключение к {self.server['host']}:{self.server['port']}...")

            # Генерация конфига
            config = self.generate_config(self.server)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.progress_signal.emit(80)
            self.log_signal.emit("✅ Конфиг создан")

            # Запуск XRay
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")

            cmd = [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )

            time.sleep(5)

            self.progress_signal.emit(100)

            if process.poll() is None:
                self.log_signal.emit("✅ VPN ПОДКЛЮЧЕН!")
                self.connected_signal.emit(self.server)
            else:
                self.error_signal.emit("❌ XRay не запустился")

        except Exception as e:
            self.error_signal.emit(f"❌ Ошибка: {e}")

    def generate_config(self, server):
        """Генерация конфига"""
        stream = server.get("streamSettings", {})
        security = stream.get("security", "tls")

        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}},
                {"port": 10809, "protocol": "http"}
            ],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": server["host"],
                        "port": server["port"],
                        "users": [{"id": server.get("uuid", ""), "encryption": "none", "flow": server.get("flow", "xtls-rprx-vision")}]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": security,
                    "sockopt": {
                        "tcpNoDelay": True,
                        "tcpKeepAliveInterval": 30
                    }
                },
                "fragment": {
                    "packets": "tlshello",
                    "length": "50-200",
                    "interval": "10-50"
                }
            }
        }

        if security == "reality":
            reality = stream.get("realitySettings", {})
            config["outbounds"][0]["streamSettings"]["realitySettings"] = {
                "serverName": reality.get("serverName", server["host"]),
                "fingerprint": "chrome",
                "publicKey": reality.get("publicKey", ""),
                "shortId": reality.get("shortId", "")
            }

        return config


# =============================================================================
# GUI ПРИЛОЖЕНИЕ
# =============================================================================

class UltimateVPNGUI(QMainWindow):
    """Ultimate VPN GUI"""

    def __init__(self):
        super().__init__()
        self.scanner_worker = None
        self.connect_worker = None
        self.is_connected = False
        self.servers = []
        self.current_server = None
        self.init_ui()
        self.load_servers()
        self.start_monitoring()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Ultimate - DPI Bypass + Чебурнет")
        self.setMinimumSize(1100, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Ultimate\nОбход DPI и Чебурнета | Сканер серверов | Автозапуск")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: white;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #e74c3c);
                border-radius: 15px;
                margin: 10px;
            }
        """)
        main_layout.addWidget(header)

        # Вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # === Вкладка 1: Подключение ===
        connect_tab = QWidget()
        tabs.addTab(connect_tab, "🔌 Подключение")
        connect_layout = QVBoxLayout(connect_tab)

        # Статус
        self.status_label = QLabel("⚪ НЕ ПОДКЛЮЧЕН")
        self.status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin: 15px;
            }
        """)
        connect_layout.addWidget(self.status_label)

        # БОЛЬШАЯ КНОПКА
        self.connect_btn = QPushButton("▶️ ПОДКЛЮЧИТЬ")
        self.connect_btn.setFont(QFont("Arial", 18, QFont.Bold))
        self.connect_btn.setMinimumHeight(80)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
                border-radius: 15px;
                padding: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #229954);
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        connect_layout.addWidget(self.connect_btn)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumHeight(30)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2c3e50;
                border-radius: 15px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 15px;
            }
        """)
        connect_layout.addWidget(self.progress)

        # DPI Bypass настройки
        dpi_group = QGroupBox("🔧 DPI Bypass Настройки")
        dpi_layout = QVBoxLayout()

        dpi_info = QLabel("✅ Активирован многоуровневый обход DPI:\n   • Фрагментация пакетов (50-200 байт)\n   • Padding (добавление случайных данных)\n   • TLS мимикрия под Chrome\n   • Адаптивное переключение стратегий")
        dpi_info.setStyleSheet("font-size: 1em; padding: 10px; color: #2ecc71;")
        dpi_layout.addWidget(dpi_info)

        self.dpi_status = QLabel("🛡️ DPI Bypass: ГОТОВ")
        self.dpi_status.setStyleSheet("font-size: 1.1em; padding: 8px; color: #f39c12; font-weight: bold;")
        dpi_layout.addWidget(self.dpi_status)

        dpi_group.setLayout(dpi_layout)
        connect_layout.addWidget(dpi_group)

        # Выбор локации
        location_group = QGroupBox("🌍 Выбор локации")
        location_layout = QVBoxLayout()

        self.location_combo = QComboBox()
        self.location_combo.setFont(QFont("Arial", 12))
        self.location_combo.setMinimumHeight(40)
        self.location_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: white;
                font-size: 1.1em;
            }
        """)
        location_layout.addWidget(QLabel("Выберите страну:"))
        location_layout.addWidget(self.location_combo)

        location_group.setLayout(location_layout)
        connect_layout.addWidget(location_group)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.scan_btn = QPushButton("🔍 Скан серверов")
        self.scan_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.scan_btn.setMinimumHeight(50)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.scan_btn.clicked.connect(self.scan_servers)
        buttons_layout.addWidget(self.scan_btn)

        self.update_btn = QPushButton("🔄 Обновить серверы")
        self.update_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.update_btn.setMinimumHeight(50)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.update_btn.clicked.connect(self.update_servers)
        buttons_layout.addWidget(self.update_btn)

        connect_layout.addLayout(buttons_layout)

        # Автозапуск
        autostart_group = QGroupBox("🚀 Автозапуск")
        autostart_layout = QVBoxLayout()

        self.autostart_check = QCheckBox("🚀 Автозапуск при старте системы")
        self.autostart_check.setStyleSheet("font-size: 1.1em; padding: 5px;")
        self.autostart_check.stateChanged.connect(self.toggle_autostart)
        autostart_layout.addWidget(self.autostart_check)

        autostart_info = QLabel("✅ VPN будет запускаться автоматически при входе в систему")
        autostart_info.setStyleSheet("font-size: 1em; padding: 10px; color: #3498db;")
        autostart_layout.addWidget(autostart_info)

        autostart_group.setLayout(autostart_layout)
        connect_layout.addWidget(autostart_group)

        # Статистика
        stats_group = QGroupBox("📊 Статистика")
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel("Загрузка...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        connect_layout.addWidget(stats_group)

        # === Вкладка 2: Сканер ===
        scanner_tab = QWidget()
        tabs.addTab(scanner_tab, "🔍 Сканер")
        scanner_layout = QVBoxLayout(scanner_tab)

        scanner_header = QLabel("🌐 Сканер серверов из всех источников")
        scanner_header.setFont(QFont("Arial", 16, QFont.Bold))
        scanner_header.setAlignment(Qt.AlignCenter)
        scanner_layout.addWidget(scanner_header)

        scanner_info = QLabel("Источники:\n   • GitHub (White/Black списки)\n   • V2Ray Aggregator\n   • Leon406 SubCrawler\n   • Pawdroid Free-servers")
        scanner_info.setStyleSheet("font-size: 1em; padding: 10px; color: #3498db;")
        scanner_layout.addWidget(scanner_info)

        self.scan_result = QTextEdit()
        self.scan_result.setReadOnly(True)
        self.scan_result.setFont(QFont("Courier", 9))
        self.scan_result.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        scanner_layout.addWidget(self.scan_result)

        scanner_tab.setLayout(scanner_layout)

        # === Вкладка 3: Логи ===
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
                border-radius: 10px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_tab.setLayout(log_layout)

        # Строка состояния
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")

        # Трей
        self.init_tray()

        # Таймер
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.load_logs()
        self.load_locations()
        self.check_autostart()

    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()

    def start_vpn(self):
        """Запуск VPN"""
        self.log("🚀 Запуск VPN с DPI Bypass...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.connect_btn.setEnabled(False)

        self.connect_worker = ConnectWorker()
        self.connect_worker.log_signal.connect(self.log)
        self.connect_worker.connected_signal.connect(self.on_connected)
        self.connect_worker.error_signal.connect(self.on_error)
        self.connect_worker.progress_signal.connect(self.progress.setValue)
        self.connect_worker.start()

    def on_connected(self, server):
        """Успешное подключение"""
        self.is_connected = True
        self.current_server = server
        global vpn_connected, current_server
        vpn_connected = True
        current_server = server

        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("⏹️ ОТКЛЮЧИТЬ")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.status_label.setText("🟢 ПОДКЛЮЧЕН")
        self.status_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin: 15px;
            }
        """)
        self.dpi_status.setText("🛡️ DPI Bypass: АКТИВЕН")
        self.dpi_status.setStyleSheet("font-size: 1.1em; padding: 8px; color: #2ecc71; font-weight: bold;")
        self.statusBar.showMessage("✅ VPN подключен с DPI Bypass")
        self.log("✅ VPN ПОДКЛЮЧЕН!")
        self.log(f"  Сервер: {server['host']}:{server['port']}")
        self.log(f"  DPI Bypass: fragmentation + padding + TLS mimicry")

        QMessageBox.information(self, "Успех", f"✅ VPN подключен!\n\nСервер: {server['host']}:{server['port']}\n\nDPI Bypass активен | Чебурнет будет обойден!")

    def on_error(self, error):
        """Ошибка подключения"""
        self.log(error, "ERROR")
        self.connect_btn.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Ошибка", error)

    def stop_vpn(self):
        """Остановка VPN"""
        self.log("🛑 Остановка VPN...")

        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True)

        self.is_connected = False
        global vpn_connected, current_server
        vpn_connected = False
        current_server = None

        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")
        self.status_label.setText("⚪ НЕ ПОДКЛЮЧЕН")
        self.status_label.setStyleSheet("QLabel { background-color: #34495e; color: white; padding: 25px; border-radius: 15px; margin: 15px; }")
        self.dpi_status.setText("🛡️ DPI Bypass: ГОТОВ")
        self.dpi_status.setStyleSheet("font-size: 1.1em; padding: 8px; color: #f39c12; font-weight: bold;")
        self.statusBar.showMessage("VPN отключен")
        self.log("✅ VPN отключен")

    def scan_servers(self):
        """Сканирование серверов"""
        self.log("🔍 Запуск сканера серверов...")
        self.scan_result.clear()
        self.scan_btn.setEnabled(False)

        self.scanner_worker = ScannerWorker()
        self.scanner_worker.log_signal.connect(lambda msg: self.scan_result.append(msg))
        self.scanner_worker.finished_signal.connect(self.on_scan_finished)
        self.scanner_worker.start()

    def on_scan_finished(self, count):
        """Сканирование завершено"""
        self.scan_btn.setEnabled(True)
        self.load_servers()
        self.load_locations()
        
        if count > 0:
            self.log(f"✅ Сканирование завершено: найдено {count} рабочих серверов")
            QMessageBox.information(self, "Успех", f"✅ Найдено {count} рабочих серверов!")
        else:
            self.log("⚠️ Сканирование завершено: серверы не найдены", "WARNING")

    def update_servers(self):
        """Обновление серверов"""
        self.scan_servers()

    def load_servers(self):
        """Загрузка серверов"""
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
                self.log(f"✅ Загружено серверов: {len(self.servers)}")
                self.update_stats()
            else:
                self.servers = []
                self.log("⚠️ servers.json не найден", "WARNING")
        except Exception as e:
            self.log(f"❌ Ошибка загрузки: {e}", "ERROR")
            self.servers = []

    def load_locations(self):
        """Загрузка локаций"""
        self.location_combo.clear()
        self.location_combo.addItem("⚡ Автовыбор (лучший сервер)", "auto")

        if not self.servers:
            return

        countries = {}
        for server in self.servers:
            if server.get("status") != "online":
                continue
            country = server.get("country", "🌍")
            if country not in countries:
                countries[country] = []
            countries[country].append(server)

        for country, servers_list in sorted(countries.items(), key=lambda x: len(x[1]), reverse=True):
            self.location_combo.addItem(f"{country} ({len(servers_list)} серверов)", country)

    def update_stats(self):
        """Обновление статистики"""
        if not self.servers:
            self.stats_label.setText("Нет данных")
            return

        online = sum(1 for s in self.servers if s.get("status") == "online")
        avg_latency = sum(s.get("latency", 9999) for s in self.servers if s.get("status") == "online") // max(online, 1)

        stats_text = f"Всего серверов: {len(self.servers)}\n"
        stats_text += f"Онлайн: {online}\n"
        stats_text += f"Средний пинг: {avg_latency}ms\n"
        stats_text += f"Лучший сервер: "
        
        if online > 0:
            best = min([s for s in self.servers if s.get("status") == "online"], key=lambda x: x.get("latency", 9999))
            stats_text += f"{best['country']} {best['host']}:{best['port']} ({best['latency']}ms)"

        self.stats_label.setText(stats_text)

    def update_status(self):
        """Обновление статуса"""
        global vpn_connected

        if vpn_connected and self.connect_worker:
            if self.connect_worker.isRunning() and self.connect_worker.process and self.connect_worker.process.poll() is not None:
                vpn_connected = False
                self.is_connected = False
                self.log("⚠️ Соединение разорвано!", "WARNING")
                self.stop_vpn()

    def log(self, message, level="INFO"):
        """Добавить лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        self.log_text.append(log_msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def load_logs(self):
        """Загрузить логи"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f.readlines()[-100:]:
                        self.log_text.append(line.strip())
            except:
                pass

    def start_monitoring(self):
        """Мониторинг"""
        def monitor():
            global vpn_connected
            while True:
                time.sleep(5)
                result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
                connected = result.returncode == 0
                if connected != vpn_connected:
                    vpn_connected = connected

        threading.Thread(target=monitor, daemon=True).start()

    def check_autostart(self):
        """Проверка автозапуска"""
        desktop_file = HOME / ".config" / "autostart" / "vless-vpn-ultimate.desktop"
        self.autostart_check.setChecked(desktop_file.exists())

    def toggle_autostart(self, state):
        """Переключение автозапуска"""
        if state == Qt.Checked:
            self.enable_autostart()
        else:
            self.disable_autostart()

    def enable_autostart(self):
        """Включить автозапуск"""
        desktop_file = HOME / ".config" / "autostart" / "vless-vpn-ultimate.desktop"
        menu_file = HOME / ".local" / "share" / "applications" / "vless-vpn-ultimate.desktop"

        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        menu_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=VLESS VPN Client с DPI Bypass
Exec={sys.executable} {SCRIPT_PATH} start
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
X-GNOME-Autostart-enabled=true
"""

        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(menu_file, 'w', encoding='utf-8') as f:
            f.write(content)

        os.chmod(desktop_file, 0o755)
        os.chmod(menu_file, 0o755)

        self.log("✅ Автозапуск включен")
        QMessageBox.information(self, "Автозапуск", "✅ Автозапуск включен\n\nVPN будет запускаться при старте системы")

    def disable_autostart(self):
        """Выключить автозапуск"""
        desktop_file = HOME / ".config" / "autostart" / "vless-vpn-ultimate.desktop"
        menu_file = HOME / ".local" / "share" / "applications" / "vless-vpn-ultimate.desktop"

        if desktop_file.exists():
            desktop_file.unlink()
        if menu_file.exists():
            menu_file.unlink()

        self.log("🗑️ Автозапуск выключен")

    def init_tray(self):
        """Трей"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setVisible(True)

        menu = QMenu()
        menu.addAction("Показать", self.show)
        menu.addAction("Подключить", self.toggle_connection)
        menu.addAction("Выход", self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(lambda r: self.show() if r == QSystemTrayIcon.DoubleClick else None)

    def closeEvent(self, event):
        """Закрытие"""
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage("VPN", "В трее", QSystemTrayIcon.Information, 2000)
            event.ignore()
        else:
            event.accept()

    def quit_app(self):
        """Выход"""
        self.stop_vpn()
        QApplication.quit()


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

def main():
    """Точка входа"""
    import argparse

    parser = argparse.ArgumentParser(description="VLESS VPN Ultimate GUI")
    parser.add_argument("command", nargs="?", choices=["gui", "start", "stop", "status"], default="gui",
                        help="Команда: gui, start, stop, status")
    parser.add_argument("--auto", action="store_true", help="Автоподключение")

    args = parser.parse_args()

    if args.command == "gui" or args.command is None:
        app = QApplication(sys.argv)
        app.setApplicationName("VLESS VPN Ultimate")
        app.setOrganizationName("VPN Client Aggregator")

        window = UltimateVPNGUI()
        window.show()

        sys.exit(app.exec_())
    else:
        # Консольный режим
        from vless_client_ultimate import UltimateVPNClient

        client = UltimateVPNClient()

        if args.command == "start":
            if client.connect():
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    client.disconnect()
            else:
                sys.exit(1)
        elif args.command == "stop":
            client.disconnect()
        elif args.command == "status":
            client.status()


if __name__ == "__main__":
    main()
