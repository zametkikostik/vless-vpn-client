#!/usr/bin/env python3
"""
VLESS VPN Web Controller - ЛЁГКАЯ ВЕРСИЯ (без Flask)
Работает на встроенном HTTP сервере
"""

import http.server
import socketserver
import json
import subprocess
import os
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import threading

PORT = 5000
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"


class VPNController:
    def __init__(self):
        self.servers = []
        self.blacklist = set()
        self.load_data()
    
    def load_data(self):
        servers_file = DATA_DIR / "servers.json"
        if servers_file.exists():
            with open(servers_file) as f:
                self.servers = json.load(f)
        
        blacklist_file = DATA_DIR / "blacklist.txt"
        if blacklist_file.exists():
            with open(blacklist_file) as f:
                self.blacklist = set(line.strip() for line in f if line.strip())
    
    def get_countries(self):
        countries = {}
        country_map = {
            "🇩🇪": "Germany", "🇳🇱": "Netherlands", "🇺🇸": "USA",
            "🇬🇧": "UK", "🇫🇷": "France", "🇪🇪": "Estonia",
            "🇧🇾": "Belarus", "🇵🇱": "Poland", "🇺🇦": "Ukraine",
            "🇰🇿": "Kazakhstan", "🇫🇮": "Finland", "🇸🇪": "Sweden",
            "🇳🇴": "Norway", "🇱🇻": "Latvia", "🇱🇹": "Lithuania",
        }
        
        for server in self.servers:
            if server.get("status") != "online":
                continue
            if server["host"] in self.blacklist:
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
        
        countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))
        for servers in countries.values():
            servers.sort(key=lambda x: x["latency"])
        
        return countries
    
    def is_connected(self):
        try:
            result = subprocess.run(["pgrep", "-f", "xray"], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_current_server(self):
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                for line in f.readlines()[-20:]:
                    if "Подключение к серверу:" in line:
                        parts = line.split(":")
                        if len(parts) >= 3:
                            return parts[-2].strip()
        return None
    
    def start(self):
        try:
            subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
            subprocess.run(["pkill", "-f", "xray"], capture_output=True)
            time.sleep(1)
            
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:{HOME}/vpn-client/bin:" + env.get("PATH", "")
            
            subprocess.Popen(
                [str(CLIENT_SCRIPT), "start", "--auto", "--mode", "split"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            return True
        except Exception:
            return False
    
    def stop(self):
        try:
            subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
            subprocess.run(["pkill", "-f", "xray"], capture_output=True)
            return True
        except Exception:
            return False
    
    def update_servers(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:{HOME}/vpn-client/bin:" + env.get("PATH", "")
            subprocess.run([str(CLIENT_SCRIPT), "update"], env=env, timeout=60)
            self.load_data()
            return True
        except Exception:
            return False
    
    def get_logs(self, lines=50):
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            with open(log_file) as f:
                return f.readlines()[-lines:]
        return []


controller = VPNController()


# HTML страница
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 VLESS VPN</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .status {
            font-size: 1.5em;
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .status.connected { background: linear-gradient(45deg, #00b894, #00cec9); }
        .status.disconnected { background: linear-gradient(45deg, #636e72, #b2bec3); }
        .btn {
            width: 100%;
            padding: 20px;
            font-size: 1.3em;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .btn-connect { background: linear-gradient(45deg, #00b894, #00cec9); color: white; }
        .btn-disconnect { background: linear-gradient(45deg, #d63031, #e17055); color: white; }
        .btn-update { background: linear-gradient(45deg, #0984e3, #74b9ff); color: white; padding: 15px; font-size: 1.1em; }
        select {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #0984e3;
            border-radius: 10px;
            background: white;
            margin-bottom: 15px;
        }
        .server-list {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .server-item {
            padding: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
        }
        .server-item:hover { background: rgba(255,255,255,0.1); }
        .server-item.selected { background: rgba(0,184,148,0.3); }
        .logs {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .info-card {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .info-value { font-size: 1.5em; font-weight: bold; color: #00d9ff; }
        .info-label { font-size: 0.9em; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 VLESS VPN</h1>
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
        let countries = {};
        window.onload = function() { loadStatus(); loadCountries(); loadLogs(); setInterval(loadStatus, 5000); setInterval(loadLogs, 3000); };
        async function loadStatus() {
            const r = await fetch('/api/status');
            const d = await r.json();
            const statusEl = document.getElementById('status');
            const btn = document.getElementById('connectBtn');
            if (d.connected) {
                statusEl.className = 'status connected';
                statusEl.innerHTML = '🟢 Подключен<br><small>' + (d.server || '') + '</small>';
                btn.className = 'btn btn-disconnect';
                btn.innerHTML = '⏹️ Отключить';
                isConnected = true;
            } else {
                statusEl.className = 'status disconnected';
                statusEl.innerHTML = '⚪ Не подключен';
                btn.className = 'btn btn-connect';
                btn.innerHTML = '▶️ Подключить';
                isConnected = false;
            }
        }
        async function loadCountries() {
            const r = await fetch('/api/countries');
            const d = await r.json();
            countries = d.countries || {};
            const select = document.getElementById('countrySelect');
            select.innerHTML = '<option value="auto">⚡ Автовыбор</option>';
            for (const [country, servers] of Object.entries(countries)) {
                select.innerHTML += '<option value="'+country+'">'+country+' ('+servers.length+')</option>';
            }
            let total = Object.values(countries).reduce((a,b) => a+b.length, 0);
            document.getElementById('totalServers').textContent = total;
            document.getElementById('onlineServers').textContent = total;
            document.getElementById('countries').textContent = Object.keys(countries).length;
        }
        function onCountryChange() {
            const country = document.getElementById('countrySelect').value;
            const list = document.getElementById('serverList');
            if (!country || country === 'auto') { list.style.display = 'none'; selectedServer = null; return; }
            const servers = (countries[country] || []).sort((a,b) => a.latency - b.latency);
            list.innerHTML = '';
            servers.slice(0, 20).forEach((s, i) => {
                const item = document.createElement('div');
                item.className = 'server-item';
                item.innerHTML = (i+1) + '. ' + s.host + ':' + s.port + ' - ' + s.latency + ' мс';
                item.onclick = () => { document.querySelectorAll('.server-item').forEach(el => el.classList.remove('selected')); item.classList.add('selected'); selectedServer = s; };
                list.appendChild(item);
            });
            list.style.display = 'block';
        }
        async function toggleConnection() {
            const btn = document.getElementById('connectBtn');
            btn.disabled = true;
            if (isConnected) { await fetch('/api/stop', {method:'POST'}); }
            else { await fetch('/api/start', {method:'POST'}); }
            setTimeout(loadStatus, 2000);
            btn.disabled = false;
        }
        async function updateServers() {
            const btn = document.querySelector('.btn-update');
            btn.disabled = true;
            await fetch('/api/update', {method:'POST'});
            setTimeout(() => { loadCountries(); btn.disabled = false; }, 3000);
        }
        async function loadLogs() {
            const r = await fetch('/api/logs');
            const d = await r.json();
            document.getElementById('logs').innerHTML = d.logs.map(l => '<div>'+l+'</div>').join('');
        }
    </script>
</body>
</html>
"""


class VPNHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        
        elif parsed.path == '/api/status':
            controller.load_data()
            data = {
                "connected": controller.is_connected(),
                "server": controller.get_current_server()
            }
            self.send_json(data)
        
        elif parsed.path == '/api/countries':
            controller.load_data()
            data = {"countries": controller.get_countries()}
            self.send_json(data)
        
        elif parsed.path == '/api/logs':
            logs = controller.get_logs()
            data = {"logs": [line.strip() for line in logs]}
            self.send_json(data)
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/start':
            success = controller.start()
            self.send_json({"success": success})
        
        elif parsed.path == '/api/stop':
            success = controller.stop()
            self.send_json({"success": success})
        
        elif parsed.path == '/api/update':
            success = controller.update_servers()
            self.send_json({"success": success})
        
        else:
            self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Тихий режим


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌐 VLESS VPN Web Controller запущен!")
    print("=" * 60)
    print("\n📱 Открой в браузере: http://localhost:5000")
    print("=" * 60)
    print("\n💡 Работает БЕЗ Flask (встроенный HTTP сервер)")
    print("=" * 60)
    print("\nДля выхода: Ctrl+C")
    print("=" * 60 + "\n")
    
    with ThreadedHTTPServer(("", PORT), VPNHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Выход...")
            httpd.shutdown()
