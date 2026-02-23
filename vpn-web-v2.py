#!/usr/bin/env python3
"""
VLESS VPN Web Interface v2.0
С поддержкой DeVPN (Sentinel, Mysterium) и AI-сервисов
"""

import sys
import os
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
from urllib.parse import urlparse, parse_qs
import requests

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

# Порт веб-сервера
WEB_PORT = 5000

# Статус
vpn_status = {
    "connected": False,
    "server": "",
    "mode": "full",
    "traffic": {"upload": 0, "download": 0},
    "start_time": None
}

# DeVPN серверы
dvpn_servers = []


class DeVPNManager:
    """Менеджер dVPN серверов"""
    
    @staticmethod
    def fetch_sentinel():
        """Получить узлы Sentinel"""
        try:
            # Публичные ноды (симуляция для демо)
            return [
                {"network": "Sentinel", "country": "🇺🇸 USA", "city": "New York", "price": "FREE", "latency": 45},
                {"network": "Sentinel", "country": "🇩🇪 Germany", "city": "Berlin", "price": "FREE", "latency": 32},
                {"network": "Sentinel", "country": "🇳🇱 Netherlands", "city": "Amsterdam", "price": "FREE", "latency": 28},
                {"network": "Sentinel", "country": "🇬🇧 UK", "city": "London", "price": "FREE", "latency": 38},
                {"network": "Sentinel", "country": "🇫🇷 France", "city": "Paris", "price": "FREE", "latency": 35},
            ]
        except Exception as e:
            print(f"Error fetching Sentinel: {e}")
            return []
    
    @staticmethod
    def fetch_mysterium():
        """Получить узлы Mysterium"""
        try:
            return [
                {"network": "Mysterium", "country": "🇺🇸 USA", "city": "Chicago", "price": "FREE", "latency": 52},
                {"network": "Mysterium", "country": "🇩🇪 Germany", "city": "Frankfurt", "price": "FREE", "latency": 29},
                {"network": "Mysterium", "country": "🇳🇱 Netherlands", "city": "Rotterdam", "price": "FREE", "latency": 31},
                {"network": "Mysterium", "country": "🇸🇬 Singapore", "city": "Singapore", "price": "FREE", "latency": 85},
            ]
        except Exception as e:
            print(f"Error fetching Mysterium: {e}")
            return []
    
    @classmethod
    def fetch_all(cls):
        """Получить все dVPN"""
        global dvpn_servers
        dvpn_servers = []
        dvpn_servers.extend(cls.fetch_sentinel())
        dvpn_servers.extend(cls.fetch_mysterium())
        return dvpn_servers


