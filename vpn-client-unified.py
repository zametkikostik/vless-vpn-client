#!/usr/bin/env python3
"""
VLESS VPN Client - Unified (Объединённое приложение)
GUI + Веб-интерфейс в одном приложении
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import threading
import http.server
import socketserver
from urllib.parse import urlparse

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QListWidget, QListWidgetItem,
                                  QMessageBox, QTabWidget, QCheckBox, QFileDialog)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
    from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QDesktopServices
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен! Установите: sudo apt-get install python3-pyqt5")
    sys.exit(1)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

# Порт веб-сервера
WEB_PORT = 5000


class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, command="start", mode="split"):
        super().__init__()
        self.command = command
        self.mode = mode
    
    def run(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:{HOME}/vpn-client/bin:" + env.get("PATH", "")
            
            if self.command == "start":
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


class VPNServer:
    """Веб-сервер для доступа из браузера"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.server = None
        self.thread = None
    
    def start(self):
        """Запуск веб-сервера"""
        gui = self.gui
        
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                
                if parsed.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(gui.get_web_page().encode('utf-8'))
                
                elif parsed.path == '/api/status':
                    data = {
                        "connected": gui.is_connected,
                        "server": gui.current_server_name if hasattr(gui, 'current_server_name') else ""
                    }
                    self.send_json(data)
                
                elif parsed.path == '/api/countries':
                    data = {"countries": gui.countries}
                    self.send_json(data)
                
                elif parsed.path == '/api/logs':
                    logs = gui.get_last_logs(50)
                    data = {"logs": logs}
                    self.send_json(data)
                
                else:
                    self.send_error(404)
            
            def do_POST(self):
                parsed = urlparse(self.path)
                
                if parsed.path == '/api/start':
                    gui.start_vpn()
                    self.send_json({"success": True})
                
                elif parsed.path == '/api/stop':
                    gui.stop_vpn()
                    self.send_json({"success": True})
                
                elif parsed.path == '/api/update':
                    gui.update_servers()
                    self.send_json({"success": True})
                
                else:
                    self.send_error(404)
            
            def send_json(self, data):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            
            def log_message(self, format, *args):
                pass
        
        class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            allow_reuse_address = True
        
        try:
            self.server = ThreadedServer(("", WEB_PORT), Handler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            gui.log(f"✅ Веб-сервер запущен на порту {WEB_PORT}")
        except Exception as e:
            gui.log(f"⚠️ Не удалось запустить веб-сервер: {e}")
    
    def stop(self):
        if self.server:
            self.server.shutdown()


class VPNClientGUI(QMainWindow):
    """Основное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.tray_icon = None
        self.is_connected = False
        self.countries = {}
        self.web_server = None
        self.current_server_name = ""
        self.init_ui()
        self.load_countries()
        self.start_web_server()
        self.start_monitoring()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client")
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        header = QLabel("🔒 VLESS VPN Client v3.0 Unified")
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
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:disabled { background-color: #95a5a6; }
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
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.update_btn.clicked.connect(self.update_servers)
        btn_layout.addWidget(self.update_btn)
        
        connect_layout.addLayout(btn_layout)
        
        # Вкладка "Веб-доступ"
        web_tab = QWidget()
        tabs.addTab(web_tab, "🌐 Веб-доступ")
        web_layout = QVBoxLayout(web_tab)
        
        web_info = QLabel("📱 Открой в браузере:")
        web_info.setFont(QFont("Arial", 14))
        web_layout.addWidget(web_info)
        
        self.web_url_label = QLabel(f"http://localhost:{WEB_PORT}")
        self.web_url_label.setFont(QFont("Courier", 16, QFont.Bold))
        self.web_url_label.setAlignment(Qt.AlignCenter)
        self.web_url_label.setStyleSheet("color: #00d9ff; padding: 20px; background-color: #2c3e50; border-radius: 10px;")
        web_layout.addWidget(self.web_url_label)
        
        open_btn = QPushButton("🌐 Открыть в браузере")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d9ff;
                color: white;
                padding: 15px;
                font-size: 1.2em;
                border-radius: 8px;
                border: none;
            }
        """)
        open_btn.clicked.connect(self.open_in_browser)
        web_layout.addWidget(open_btn)
        
        web_layout.addStretch()
        
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
        
        log_btn_layout = QHBoxLayout()
        clear_log_btn = QPushButton("🗑️ Очистить")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("💾 Сохранить")
        save_log_btn.clicked.connect(self.save_log)
        log_btn_layout.addWidget(save_log_btn)
        
        log_layout.addLayout(log_btn_layout)
        
        # Вкладка "О программе"
        about_tab = QWidget()
        tabs.addTab(about_tab, "ℹ️ О программе")
        about_layout = QVBoxLayout(about_tab)
        
        about_group = QGroupBox("Информация")
        about_info_layout = QVBoxLayout()
        about_info_layout.addWidget(QLabel("Версия: 3.0 Unified"))
        about_info_layout.addWidget(QLabel("Протокол: VLESS-Reality"))
        about_info_layout.addWidget(QLabel("Порт SOCKS5: 10808"))
        about_info_layout.addWidget(QLabel("Порт HTTP: 10809"))
        about_info_layout.addWidget(QLabel("Веб-порт: 5000"))
        about_info_layout.addWidget(QLabel("Режим: Split (РФ напрямую)"))
        about_group.setLayout(about_info_layout)
        about_layout.addWidget(about_group)
        
        about_layout.addStretch()
        
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
    
    def start_web_server(self):
        """Запуск веб-сервера"""
        self.web_server = VPNServer(self)
        self.web_server.start()
    
    def open_in_browser(self):
        """Открыть веб-интерфейс в браузере"""
        url = QUrl(f"http://localhost:{WEB_PORT}")
        QDesktopServices.openUrl(url)
    
    def get_web_page(self):
        """Возвращает HTML страницу для веб-интерфейса"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 VLESS VPN</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .status {{
            font-size: 1.5em;
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        .status.connected {{ background: linear-gradient(45deg, #00b894, #00cec9); }}
        .status.disconnected {{ background: linear-gradient(45deg, #636e72, #b2bec3); }}
        .btn {{
            width: 100%;
            padding: 20px;
            font-size: 1.3em;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .btn-connect {{ background: linear-gradient(45deg, #00b894, #00cec9); color: white; }}
        .btn-disconnect {{ background: linear-gradient(45deg, #d63031, #e17055); color: white; }}
        .btn-update {{ background: linear-gradient(45deg, #0984e3, #74b9ff); color: white; padding: 15px; font-size: 1.1em; }}
        select {{
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #0984e3;
            border-radius: 10px;
            background: white;
            margin-bottom: 15px;
        }}
        .server-list {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
        }}
        .server-item {{
            padding: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
        }}
        .server-item:hover {{ background: rgba(255,255,255,0.1); }}
        .server-item.selected {{ background: rgba(0,184,148,0.3); }}
        .logs {{
            background: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .info-card {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .info-value {{ font-size: 1.5em; font-weight: bold; color: #00d9ff; }}
        .info-label {{ font-size: 0.9em; opacity: 0.7; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 VLESS VPN Web</h1>
        <div class="card">
            <div id="status" class="status disconnected">⏳ Загрузка...</div>
            <select id="countrySelect" onchange="onCountryChange()"><option>Загрузка...</option></select>
            <div id="serverList" class="server-list" style="display:none;"></div>
            <button id="connectBtn" class="btn btn-connect" onclick="toggleConnection()">▶️ Подключить</button>
            <button class="btn btn-update" onclick="updateServers()">🔄 Обновить серверы</button>
        </div>
        <div class="card">
            <h3>📊 Статистика</h3>
            <div class="info-grid">
                <div class="info-card"><div class="info-value" id="totalServers">-</div><div class="info-label">Всего серверов</div></div>
                <div class="info-card"><div class="info-value" id="onlineServers">-</div><div class="info-label">Онлайн</div></div>
                <div class="info-card"><div class="info-value" id="countries">-</div><div class="info-label">Стран</div></div>
            </div>
        </div>
        <div class="card">
            <h3>📋 Логи</h3>
            <div id="logs" class="logs">Загрузка...</div>
        </div>
    </div>
    <script>
        let isConnected = false;
        let selectedServer = null;
        let countries = {{}};
        window.onload = function() {{ loadStatus(); loadCountries(); loadLogs(); setInterval(loadStatus, 5000); setInterval(loadLogs, 3000); }};
        async function loadStatus() {{
            const r = await fetch('/api/status');
            const d = await r.json();
            const statusEl = document.getElementById('status');
            const btn = document.getElementById('connectBtn');
            if (d.connected) {{
                statusEl.className = 'status connected';
                statusEl.innerHTML = '🟢 Подключен<br><small>' + (d.server || '') + '</small>';
                btn.className = 'btn btn-disconnect';
                btn.innerHTML = '⏹️ Отключить';
                isConnected = true;
            }} else {{
                statusEl.className = 'status disconnected';
                statusEl.innerHTML = '⚪ Не подключен';
                btn.className = 'btn btn-connect';
                btn.innerHTML = '▶️ Подключить';
                isConnected = false;
            }}
        }}
        async function loadCountries() {{
            const r = await fetch('/api/countries');
            const d = await r.json();
            countries = d.countries || {{}};
            const select = document.getElementById('countrySelect');
            select.innerHTML = '<option value="auto">⚡ Автовыбор</option>';
            for (const [country, servers] of Object.entries(countries)) {{
                select.innerHTML += '<option value="'+country+'">'+country+' ('+servers.length+')</option>';
            }}
            let total = Object.values(countries).reduce((a,b) => a+b.length, 0);
            document.getElementById('totalServers').textContent = total;
            document.getElementById('onlineServers').textContent = total;
            document.getElementById('countries').textContent = Object.keys(countries).length;
        }}
        function onCountryChange() {{
            const country = document.getElementById('countrySelect').value;
            const list = document.getElementById('serverList');
            if (!country || country === 'auto') {{ list.style.display = 'none'; selectedServer = null; return; }}
            const servers = (countries[country] || []).sort((a,b) => a.latency - b.latency);
            list.innerHTML = '';
            servers.slice(0, 20).forEach((s, i) => {{
                const item = document.createElement('div');
                item.className = 'server-item';
                item.innerHTML = (i+1) + '. ' + s.host + ':' + s.port + ' - ' + s.latency + ' мс';
                item.onclick = () => {{ document.querySelectorAll('.server-item').forEach(el => el.classList.remove('selected')); item.classList.add('selected'); selectedServer = s; }};
                list.appendChild(item);
            }});
            list.style.display = 'block';
        }}
        async function toggleConnection() {{
            const btn = document.getElementById('connectBtn');
            btn.disabled = true;
            if (isConnected) {{ await fetch('/api/stop', {{method:'POST'}}); }}
            else {{ await fetch('/api/start', {{method:'POST'}}); }}
            setTimeout(loadStatus, 2000);
            btn.disabled = false;
        }}
        async function updateServers() {{
            const btn = document.querySelector('.btn-update');
            btn.disabled = true;
            await fetch('/api/update', {{method:'POST'}});
            setTimeout(() => {{ loadCountries(); btn.disabled = false; }}, 3000);
        }}
        async function loadLogs() {{
            const r = await fetch('/api/logs');
            const d = await r.json();
            document.getElementById('logs').innerHTML = d.logs.map(l => '<div>'+l+'</div>').join('');
        }}
    </script>
</body>
</html>
"""
    
    def load_countries(self):
        """Загружает список стран"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if not servers_file.exists():
                self.country_combo.addItem("🔄 Сначала обновите серверы", None)
                return
            
            with open(servers_file) as f:
                servers = json.load(f)
            
            countries = {}
            country_map = {
                "🇩🇪": "Germany", "🇳🇱": "Netherlands", "🇺🇸": "USA",
                "🇬🇧": "UK", "🇫🇷": "France", "🇪🇪": "Estonia",
                "🇧🇾": "Belarus", "🇵🇱": "Poland", "🇺🇦": "Ukraine",
                "🇰🇿": "Kazakhstan", "🇫🇮": "Finland", "🇸🇪": "Sweden",
                "🇳🇴": "Norway", "🇱🇻": "Latvia", "🇱🇹": "Lithuania",
                "🤖": "AI Services", "chatgpt.com": "AI Services", "claude.com": "AI Services",
            }
            
            for server in servers:
                if server.get("status") != "online":
                    continue
                name = server.get("name", "")
                host = server.get("host", "")
                country = "🌍 Other"
                
                # Проверка на AI сервисы (claude.com, chatgpt.com, lovable.dev)
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
                    "name": name[:40]
                })
            
            countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))
            self.countries = countries
            
            self.country_combo.clear()
            self.country_combo.addItem("⚡ Автовыбор (лучший сервер)", "auto")
            for country, servers_list in countries.items():
                self.country_combo.addItem(f"{country} ({len(servers_list)} серверов)", country)
            
            self.country_combo.currentIndexChanged.connect(self.on_country_changed)
            self.log("✅ Загружено локаций: " + str(len(countries)))
            
        except Exception as e:
            self.log(f"Ошибка загрузки стран: {e}")
    
    def on_country_changed(self, index):
        self.server_list.clear()
        country = self.country_combo.itemData(index)
        
        if not country or country == "auto":
            return
        
        if country in self.countries:
            servers = self.countries[country]
            servers.sort(key=lambda x: x["latency"])
            
            for i, s in enumerate(servers[:20], 1):
                item_text = f"{i}. {s['host']}:{s['port']} - {s['latency']} мс | {s['name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, s)
                self.server_list.addItem(item)
    
    def on_server_double_click(self, item):
        server = item.data(Qt.UserRole)
        if server:
            self.log(f"Подключение к серверу: {server['host']}:{server['port']}")
            self.connect_to_best_in_country()
    
    def load_logs(self):
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-50:]
                    for line in lines:
                        self.log_text.append(line.strip())
            except Exception:
                pass
    
    def get_last_logs(self, count=50):
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                return [line.strip() for line in f.readlines()[-count:]]
        return []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def toggle_connection(self):
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()
    
    def start_vpn(self):
        country = self.country_combo.currentData()
        if country == "auto":
            self.log("Запуск VPN в режиме АВТОВЫБОР...")
        else:
            self.log(f"Запуск VPN: {country}...")
        
        self.worker = VPNWorker("start", "split")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_start_finished)
        self.worker.start()
        
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("⏳ Подключение...")
        self.statusBar.showMessage("Подключение к VPN...")
    
    def stop_vpn(self):
        self.log("Остановка VPN...")
        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_stop_finished)
        self.worker.start()
        self.connect_btn.setEnabled(False)
    
    def update_servers(self):
        self.log("Обновление списка серверов...")
        self.worker = VPNWorker("update")
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_update_finished)
        self.worker.start()
        self.update_btn.setEnabled(False)
    
    def on_start_finished(self, success):
        self.connect_btn.setEnabled(True)
        if success:
            self.is_connected = True
            self.connect_btn.setText("⏹️ Отключить")
            self.connect_btn.setStyleSheet("""
                QPushButton { background-color: #e74c3c; color: white; padding: 15px 30px; border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #c0392b; }
            """)
            self.status_label.setText("🟢 Подключен")
            self.status_label.setStyleSheet("""
                QLabel { background-color: #27ae60; color: white; padding: 20px; border-radius: 10px; margin: 10px; }
            """)
            self.statusBar.showMessage("VPN подключен")
            if self.tray_icon:
                self.tray_icon.showMessage("VPN", "Подключено", QSystemTrayIcon.Information, 2000)
        else:
            self.status_label.setText("🔴 Ошибка подключения")
            self.statusBar.showMessage("Ошибка подключения")
    
    def on_stop_finished(self, success):
        self.is_connected = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ Подключить")
        self.connect_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; padding: 15px 30px; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.status_label.setText("⚪ Не подключен")
        self.status_label.setStyleSheet("""
            QLabel { background-color: #34495e; color: white; padding: 20px; border-radius: 10px; margin: 10px; }
        """)
        self.statusBar.showMessage("VPN отключен")
    
    def on_update_finished(self, success):
        self.update_btn.setEnabled(True)
        if success:
            self.load_countries()
            self.log("✅ Серверы обновлены")
    
    def update_status(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:{HOME}/vpn-client/bin:" + env.get("PATH", "")
            result = subprocess.run([str(CLIENT_SCRIPT), "status"], capture_output=True, text=True, env=env, timeout=5)
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
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить лог", "", "Текстовые файлы (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Успех", "Лог сохранен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
    
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    result = subprocess.run(["pgrep", "-f", "vless-vpn"], capture_output=True)
                    connected = result.returncode == 0
                    if connected != self.is_connected:
                        self.update_status()
                except Exception:
                    pass
                time.sleep(3)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def init_tray(self):
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
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def closeEvent(self, event):
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage("VPN Client", "Приложение свернуто в трей", QSystemTrayIcon.Information, 2000)
            event.ignore()
        else:
            event.accept()
    
    def quit_app(self):
        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        self.worker.wait(3000)
        if self.web_server:
            self.web_server.stop()
        QApplication.quit()
    
    def connect_to_best_in_country(self):
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
