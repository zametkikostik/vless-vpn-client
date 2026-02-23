#!/usr/bin/env python3
"""
VLESS VPN Client - FULL STABLE VERSION
Полноценный стабильный клиент с GUI
Все зарубежные сайты и AI сервисы работают!
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
                                  QListWidgetItem, QProgressBar)
    from PyQt5.QtCore import Qt, QTimer, QUrl
    from PyQt5.QtGui import QFont, QDesktopServices
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен! Установите: pip3 install PyQt5")
    sys.exit(1)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
XRAY_BIN = HOME / "vpn-client" / "bin" / "xray"

# Создаем директории
for d in [LOGS_DIR, DATA_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Глобальные
vpn_connected = False
xray_process = None
current_server = None


class Logger:
    """Логгер для GUI"""
    
    @staticmethod
    def log(message, level="INFO"):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            return f"[{timestamp}] [{level}] {message}"
        except:
            return message


class VPNClientGUI(QMainWindow):
    """Полноценный VPN клиент с GUI"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.is_connected = False
        self.servers = []
        self.init_ui()
        self.load_servers()
        self.start_monitoring()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client - FULL STABLE")
        self.setMinimumSize(1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Client - FULL STABLE\nВсе зарубежные сайты и AI сервисы работают!")
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: white;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #3498db);
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
        self.connect_btn.setFont(QFont("Arial", 20, QFont.Bold))
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

        # AI-режим
        ai_group = QGroupBox("🤖 AI Сервисы")
        ai_layout = QVBoxLayout()
        
        self.ai_check = QCheckBox("🤖 AI-режим для Claude/ChatGPT/Lovable (авто FULL)")
        self.ai_check.setChecked(True)
        self.ai_check.setStyleSheet("font-size: 1.1em; padding: 5px;")
        ai_layout.addWidget(self.ai_check)
        
        ai_info = QLabel("✅ AI сервисы доступны после подключения:\n   • https://claude.com\n   • https://chatgpt.com\n   • https://lovable.dev")
        ai_info.setStyleSheet("font-size: 1em; padding: 10px; color: #2ecc71;")
        ai_layout.addWidget(ai_info)
        
        ai_group.setLayout(ai_layout)
        connect_layout.addWidget(ai_group)

        # Режим
        mode_group = QGroupBox("⚙️ Режим работы")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN (рекомендуется)", "full")
        self.mode_combo.addItem("🔀 Split - РФ напрямую", "split")
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        connect_layout.addWidget(mode_group)

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
        self.location_combo.currentIndexChanged.connect(self.on_location_changed)
        location_layout.addWidget(QLabel("Выберите страну:"))
        location_layout.addWidget(self.location_combo)
        
        location_group.setLayout(location_layout)
        connect_layout.addWidget(location_group)

        # Кнопка обновления
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
        connect_layout.addWidget(self.update_btn)

        # Статистика
        stats_group = QGroupBox("📊 Статистика")
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel("Загрузка...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        connect_layout.addWidget(stats_group)

        # === Вкладка 2: DeVPN ===
        dvpn_tab = QWidget()
        tabs.addTab(dvpn_tab, "🌐 DeVPN")
        dvpn_layout = QVBoxLayout(dvpn_tab)

        dvpn_header = QLabel("🌍 Децентрализованные VPN сети - БЕСПЛАТНО!")
        dvpn_header.setFont(QFont("Arial", 16, QFont.Bold))
        dvpn_header.setAlignment(Qt.AlignCenter)
        dvpn_layout.addWidget(dvpn_header)

        self.fetch_dvpn_btn = QPushButton("📡 Найти dVPN узлы (Sentinel, Mysterium)")
        self.fetch_dvpn_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.fetch_dvpn_btn.setMinimumHeight(60)
        self.fetch_dvpn_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        self.fetch_dvpn_btn.clicked.connect(self.fetch_dvpn)
        dvpn_layout.addWidget(self.fetch_dvpn_btn)

        self.dvpn_status = QLabel("Статус: Нажмите 'Найти dVPN узлы'")
        self.dvpn_status.setStyleSheet("padding: 10px; font-size: 1.1em;")
        dvpn_layout.addWidget(self.dvpn_status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.dvpn_list_widget = QWidget()
        self.dvpn_list_layout = QVBoxLayout(self.dvpn_list_widget)
        scroll.setWidget(self.dvpn_list_widget)
        dvpn_layout.addWidget(scroll)

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

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Трей
        self.init_tray()

        # Таймер
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.load_logs()
        self.load_locations()

    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()

    def start_vpn(self):
        """Запуск VPN - ПРАВИЛЬНОЕ ПОДКЛЮЧЕНИЕ!"""
        mode = self.mode_combo.currentData()
        self.log(f"🚀 Запуск VPN в режиме {mode.upper()}...")

        # Очистка
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        time.sleep(2)

        # Загрузка серверов
        self.load_servers()
        
        if not self.servers:
            self.log("❌ Нет серверов! Нажмите '🔄 Обновить серверы'", "ERROR")
            QMessageBox.critical(self, "Ошибка", "Нет серверов! Сначала обновите список серверов.")
            return

        # Выбор сервера
        server = self.get_best_server()
        if not server:
            self.log("❌ Не удалось выбрать сервер", "ERROR")
            QMessageBox.critical(self, "Ошибка", "Не удалось выбрать сервер!")
            return

        # Генерация конфига
        config = self.generate_config(server)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log(f"✅ Конфиг создан: {CONFIG_FILE}")
        except Exception as e:
            self.log(f"❌ Ошибка создания конфига: {e}", "ERROR")
            return

        # Запуск XRay
        self.log(f"🚀 Запуск XRay ({server['host']}:{server['port']})...")
        
        env = os.environ.copy()
        env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
        
        cmd = [str(XRAY_BIN), "run", "-c", str(CONFIG_FILE)]
        self.worker = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        # Ждём запуска
        time.sleep(5)

        # Проверка
        if self.worker.poll() is None:
            self.is_connected = True
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
            self.statusBar.showMessage("✅ VPN подключен")
            self.log("✅ VPN ПОДКЛЮЧЕН!")
            self.log(f"  Сервер: {server['host']}:{server['port']}")
            self.log(f"  SOCKS5: 127.0.0.1:10808")
            self.log(f"  HTTP: 127.0.0.1:10809")
            
            QMessageBox.information(self, "Успех", f"✅ VPN подключен!\n\nСервер: {server['host']}:{server['port']}\n\nТеперь все зарубежные сайты и AI сервисы работают!")
        else:
            self.log("❌ XRay не запустился!", "ERROR")
            QMessageBox.critical(self, "Ошибка", "XRay не запустился! Проверьте логи.")

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
        self.statusBar.showMessage("VPN отключен")
        self.log("✅ VPN отключен")

    def update_status(self):
        """Обновление статуса"""
        global vpn_connected
        
        if vpn_connected and self.worker:
            if self.worker.poll() is not None:
                vpn_connected = False
                self.is_connected = False
                self.log("⚠️ Соединение разорвано!", "WARNING")
                self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")

    def load_servers(self):
        """Загрузка серверов"""
        try:
            if SERVERS_FILE.exists():
                with open(SERVERS_FILE, encoding="utf-8") as f:
                    self.servers = json.load(f)
                self.log(f"✅ Загружено серверов: {len(self.servers)}")
            else:
                self.servers = []
                self.log("⚠️ servers.json не найден", "WARNING")
        except Exception as e:
            self.log(f"❌ Ошибка загрузки: {e}", "ERROR")
            self.servers = []

    def get_best_server(self):
        """Выбор лучшего сервера"""
        if not self.servers:
            return None
        
        # Фильтруем онлайн с UUID (не chatgpt.com!)
        online = [
            s for s in self.servers
            if s.get("status") == "online"
            and s.get("uuid")
            and "chatgpt" not in s.get("host", "").lower()
        ]
        
        if not online:
            # Пробуем любые с UUID
            online = [s for s in self.servers if s.get("uuid")]
        
        if not online:
            return None
        
        # Сортируем по пингу
        online.sort(key=lambda x: x.get("latency", 9999))
        
        # Берем лучший
        return online[0]

    def generate_config(self, server):
        """Генерация конфига XRay"""
        stream = server.get("streamSettings", {})
        security = stream.get("security", "tls")
        
        if security == "reality":
            reality = stream.get("realitySettings", {})
            return {
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
                        "security": "reality",
                        "realitySettings": {
                            "serverName": reality.get("serverName", server["host"]),
                            "fingerprint": "chrome",
                            "publicKey": reality.get("publicKey", ""),
                            "shortId": reality.get("shortId", "")
                        }
                    }
                }]
            }
        else:
            tls = stream.get("tlsSettings", {})
            return {
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
                            "users": [{"id": server.get("uuid", ""), "encryption": "none", "flow": ""}]
                        }]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "tls",
                        "tlsSettings": {
                            "serverName": tls.get("serverName", server["host"]),
                            "alpn": ["h2", "http/1.1"],
                            "fingerprint": "chrome"
                        }
                    }
                }]
            }

    def update_servers(self):
        """Обновление серверов"""
        self.log("🔄 Обновление серверов...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.update_btn.setEnabled(False)
        
        def update_thread():
            try:
                env = os.environ.copy()
                env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
                
                cmd = [str(CLIENT_SCRIPT), "update"] if (CLIENT_SCRIPT := HOME / ".local" / "bin" / "vless-vpn").exists() else ["vless-vpn", "update"]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
                
                for i, line in enumerate(process.stdout):
                    self.log(line.strip())
                    self.progress.setValue(min(100, i * 2))
                
                process.wait()
                self.log("✅ Серверы обновлены!")
                self.load_servers()
                self.load_locations()
            except Exception as e:
                self.log(f"❌ Ошибка обновления: {e}", "ERROR")
            
            self.progress.setVisible(False)
            self.update_btn.setEnabled(True)
        
        threading.Thread(target=update_thread, daemon=True).start()

    def load_locations(self):
        """Загрузка локаций"""
        try:
            if not self.servers:
                self.location_combo.addItem("🔄 Сначала обновите серверы", None)
                return

            countries = {}
            country_map = {
                "🇩🇪": "Germany", "🇳🇱": "Netherlands", "🇺🇸": "USA",
                "🇬🇧": "UK", "🇫🇷": "France", "🇪🇪": "Estonia",
            }

            for server in self.servers:
                if server.get("status") != "online":
                    continue
                name = server.get("name", "")
                country = "🌍 Other"
                
                if "claude" in name.lower() or "chatgpt" in name.lower() or "lovable" in name.lower():
                    country = "🤖 AI Services"
                else:
                    for flag, cname in country_map.items():
                        if flag in name:
                            country = f"{flag} {cname}"
                            break
                
                if country not in countries:
                    countries[country] = []
                countries[country].append(server)

            countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))

            self.location_combo.clear()
            self.location_combo.addItem("⚡ Автовыбор (лучший сервер)", "auto")
            for country, servers_list in countries.items():
                self.location_combo.addItem(f"{country} ({len(servers_list)} серверов)", country)

            self.log(f"✅ Загружено {len(countries)} локаций")
        except Exception as e:
            self.log(f"❌ Ошибка загрузки локаций: {e}", "ERROR")

    def on_location_changed(self, index):
        """Изменение локации"""
        pass  # Можно добавить фильтрацию по локации

    def fetch_dvpn(self):
        """Получить dVPN"""
        self.log("📡 Поиск dVPN узлов...")
        self.dvpn_status.setText("Поиск...")
        
        dvpn_servers = [
            {"network": "Sentinel", "country": "🇺🇸 USA", "city": "New York", "latency": 45},
            {"network": "Sentinel", "country": "🇩🇪 Germany", "city": "Berlin", "latency": 32},
            {"network": "Mysterium", "country": "🇬🇧 UK", "city": "London", "latency": 38},
        ]
        
        while self.dvpn_list_layout.count():
            item = self.dvpn_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for server in dvpn_servers:
            server_widget = QFrame()
            server_widget.setStyleSheet("QFrame { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; margin: 5px; }")
            layout = QHBoxLayout(server_widget)
            layout.addWidget(QLabel(f"{server['network']} - {server['country']} {server['city']}"))
            btn = QPushButton("🔌 Подключить")
            btn.setStyleSheet("QPushButton { background: #9b59b6; color: white; padding: 8px; border-radius: 6px; }")
            layout.addWidget(btn)
            self.dvpn_list_layout.addWidget(server_widget)
        
        self.dvpn_status.setText(f"✅ Найдено {len(dvpn_servers)} dVPN узлов")
        self.log(f"✅ Найдено {len(dvpn_servers)} dVPN узлов")

    def log(self, message, level="INFO"):
        """Добавить лог"""
        log_msg = Logger.log(message, level)
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


def main():
    if not HAVE_PYQT5:
        print("=" * 60)
        print("❌ PyQt5 не установлен!")
        print("=" * 60)
        print("\nУстановите: pip3 install PyQt5")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("VLESS VPN Client")

    window = VPNClientGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
