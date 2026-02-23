#!/usr/bin/env python3
"""
VLESS VPN Client GUI v2.0
С выбором локаций и полным управлением
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QListWidget, QListWidgetItem,
                                  QMessageBox, QTabWidget, QProgressBar, QCheckBox)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
    from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QDesktopServices
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен! Установите: sudo apt-get install python3-pyqt5")
    sys.exit(1)

# Пробуем импортировать Flask для веб-интерфейса
try:
    import threading
    import http.server
    import socketserver
    import json
    from urllib.parse import urlparse
    HAVE_FLASK = False  # Используем встроенный HTTP сервер
except ImportError:
    HAVE_FLASK = False

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"
CONTROLLER_SCRIPT = HOME / "/vpn-client-aggregator/vpn-controller.py"


class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, command="start", mode="split", country=None):
        super().__init__()
        self.command = command
        self.mode = mode
        self.country = country
    
    def run(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
            
            if self.command == "start":
                # Остановить старые процессы
                subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
                subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
                time.sleep(1)
                
                cmd = [str(CLIENT_SCRIPT), "start", "--auto", "--mode", self.mode]
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, env=env
                )
                
                for line in process.stdout:
                    self.log_signal.emit(line.strip())
                
                process.wait()
                self.finished_signal.emit(process.returncode == 0)
                
            elif self.command == "stop":
                subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
                subprocess.run(["pkill", "-f", "xray"], capture_output=True)
                self.log_signal.emit("VPN остановлен")
                self.finished_signal.emit(True)
                
            elif self.command == "status":
                result = subprocess.run(
                    [str(CLIENT_SCRIPT), "status"],
                    capture_output=True, text=True, env=env
                )
                self.log_signal.emit(result.stdout)
                self.finished_signal.emit(True)
                
            elif self.command == "update":
                cmd = [str(CLIENT_SCRIPT), "update"]
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, env=env
                )
                for line in process.stdout:
                    self.log_signal.emit(line.strip())
                process.wait()
                self.finished_signal.emit(process.returncode == 0)
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
            self.finished_signal.emit(False)


class VPNClientGUI(QMainWindow):
    """Основное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.tray_icon = None
        self.is_connected = False
        self.countries = {}
        self.init_ui()
        self.load_countries()
        self.start_monitoring()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client")
        self.setMinimumSize(900, 700)
        
        # Центральное окно
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        header = QLabel("🔒 VLESS VPN Client v2.0")
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2ecc71; padding: 15px; background-color: #2c3e50; border-radius: 10px;")
        main_layout.addWidget(header)
        
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
        main_layout.addWidget(self.status_label)
        
        # Вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Вкладка "Подключение"
        connect_tab = QWidget()
        tabs.addTab(connect_tab, "🔌 Подключение")
        connect_layout = QVBoxLayout(connect_tab)
        
        # Выбор локации
        location_group = QGroupBox("🌍 Выбор локации")
        location_layout = QVBoxLayout()
        
        self.country_combo = QComboBox()
        self.country_combo.setFont(QFont("Arial", 12))
        self.country_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
        """)
        location_layout.addWidget(self.country_combo)
        
        # Список серверов
        self.server_list = QListWidget()
        self.server_list.setFont(QFont("Courier", 10))
        self.server_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.server_list.itemDoubleClicked.connect(self.on_server_double_click)
        location_layout.addWidget(QLabel("Дважды кликните на сервер для подключения:"))
        location_layout.addWidget(self.server_list)
        
        location_group.setLayout(location_layout)
        connect_layout.addWidget(location_group)
        
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
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        btn_layout.addWidget(self.connect_btn)
        
        self.update_btn = QPushButton("🔄 Обновить")
        self.update_btn.setFont(QFont("Arial", 11))
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.update_btn.clicked.connect(self.update_servers)
        btn_layout.addWidget(self.update_btn)
        
        connect_layout.addLayout(btn_layout)
        
        # Вкладка "Логи"
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
        
        # Кнопки логов
        log_btn_layout = QHBoxLayout()
        clear_log_btn = QPushButton("🗑️ Очистить")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("💾 Сохранить")
        save_log_btn.clicked.connect(self.save_log)
        log_btn_layout.addWidget(save_log_btn)
        
        log_layout.addLayout(log_btn_layout)
        
        # Вкладка "Настройки"
        settings_tab = QWidget()
        tabs.addTab(settings_tab, "⚙️ Настройки")
        settings_layout = QVBoxLayout(settings_tab)
        
        # Информация
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Версия: 2.0"))
        info_layout.addWidget(QLabel("Протокол: VLESS-Reality"))
        info_layout.addWidget(QLabel("Порт SOCKS5: 10808"))
        info_layout.addWidget(QLabel("Порт HTTP: 10809"))
        info_layout.addWidget(QLabel("Режим: Split (РФ напрямую)"))
        info_group.setLayout(info_layout)
        settings_layout.addWidget(info_group)
        
        settings_layout.addStretch()
        
        # Строка состояния
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
        
        # Системный трей
        self.init_tray()
        
        # Таймер обновления статуса
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        
        # Загрузка логов
        self.load_logs()
        
    def init_tray(self):
        """Инициализация системного трея"""
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
        
    def load_countries(self):
        """Загружает список стран"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if not servers_file.exists():
                self.country_combo.addItem("🔄 Сначала обновите серверы", None)
                return
            
            with open(servers_file) as f:
                servers = json.load(f)
            
            # Группируем по странам
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
                country = "🌍 Other"
                for flag, cname in country_map.items():
                    if flag in name or cname in name:
                        country = f"{flag} {cname}"
                        break
                
                if country not in countries:
                    countries[country] = []
                
                countries[country].append({
                    "host": server["host"],
                    "port": server["port"],
                    "latency": server.get("latency", 9999),
                    "name": name[:40]
                })
            
            # Сортируем
            countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))
            self.countries = countries
            
            # Заполняем комбобокс
            self.country_combo.clear()
            self.country_combo.addItem("⚡ Автовыбор (лучший сервер)", "auto")
            for country, servers_list in countries.items():
                self.country_combo.addItem(f"{country} ({len(servers_list)} серверов)", country)
            
            # Обновляем список серверов при выборе страны
            self.country_combo.currentIndexChanged.connect(self.on_country_changed)
            
            self.log("✅ Загружено локаций: " + str(len(countries)))
            
        except Exception as e:
            self.log(f"Ошибка загрузки стран: {e}")
            self.country_combo.addItem("❌ Ошибка загрузки", None)
    
    def on_country_changed(self, index):
        """Обновляет список серверов при выборе страны"""
        self.server_list.clear()
        country = self.country_combo.itemData(index)
        
        if not country or country == "auto":
            return
        
        if country in self.countries:
            servers = self.countries[country]
            servers.sort(key=lambda x: x["latency"])
            
            for i, s in enumerate(servers[:20], 1):  # Показываем топ-20
                item_text = f"{i}. {s['host']}:{s['port']} - {s['latency']} мс | {s['name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, s)
                self.server_list.addItem(item)
    
    def on_server_double_click(self, item):
        """Подключение к выбранному серверу"""
        server = item.data(Qt.UserRole)
        if server:
            self.log(f"Подключение к серверу: {server['host']}:{server['port']}")
            # Добавляем в blacklist все кроме выбранной страны
            self.connect_to_best_in_country()
    
    def load_logs(self):
        """Загрузка последних логов"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-50:]
                    for line in lines:
                        self.log_text.append(line.strip())
            except Exception:
                pass
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()
    
    def start_vpn(self):
        """Запуск VPN"""
        country = self.country_combo.currentData()
        
        if country == "auto":
            self.log("Запуск VPN в режиме АВТОВЫБОР...")
        else:
            self.log(f"Запуск VPN: {country}...")
        
        self.worker = VPNWorker("start", "split", country)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_start_finished)
        self.worker.start()
        
        self.connect_btn.setEnabled(False)
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
        self.worker.finished_signal.connect(self.on_update_finished)
        self.worker.start()
        self.update_btn.setEnabled(False)
    
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
                    padding: 20px;
                    border-radius: 10px;
                    margin: 10px;
                }
            """)
            self.statusBar.showMessage("VPN подключен")
            
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
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        self.statusBar.showMessage("VPN отключен")
    
    def on_update_finished(self, success):
        """Обработка завершения обновления"""
        self.update_btn.setEnabled(True)
        if success:
            self.load_countries()
            self.log("✅ Серверы обновлены")
    
    def update_status(self):
        """Обновление статуса"""
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
            
            result = subprocess.run(
                [str(CLIENT_SCRIPT), "status"],
                capture_output=True, text=True, env=env, timeout=5
            )
            
            output = result.stdout
            
            if "Подключен" in output or "подключен" in output.lower():
                if not self.is_connected:
                    self.is_connected = True
                    self.connect_btn.setText("⏹️ Отключить")
                    self.status_label.setText("🟢 Подключен")
            elif "Не подключен" in output:
                if self.is_connected:
                    self.is_connected = False
                    self.connect_btn.setText("▶️ Подключить")
                    self.status_label.setText("⚪ Не подключен")
                    
        except Exception:
            pass
    
    def save_log(self):
        """Сохранение лога"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить лог", "", "Текстовые файлы (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Успех", "Лог сохранен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
    
    def start_monitoring(self):
        """Запуск мониторинга процесса"""
        def monitor():
            while True:
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "vless-vpn"], capture_output=True
                    )
                    connected = result.returncode == 0
                    if connected != self.is_connected:
                        self.update_status()
                except Exception:
                    pass
                time.sleep(3)
        
        import threading
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def tray_activated(self, reason):
        """Обработка клика по трею"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
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
        """Выход из приложения"""
        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        self.worker.wait(3000)
        QApplication.quit()
    
    def connect_to_best_in_country(self):
        """Подключение к лучшему серверу в стране"""
        country = self.country_combo.currentData()
        if country and country != "auto" and country in self.countries:
            servers = self.countries[country]
            if servers:
                servers.sort(key=lambda x: x["latency"])
                best = servers[0]
                self.log(f"Лучший сервер: {best['host']}:{best['port']} - {best['latency']} мс")
        
        self.start_vpn()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VLESS VPN Client")
    app.setStyle("Fusion")
    
    # Тёмная тема
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = VPNClientGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