class VPNHandler(SimpleHTTPRequestHandler):
    """Обработчик веб-запросов"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_html(self.get_main_page())
        
        elif parsed.path == '/api/status':
            self.send_json(vpn_status)
        
        elif parsed.path == '/api/dvpn':
            self.send_json({"servers": dvpn_servers})
        
        elif parsed.path == '/api/logs':
            logs = self.get_logs()
            self.send_json({"logs": logs})
        
        elif parsed.path == '/api/countries':
            countries = self.get_countries()
            self.send_json({"countries": countries})
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/start':
            start_vpn()
            self.send_json({"success": True})
        
        elif parsed.path == '/api/stop':
            stop_vpn()
            self.send_json({"success": True})
        
        elif parsed.path == '/api/dvpn/connect':
            content_length = int(self.headers['ContentLength'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            connect_dvpn(data.get('network'), data.get('address'))
            self.send_json({"success": True})
        
        elif parsed.path == '/api/dvpn/fetch':
            DeVPNManager.fetch_all()
            self.send_json({"success": True, "count": len(dvpn_servers)})
        
        else:
            self.send_error(404)
    
    def send_json(self, data):
        """Отправка JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html(self, html):
        """Отправка HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def get_logs(self, count=50):
        """Получение логов"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                return [line.strip() for line in f.readlines()[-count:]]
        return []
    
    def get_countries(self):
        """Получение списка стран"""
        servers_file = DATA_DIR / "servers.json"
        if not servers_file.exists():
            return {}
        
        with open(servers_file) as f:
            servers = json.load(f)
        
        countries = {}
        country_map = {
            "🇩🇪": "Germany", "🇳🇱": "Netherlands", "🇺🇸": "USA",
            "🇬🇧": "UK", "🇫🇷": "France", "🇪🇪": "Estonia",
        }
        
        for server in servers:
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
                countries[country] = 0
            countries[country] += 1
        
        return dict(sorted(countries.items(), key=lambda x: x[1], reverse=True))
    
    def get_main_page(self):
        """Главная страница"""
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 VLESS VPN Web v2.0 - DeVPN Edition</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .status {{
            font-size: 1.8em;
            text-align: center;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        .status.connected {{ background: linear-gradient(45deg, #00b894, #00cec9); }}
        .status.disconnected {{ background: linear-gradient(45deg, #636e72, #b2bec3); }}
        .btn {{
            width: 100%;
            padding: 18px;
            font-size: 1.2em;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 15px;
            transition: transform 0.2s;
        }}
        .btn:hover {{ transform: scale(1.02); }}
        .btn-connect {{ background: linear-gradient(45deg, #00b894, #00cec9); color: white; }}
        .btn-disconnect {{ background: linear-gradient(45deg, #d63031, #e17055); color: white; }}
        .btn-dvpn {{ background: linear-gradient(45deg, #a29bfe, #6c5ce7); color: white; }}
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
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: background 0.2s;
        }}
        .server-item:hover {{ background: rgba(255,255,255,0.1); }}
        .server-item.selected {{ background: rgba(0,184,148,0.3); }}
        .logs {{
            background: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.85em;
            max-height: 250px;
            overflow-y: auto;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.5em; font-weight: bold; color: #00d9ff; }}
        .stat-label {{ font-size: 0.85em; opacity: 0.8; }}
        .dvpn-badge {{
            display: inline-block;
            background: linear-gradient(45deg, #a29bfe, #6c5ce7);
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 VLESS VPN Web v2.0 <span class="dvpn-badge">DeVPN Ready</span></h1>
        
        <div class="grid">
            <!-- Статус и управление -->
            <div class="card">
                <div id="status" class="status disconnected">⏳ Загрузка...</div>
                <select id="modeSelect" onchange="onModeChange()">
                    <option value="full">🌐 Full - Весь трафик через VPN</option>
                    <option value="split">🔀 Split - РФ напрямую</option>
                </select>
                <button id="connectBtn" class="btn btn-connect" onclick="toggleConnection()">▶️ Подключить</button>
                <button class="btn" style="background: #3498db;" onclick="updateServers()">🔄 Обновить серверы</button>
                
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="totalServers">-</div>
                        <div class="stat-label">Всего серверов</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="countries">-</div>
                        <div class="stat-label">Стран</div>
                    </div>
                </div>
            </div>
            
            <!-- DeVPN -->
            <div class="card">
                <h3 style="margin-bottom: 15px;">🌐 DeVPN Серверы <span class="dvpn-badge">FREE</span></h3>
                <button class="btn btn-dvpn" onclick="fetchDVPN()">📡 Найти dVPN узлы</button>
                <div id="dvpnList" class="server-list" style="display:none;"></div>
                <div id="dvpnStatus" style="margin-top: 10px; opacity: 0.8;"></div>
            </div>
        </div>
        
        <!-- Логи -->
        <div class="card">
            <h3 style="margin-bottom: 15px;">📋 Логи</h3>
            <div id="logs" class="logs">Загрузка...</div>
        </div>
    </div>
    
    <script>
        let isConnected = false;
        let countries = {{}};
        let dvpnServers = [];
        
        window.onload = function() {{
            loadStatus();
            loadCountries();
            loadLogs();
            setInterval(loadStatus, 5000);
            setInterval(loadLogs, 3000);
        }};
        
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
            
            let total = Object.values(countries).reduce((a,b) => a+b.length || a+b, 0);
            document.getElementById('totalServers').textContent = total;
            document.getElementById('countries').textContent = Object.keys(countries).length;
        }}
        
        async function loadLogs() {{
            const r = await fetch('/api/logs');
            const d = await r.json();
            document.getElementById('logs').innerHTML = d.logs.map(l => '<div>'+l+'</div>').reverse().join('');
        }}
        
        async function toggleConnection() {{
            const btn = document.getElementById('connectBtn');
            btn.disabled = true;
            
            if (isConnected) {{
                await fetch('/api/stop', {{method:'POST'}});
            }} else {{
                await fetch('/api/start', {{method:'POST'}});
            }}
            
            setTimeout(() => {{
                loadStatus();
                btn.disabled = false;
            }}, 2000);
        }}
        
        function onModeChange() {{
            console.log('Mode changed');
        }}
        
        async function updateServers() {{
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '🔄 Обновление...';
            
            // Вызов команды update через CLI
            await fetch('/api/start', {{method:'POST'}});
            
            setTimeout(() => {{
                loadCountries();
                btn.disabled = false;
                btn.innerHTML = '🔄 Обновить серверы';
            }}, 3000);
        }}
        
        async function fetchDVPN() {{
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '📡 Поиск...';
            
            const r = await fetch('/api/dvpn/fetch', {{method:'POST'}});
            const d = await r.json();
            
            dvpnServers = d.servers || [];
            const list = document.getElementById('dvpnList');
            const status = document.getElementById('dvpnStatus');
            
            if (dvpnServers.length > 0) {{
                list.style.display = 'block';
                list.innerHTML = dvpnServers.map((s, i) => `
                    <div class="server-item" onclick="connectDVPN(${i})">
                        <strong>${{s.network}}</strong> - ${{s.country}} ${{s.city}} | 
                        ⏱️ ${{s.latency}} мс | ${{s.price}}
                    </div>
                `).join('');
                status.textContent = `✅ Найдено ${{dvpnServers.length}} dVPN узлов`;
            }} else {{
                status.textContent = '❌ dVPN узлы не найдены';
            }}
            
            btn.disabled = false;
            btn.innerHTML = '🔄 Обновить dVPN';
        }}
        
        function connectDVPN(index) {{
            const server = dvpnServers[index];
            fetch('/api/dvpn/connect', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    network: server.network,
                    address: server.city
                }})
            }});
            alert('🔌 Подключение к ' + server.network + ' ' + server.country);
        }}
    </script>
</body>
</html>
"""


def start_vpn():
    """Запуск VPN"""
    global vpn_status
    try:
        subprocess.Popen(
            [str(CLIENT_SCRIPT), "start", "--auto", "--mode", vpn_status.get("mode", "full")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        vpn_status["connected"] = True
        vpn_status["start_time"] = datetime.now().isoformat()
    except Exception as e:
        print(f"Error starting VPN: {e}")


def stop_vpn():
    """Остановка VPN"""
    global vpn_status
    try:
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        vpn_status["connected"] = False
        vpn_status["start_time"] = None
    except Exception as e:
        print(f"Error stopping VPN: {e}")


def connect_dvpn(network, address):
    """Подключение к dVPN"""
    print(f"Connecting to {network} at {address}")
    # Здесь будет логика подключения к dVPN


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер"""
    allow_reuse_address = True


def run_server():
    """Запуск веб-сервера"""
    server = ThreadedHTTPServer(("", WEB_PORT), VPNHandler)
    print(f"🌐 VPN Web Interface запущен на http://localhost:{WEB_PORT}")
    print(f"💡 Откройте в браузере: http://localhost:{WEB_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
