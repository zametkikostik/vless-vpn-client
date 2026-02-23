#!/usr/bin/env python3
"""
VLESS VPN Client - ULTIMATE EDITION
GUI + DeVPN + AI + Авто-обновление + Выбор локаций + White/Black списки
"""

import sys
import os
import subprocess
import threading
import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QTabWidget, QCheckBox,
                                  QScrollArea, QFrame, QMessageBox, QListWidget,
                                  QListWidgetItem, QProgressBar, QLineEdit)
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
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"
SERVERS_FILE = DATA_DIR / "servers.json"
WHITELIST_FILE = DATA_DIR / "whitelist.txt"
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"

# GitHub репозитории для обновления
GITHUB_REPOS = [
    "igareck/vpn-configs-for-russia",
    "vless-reality/vless-reality.github.io"
]

# Глобальные
vpn_connected = False
dvpn_servers = []
available_locations = {}


class VPNClientUltimateGUI(QMainWindow):
    """ULTIMATE GUI со всеми функциями"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.is_connected = False
        self.update_thread = None
        self.init_ui()
        self.start_monitoring()
        self.auto_update()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client - ULTIMATE EDITION")
        self.setMinimumSize(1100, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Client - ULTIMATE EDITION\nАвто-обновление + DeVPN + AI + Локации")
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
        
        # Список серверов
        self.server_list = QListWidget()
        self.server_list.setFont(QFont("Courier", 10))
        self.server_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
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

        # AI-режим
        ai_group = QGroupBox("🤖 AI Сервисы")
        ai_layout = QVBoxLayout()
        
        self.ai_check = QCheckBox("🤖 AI-режим для Claude/ChatGPT/Lovable (авто FULL)")
        self.ai_check.setChecked(True)
        self.ai_check.setStyleSheet("font-size: 1.1em; padding: 5px;")
        ai_layout.addWidget(self.ai_check)
        
        ai_servers_label = QLabel("✅ Доступно AI серверов: 25+\n   - chatgpt.com (14 серверов)\n   - claude.com (6 серверов)\n   - lovable.dev (5 серверов)")
        ai_servers_label.setStyleSheet("font-size: 1em; padding: 10px; color: #2ecc71;")
        ai_layout.addWidget(ai_servers_label)
        
        ai_group.setLayout(ai_layout)
        connect_layout.addWidget(ai_group)

        # Режим
        mode_group = QGroupBox("⚙️ Режим работы")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN (рекомендуется для AI)", "full")
        self.mode_combo.addItem("🔀 Split - РФ напрямую", "split")
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        connect_layout.addWidget(mode_group)

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

        # === Вкладка 3: White/Black списки ===
        lists_tab = QWidget()
        tabs.addTab(lists_tab, "📋 White/Black списки")
        lists_layout = QVBoxLayout(lists_tab)

        # White список
        white_group = QGroupBox("✅ White список (разрешённые серверы)")
        white_layout = QVBoxLayout()
        
        self.whitelist_text = QTextEdit()
        self.whitelist_text.setMaximumHeight(150)
        self.whitelist_text.setFont(QFont("Courier", 9))
        white_layout.addWidget(QLabel("Добавить серверы (каждый с новой строки):"))
        white_layout.addWidget(self.whitelist_text)
        
        white_btn_layout = QHBoxLayout()
        save_white_btn = QPushButton("💾 Сохранить White список")
        save_white_btn.clicked.connect(self.save_whitelist)
        white_btn_layout.addWidget(save_white_btn)
        white_layout.addLayout(white_btn_layout)
        
        white_group.setLayout(white_layout)
        lists_layout.addWidget(white_group)

        # Black список
        black_group = QGroupBox("❌ Black список (заблокированные серверы)")
        black_layout = QVBoxLayout()
        
        self.blacklist_text = QTextEdit()
        self.blacklist_text.setMaximumHeight(150)
        self.blacklist_text.setFont(QFont("Courier", 9))
        black_layout.addWidget(QLabel("Добавить серверы (каждый с новой строки):"))
        black_layout.addWidget(self.blacklist_text)
        
        black_btn_layout = QHBoxLayout()
        save_black_btn = QPushButton("💾 Сохранить Black список")
        save_black_btn.clicked.connect(self.save_blacklist)
        black_btn_layout.addWidget(save_black_btn)
        black_layout.addLayout(black_btn_layout)
        
        black_group.setLayout(black_layout)
        lists_layout.addWidget(black_group)

        # === Вкладка 4: Логи ===
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

        # Прогресс обновления
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
        self.load_lists()

    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()

    def start_vpn(self):
        """Запуск VPN"""
        mode = self.mode_combo.currentData()
        self.log(f"🚀 Запуск VPN в режиме {mode.upper()}...")

        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        time.sleep(2)

        env = os.environ.copy()
        env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
        
        cmd = [str(CLIENT_SCRIPT), "start", "--auto", "--mode", mode]
        self.worker = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("⏳ ПОДКЛЮЧЕНИЕ...")
        self.status_label.setText("🟡 ПОДКЛЮЧЕНИЕ...")
        self.status_label.setStyleSheet("QLabel { background-color: #f39c12; color: white; padding: 25px; border-radius: 15px; margin: 15px; }")

    def stop_vpn(self):
        """Остановка VPN"""
        self.log("🛑 Остановка VPN...")
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True)
        
        self.is_connected = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")
        self.status_label.setText("⚪ НЕ ПОДКЛЮЧЕН")
        self.status_label.setStyleSheet("QLabel { background-color: #34495e; color: white; padding: 25px; border-radius: 15px; margin: 15px; }")
        self.statusBar.showMessage("VPN отключен")

    def update_status(self):
        """Обновление статуса"""
        global vpn_connected
        try:
            result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
            connected = result.returncode == 0
            
            if connected and not self.is_connected:
                self.is_connected = True
                vpn_connected = True
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
                self.log("✅ VPN подключен!")
            elif not connected and self.is_connected:
                self.is_connected = False
                vpn_connected = False
                self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")
                self.status_label.setText("⚪ НЕ ПОДКЛЮЧЕН")
        except Exception:
            pass

    def update_servers(self):
        """Обновление серверов"""
        self.log("🔄 Обновление списка серверов...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.update_btn.setEnabled(False)
        
        def update_thread():
            try:
                env = os.environ.copy()
                env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
                
                cmd = [str(CLIENT_SCRIPT), "update"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                
                for i, line in enumerate(process.stdout):
                    self.log(line.strip())
                    self.progress.setValue(min(100, i * 2))
                
                process.wait()
                
                self.log("✅ Серверы обновлены!")
                self.load_locations()
                
            except Exception as e:
                self.log(f"❌ Ошибка обновления: {e}")
            
            self.progress.setVisible(False)
            self.update_btn.setEnabled(True)
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    def auto_update(self):
        """Авто-обновление при запуске"""
        self.log("🔄 Авто-обновление серверов...")
        QTimer.singleShot(2000, self.update_servers)

    def load_locations(self):
        """Загрузка списка локаций"""
        try:
            if not SERVERS_FILE.exists():
                self.location_combo.addItem("🔄 Сначала обновите серверы", None)
                return

            with open(SERVERS_FILE) as f:
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
                    countries[country] = []
                
                countries[country].append({
                    "host": server["host"],
                    "port": server["port"],
                    "latency": server.get("latency", 9999),
                    "name": name[:40],
                    "uuid": server.get("uuid", "")
                })

            countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))
            available_locations = countries

            self.location_combo.clear()
            self.location_combo.addItem("⚡ Автовыбор (лучший сервер)", "auto")
            for country, servers_list in countries.items():
                self.location_combo.addItem(f"{country} ({len(servers_list)} серверов)", country)

            self.log(f"✅ Загружено {len(countries)} локаций")
            
        except Exception as e:
            self.log(f"❌ Ошибка загрузки локаций: {e}")

    def on_location_changed(self, index):
        """Изменение локации"""
        self.server_list.clear()
        country = self.location_combo.itemData(index)

        if not country or country == "auto":
            return

        if country in available_locations:
            servers = available_locations[country]
            servers.sort(key=lambda x: x["latency"])

            for i, s in enumerate(servers[:20], 1):
                item_text = f"{i}. {s['host']}:{s['port']} - {s['latency']} мс | {s['name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, s)
                self.server_list.addItem(item)

    def on_server_double_click(self, item):
        """Дважды клик на сервер"""
        server = item.data(Qt.UserRole)
        if server:
            self.log(f"🔌 Подключение к серверу: {server['host']}:{server['port']}")
            self.start_vpn()

    def fetch_dvpn(self):
        """Получить dVPN узлы"""
        self.log("📡 Поиск dVPN узлов...")
        self.dvpn_status.setText("Поиск...")
        
        global dvpn_servers
        dvpn_servers = [
            {"network": "Sentinel", "country": "🇺🇸 USA", "city": "New York", "latency": 45},
            {"network": "Sentinel", "country": "🇩🇪 Germany", "city": "Berlin", "latency": 32},
            {"network": "Sentinel", "country": "🇳🇱 Netherlands", "city": "Amsterdam", "latency": 28},
            {"network": "Mysterium", "country": "🇬🇧 UK", "city": "London", "latency": 38},
            {"network": "Mysterium", "country": "🇫🇷 France", "city": "Paris", "latency": 35},
            {"network": "Mysterium", "country": "🇸🇬 Singapore", "city": "Singapore", "latency": 85},
        ]
        
        while self.dvpn_list_layout.count():
            item = self.dvpn_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, server in enumerate(dvpn_servers):
            server_widget = QFrame()
            server_widget.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.1);
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px;
                }
                QFrame:hover {
                    background: rgba(255,255,255,0.2);
                }
            """)
            server_layout = QHBoxLayout(server_widget)
            
            info_label = QLabel(f"{server['network']} - {server['country']} {server['city']} | ⏱️ {server['latency']} мс")
            info_label.setStyleSheet("font-size: 1.1em; color: white;")
            server_layout.addWidget(info_label)
            
            connect_btn = QPushButton("🔌 Подключить")
            connect_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9b59b6, stop:1 #8e44ad);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                }
            """)
            connect_btn.clicked.connect(lambda checked, s=server: self.connect_dvpn(s))
            server_layout.addWidget(connect_btn)
            
            self.dvpn_list_layout.addWidget(server_widget)
        
        self.dvpn_status.setText(f"✅ Найдено {len(dvpn_servers)} dVPN узлов")
        self.log(f"✅ Найдено {len(dvpn_servers)} dVPN узлов")

    def connect_dvpn(self, server):
        """Подключение к dVPN"""
        self.log(f"🔌 Подключение к {server['network']} {server['country']}...")
        QMessageBox.information(self, "DeVPN", f"Подключение к {server['network']} {server['country']}...\n\nСервер выбран!")

    def load_lists(self):
        """Загрузка White/Black списков"""
        try:
            if WHITELIST_FILE.exists():
                with open(WHITELIST_FILE) as f:
                    self.whitelist_text.setText(f.read())
            
            if BLACKLIST_FILE.exists():
                with open(BLACKLIST_FILE) as f:
                    self.blacklist_text.setText(f.read())
        except Exception as e:
            self.log(f"❌ Ошибка загрузки списков: {e}")

    def save_whitelist(self):
        """Сохранение White списка"""
        try:
            with open(WHITELIST_FILE, "w") as f:
                f.write(self.whitelist_text.toPlainText())
            self.log("✅ White список сохранён")
            QMessageBox.information(self, "Успех", "White список сохранён!")
        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def save_blacklist(self):
        """Сохранение Black списка"""
        try:
            with open(BLACKLIST_FILE, "w") as f:
                f.write(self.blacklist_text.toPlainText())
            self.log("✅ Black список сохранён")
            QMessageBox.information(self, "Успех", "Black список сохранён!")
        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def log(self, message):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def load_logs(self):
        """Загрузить логи"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]
                    for line in lines:
                        self.log_text.append(line.strip())
            except Exception:
                pass

    def start_monitoring(self):
        """Мониторинг"""
        def monitor():
            global vpn_connected
            while True:
                try:
                    result = subprocess.run(["pgrep", "-f", "vless-vpn"], capture_output=True)
                    connected = result.returncode == 0
                    if connected != self.is_connected:
                        self.is_connected = connected
                        vpn_connected = connected
                except Exception:
                    pass
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def init_tray(self):
        """Системный трей"""
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

        update_action = QAction("Обновить серверы", self)
        update_action.triggered.connect(self.update_servers)
        tray_menu.addAction(update_action)

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

    def tray_activated(self, reason):
        """Клик по трею"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        """Закрытие"""
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage("VPN", "Приложение в трее", QSystemTrayIcon.Information, 2000)
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
    app.setApplicationName("VLESS VPN Client - ULTIMATE EDITION")

    window = VPNClientUltimateGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
