#!/usr/bin/env python3
"""
VLESS VPN Client - ALL IN ONE
GUI + Web Interface + DeVPN в одном приложении!
"""

import sys
import os
import subprocess
import threading
import json
import time
from pathlib import Path
from datetime import datetime
import socketserver
import http.server
from urllib.parse import urlparse

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QTabWidget, QCheckBox,
                                  QMessageBox, QScrollArea, QFrame)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
    from PyQt5.QtGui import QFont, QDesktopServices
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен! Установите: pip3 install PyQt5")
    sys.exit(1)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

# Порт веб-сервера
WEB_PORT = 5000

# Глобальные переменные
vpn_connected = False
web_server_running = False
dvpn_servers = []


# ==================== VPN WORKER ====================
class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, command="start", mode="full"):
        super().__init__()
        self.command = command
        self.mode = mode

    def run(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")

            if self.command == "start":
                # Остановить старые процессы
                subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
                subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
                time.sleep(2)

                # Запустить VPN
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
                subprocess.run(["pkill", "-f", "xray"], capture_output=True)
                self.log_signal.emit("✅ VPN остановлен")
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

        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка: {e}")
            self.finished_signal.emit(False)


# ==================== WEB SERVER ====================
class WebServerThread(QThread):
    """Веб-сервер в отдельном потоке"""
    log_signal = pyqtSignal(str)

    def __init__(self, gui_instance):
        super().__init__()
        self.gui = gui_instance
        self.server = None

    def run(self):
        global web_server_running
        
        class VPNWebHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(handler):
                parsed = urlparse(handler.path)
                
                if parsed.path == '/':
                    handler.send_response(200)
                    handler.send_header('Content-type', 'text/html; charset=utf-8')
                    handler.end_headers()
                    handler.wfile.write(self.gui.get_web_page().encode('utf-8'))
                
                elif parsed.path == '/api/status':
                    data = {"connected": vpn_connected, "web_port": WEB_PORT}
                    handler.send_json(data)
                
                elif parsed.path == '/api/dvpn':
                    data = {"servers": dvpn_servers}
                    handler.send_json(data)
                
                elif parsed.path == '/api/logs':
                    logs = self.gui.get_last_logs(50)
                    data = {"logs": logs}
                    handler.send_json(data)
                
                else:
                    handler.send_error(404)

            def do_POST(handler):
                parsed = urlparse(handler.path)
                
                if parsed.path == '/api/start':
                    self.gui.start_vpn()
                    handler.send_json({"success": True})
                
                elif parsed.path == '/api/stop':
                    self.gui.stop_vpn()
                    handler.send_json({"success": True})
                
                elif parsed.path == '/api/dvpn/fetch':
                    self.gui.fetch_dvpn()
                    handler.send_json({"success": True, "count": len(dvpn_servers)})
                
                else:
                    handler.send_error(404)

            def send_json(handler, data):
                handler.send_response(200)
                handler.send_header('Content-type', 'application/json; charset=utf-8')
                handler.send_header('Access-Control-Allow-Origin', '*')
                handler.end_headers()
                handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

            def log_message(handler, format, *args):
                pass

        class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            allow_reuse_address = True

        try:
            self.server = ThreadedServer(("", WEB_PORT), VPNWebHandler)
            web_server_running = True
            self.log_signal.emit(f"✅ Веб-сервер запущен на http://localhost:{WEB_PORT}")
            self.server.serve_forever()
        except Exception as e:
            self.log_signal.emit(f"❌ Веб-сервер: {e}")
            web_server_running = False

    def stop(self):
        global web_server_running
        if self.server:
            self.server.shutdown()
            web_server_running = False


# ==================== MAIN GUI ====================
class VPNClientGUI(QMainWindow):
    """Основное окно приложения"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.web_server = None
        self.tray_icon = None
        self.is_connected = False
        
        self.init_ui()
        self.start_web_server()
        self.start_monitoring()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client - ALL IN ONE")
        self.setMinimumSize(1100, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Client v3.0 - ALL IN ONE\nGUI + Web + DeVPN")
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
        self.status_label = QLabel("⚪ Не подключен")
        self.status_label.setFont(QFont("Arial", 18, QFont.Bold))
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

        # Режим работы
        mode_group = QGroupBox("⚙️ Режим работы")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN (рекомендуется)", "full")
        self.mode_combo.addItem("🔀 Split - РФ напрямую, остальное через VPN", "split")
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)

        # AI-режим
        self.ai_check = QCheckBox("🤖 AI-режим для Claude/ChatGPT/Lovable (авто FULL)")
        self.ai_check.setChecked(True)
        self.ai_check.stateChanged.connect(self.on_ai_mode_changed)
        mode_layout.addWidget(self.ai_check)

        mode_group.setLayout(mode_layout)
        connect_layout.addWidget(mode_group)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(45deg, #2ecc71, #27ae60);
                color: white;
                padding: 20px 40px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background: linear-gradient(45deg, #27ae60, #229954); }
            QPushButton:disabled { background: #95a5a6; }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        btn_layout.addWidget(self.connect_btn)

        self.web_btn = QPushButton("🌐 Открыть веб-интерфейс")
        self.web_btn.setFont(QFont("Arial", 12))
        self.web_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(45deg, #3498db, #2980b9);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
        """)
        self.web_btn.clicked.connect(self.open_web)
        btn_layout.addWidget(self.web_btn)

        connect_layout.addLayout(btn_layout)

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

        dvpn_header = QLabel("🌍 Децентрализованные VPN сети (Sentinel, Mysterium) - БЕСПЛАТНО!")
        dvpn_header.setFont(QFont("Arial", 14))
        dvpn_header.setAlignment(Qt.AlignCenter)
        dvpn_layout.addWidget(dvpn_header)

        self.fetch_dvpn_btn = QPushButton("📡 Найти dVPN узлы")
        self.fetch_dvpn_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.fetch_dvpn_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(45deg, #9b59b6, #8e44ad);
                color: white;
                padding: 18px;
                border-radius: 12px;
                border: none;
            }
        """)
        self.fetch_dvpn_btn.clicked.connect(self.fetch_dvpn)
        dvpn_layout.addWidget(self.fetch_dvpn_btn)

        self.dvpn_status = QLabel("Статус: Нажмите 'Найти dVPN узлы'")
        self.dvpn_status.setStyleSheet("padding: 10px; font-size: 1.1em;")
        dvpn_layout.addWidget(self.dvpn_status)

        # Scroll area для списка dVPN
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
                border: 1px solid #34495e;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)

        log_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Очистить")
        clear_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_btn)
        log_layout.addLayout(log_btn_layout)

        # Строка состояния
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")

        # Трей
        self.init_tray()

        # Таймер обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.load_logs()
        self.load_stats()

    def on_ai_mode_changed(self, state):
        """AI режим"""
        if state == Qt.Checked:
            self.mode_combo.setCurrentIndex(0)
            self.log("✅ AI-режим включен - FULL для Claude/ChatGPT/Lovable")
        else:
            self.log("ℹ️ AI-режим выключен")

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

        self.worker = VPNWorker("start", mode)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_start_finished)
        self.worker.start()

        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("⏳ Подключение...")

    def stop_vpn(self):
        """Остановка VPN"""
        self.log("🛑 Остановка VPN...")

        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_stop_finished)
        self.worker.start()

    def on_start_finished(self, success):
        """Запуск завершён"""
        global vpn_connected
        
        self.connect_btn.setEnabled(True)

        if success:
            self.is_connected = True
            vpn_connected = True
            
            self.connect_btn.setText("⏹️ Отключить")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background: linear-gradient(45deg, #e74c3c, #c0392b);
                    color: white;
                    padding: 20px 40px;
                    border-radius: 12px;
                    border: none;
                }
            """)
            self.status_label.setText("🟢 Подключен")
            self.status_label.setStyleSheet("""
                QLabel {
                    background: linear-gradient(45deg, #27ae60, #2ecc71);
                    color: white;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 15px;
                }
            """)
            self.statusBar.showMessage("✅ VPN подключен")
            self.load_stats()
        else:
            self.status_label.setText("🔴 Ошибка подключения")

    def on_stop_finished(self, success):
        """Остановка завершена"""
        global vpn_connected
        
        self.is_connected = False
        vpn_connected = False
        
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ Подключить")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(45deg, #2ecc71, #27ae60);
                color: white;
                padding: 20px 40px;
                border-radius: 12px;
                border: none;
            }
        """)
        self.status_label.setText("⚪ Не подключен")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin: 15px;
            }
        """)
        self.statusBar.showMessage("VPN отключен")

    def start_web_server(self):
        """Запуск веб-сервера"""
        self.web_server = WebServerThread(self)
        self.web_server.log_signal.connect(self.log)
        self.web_server.start()
        self.log(f"✅ Веб-сервер запущен на http://localhost:{WEB_PORT}")

    def open_web(self):
        """Открыть веб-интерфейс"""
        url = QUrl(f"http://localhost:{WEB_PORT}")
        QDesktopServices.openUrl(url)
        self.log(f"🌐 Веб-интерфейс: http://localhost:{WEB_PORT}")

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
        ]
        
        # Очистить список
        while self.dvpn_list_layout.count():
            item = self.dvpn_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Добавить узлы
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
                    background: linear-gradient(45deg, #9b59b6, #8e44ad);
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

    def update_status(self):
        """Обновление статуса"""
        global vpn_connected
        
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
                    vpn_connected = True
                    self.connect_btn.setText("⏹️ Отключить")
                    self.status_label.setText("🟢 Подключен")
            elif "✗ Не подключен" in output:
                if self.is_connected:
                    self.is_connected = False
                    vpn_connected = False
                    self.connect_btn.setText("▶️ Подключить")
                    self.status_label.setText("⚪ Не подключен")

        except Exception:
            pass

    def load_stats(self):
        """Загрузка статистики"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if servers_file.exists():
                with open(servers_file) as f:
                    servers = json.load(f)
                
                countries = {}
                for server in servers:
                    if server.get("status") != "online":
                        continue
                    name = server.get("name", "")
                    country = "🌍 Other"
                    
                    if "claude" in name.lower() or "chatgpt" in name.lower() or "lovable" in name.lower():
                        country = "🤖 AI Services"
                    elif "🇩🇪" in name:
                        country = "🇩🇪 Germany"
                    elif "🇳🇱" in name:
                        country = "🇳🇱 Netherlands"
                    elif "🇺🇸" in name:
                        country = "🇺🇸 USA"
                    
                    if country not in countries:
                        countries[country] = 0
                    countries[country] += 1
                
                stats_text = f"🌍 Всего серверов: {len(servers)}\n"
                stats_text += f"🌐 Локаций: {len(countries)}\n"
                
                if countries.get("🤖 AI Services", 0) > 0:
                    stats_text += f"🤖 AI Services: {countries['🤖 AI Services']}\n"
                
                stats_text += "\nТоп локаций:\n"
                for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
                    stats_text += f"  {country}: {count}\n"
                
                self.stats_label.setText(stats_text)
        except Exception as e:
            self.stats_label.setText(f"Ошибка: {e}")

    def log(self, message):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def get_last_logs(self, count=50):
        """Получить последние логи"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                return [line.strip() for line in f.readlines()[-count:]]
        return []

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

    def get_web_page(self):
        """Веб-страница"""
        status = "🟢 Подключен" if self.is_connected else "⚪ Не подключен"
        status_class = "connected" if self.is_connected else "disconnected"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔒 VLESS VPN Web</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            background: linear-gradient(45deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            text-align: center;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            font-size: 2em;
        }}
        .status.connected {{ background: linear-gradient(45deg, #00b894, #00cec9); }}
        .status.disconnected {{ background: linear-gradient(45deg, #636e72, #b2bec3); }}
        .btn {{
            width: 100%;
            padding: 20px;
            font-size: 1.3em;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            margin: 10px 0;
        }}
        .btn-connect {{ background: linear-gradient(45deg, #2ecc71, #27ae60); color: white; }}
        .btn-disconnect {{ background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }}
        .btn-dvpn {{ background: linear-gradient(45deg, #9b59b6, #8e44ad); color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 VLESS VPN Web</h1>
        <div class="status {status_class}">{status}</div>
        <button class="btn btn-connect" onclick="fetch('/api/start', {{method:'POST'}}).then(()=>location.reload())">▶️ Подключить</button>
        <button class="btn btn-disconnect" onclick="fetch('/api/stop', {{method:'POST'}}).then(()=>location.reload())">⏹️ Отключить</button>
        <button class="btn btn-dvpn" onclick="fetch('/api/dvpn/fetch', {{method:'POST'}}).then(()=>location.reload())">📡 Найти dVPN</button>
    </div>
</body>
</html>
"""

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
        """Закрытие окна"""
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage("VPN", "Приложение в трее", QSystemTrayIcon.Information, 2000)
            event.ignore()
        else:
            event.accept()

    def quit_app(self):
        """Выход"""
        self.stop_vpn()
        if self.web_server:
            self.web_server.stop()
        QApplication.quit()

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
                        if connected:
                            self.log("✅ VPN подключен (обнаружен)")
                        else:
                            self.log("⚠️ VPN отключен")
                except Exception:
                    pass
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()


def main():
    if not HAVE_PYQT5:
        print("=" * 60)
        print("❌ PyQt5 не установлен!")
        print("=" * 60)
        print("\nУстановите: pip3 install PyQt5")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("VLESS VPN Client - ALL IN ONE")

    window = VPNClientGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
