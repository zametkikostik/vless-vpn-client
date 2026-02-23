#!/usr/bin/env python3
"""
VLESS VPN Web Controller - Быстрый веб-интерфейс
Работает через браузер, грузится мгновенно
"""

from flask import Flask, render_template_string, jsonify, request
import subprocess
import json
import os
import time
from pathlib import Path
from datetime import datetime
import threading

app = Flask(__name__)

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

# HTML шаблон (всё в одном файле для скорости)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
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
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-card {
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
        .status.connected {
            background: linear-gradient(45deg, #00b894, #00cec9);
        }
        .status.disconnected {
            background: linear-gradient(45deg, #636e72, #b2bec3);
        }
        .status.error {
            background: linear-gradient(45deg, #d63031, #e17055);
        }
        .btn {
            width: 100%;
            padding: 20px;
            font-size: 1.3em;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .btn-connect {
            background: linear-gradient(45deg, #00b894, #00cec9);
            color: white;
        }
        .btn-connect:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,184,148,0.3);
        }
        .btn-disconnect {
            background: linear-gradient(45deg, #d63031, #e17055);
            color: white;
        }
        .btn-update {
            background: linear-gradient(45deg, #0984e3, #74b9ff);
            color: white;
            padding: 15px;
            font-size: 1.1em;
        }
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
            transition: background 0.2s;
        }
        .server-item:hover {
            background: rgba(255,255,255,0.1);
        }
        .server-item.selected {
            background: rgba(0,184,148,0.3);
        }
        .logs {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }
        .log-line {
            padding: 3px 0;
            border-bottom: 1px solid #333;
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
        .info-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #00d9ff;
        }
        .info-label {
            font-size: 0.9em;
            opacity: 0.7;
        }
        .loading {
            text-align: center;
            padding: 20px;
            font-size: 1.2em;
            color: #00d9ff;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 VLESS VPN</h1>
        
        <div class="status-card">
            <div id="status" class="status disconnected">
                <div class="loading">Загрузка...</div>
            </div>
            
            <select id="countrySelect" onchange="onCountryChange()">
                <option value="">Загрузка...</option>
            </select>
            
            <div id="serverList" class="server-list" style="display:none;"></div>
            
            <button id="connectBtn" class="btn btn-connect" onclick="toggleConnection()">
                ▶️ Подключить
            </button>
            
            <button class="btn btn-update" onclick="updateServers()">
                🔄 Обновить серверы
            </button>
        </div>
        
        <div class="status-card">
            <h3>📊 Статистика</h3>
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-value" id="totalServers">-</div>
                    <div class="info-label">Всего серверов</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="onlineServers">-</div>
                    <div class="info-label">Онлайн</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="countries">-</div>
                    <div class="info-label">Стран</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="currentLatency">-</div>
                    <div class="info-label">Задержка (мс)</div>
                </div>
            </div>
        </div>
        
        <div class="status-card">
            <h3>📋 Логи</h3>
            <div id="logs" class="logs">
                <div class="loading">Загрузка логов...</div>
            </div>
        </div>
    </div>
    
    <script>
        let isConnected = false;
        let selectedServer = null;
        let countries = {};
        
        // Загрузка при старте
        window.onload = function() {
            loadStatus();
            loadCountries();
            loadLogs();
            setInterval(loadStatus, 5000);
            setInterval(loadLogs, 3000);
        };
        
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusEl = document.getElementById('status');
                const connectBtn = document.getElementById('connectBtn');
                
                if (data.connected) {
                    statusEl.className = 'status connected';
                    statusEl.innerHTML = '🟢 Подключен<br><small>' + (data.server || '') + '</small>';
                    connectBtn.className = 'btn btn-disconnect';
                    connectBtn.innerHTML = '⏹️ Отключить';
                    isConnected = true;
                    
                    document.getElementById('currentLatency').textContent = data.latency || '-';
                } else {
                    statusEl.className = 'status disconnected';
                    statusEl.innerHTML = '⚪ Не подключен';
                    connectBtn.className = 'btn btn-connect';
                    connectBtn.innerHTML = '▶️ Подключить';
                    isConnected = false;
                    document.getElementById('currentLatency').textContent = '-';
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        async function loadCountries() {
            try {
                const response = await fetch('/api/countries');
                const data = await response.json();
                countries = data.countries || {};
                
                const select = document.getElementById('countrySelect');
                select.innerHTML = '<option value="auto">⚡ Автовыбор (лучший сервер)</option>';
                
                for (const [country, servers] of Object.entries(countries)) {
                    select.innerHTML += `<option value="${country}">${country} (${servers.length} серверов)</option>`;
                }
                
                // Статистика
                let totalServers = 0;
                for (const servers of Object.values(countries)) {
                    totalServers += servers.length;
                }
                document.getElementById('totalServers').textContent = totalServers;
                document.getElementById('onlineServers').textContent = totalServers;
                document.getElementById('countries').textContent = Object.keys(countries).length;
                
            } catch (e) {
                console.error(e);
            }
        }
        
        function onCountryChange() {
            const country = document.getElementById('countrySelect').value;
            const serverList = document.getElementById('serverList');
            
            if (!country || country === 'auto') {
                serverList.style.display = 'none';
                selectedServer = null;
                return;
            }
            
            const servers = countries[country] || [];
            servers.sort((a, b) => a.latency - b.latency);
            
            serverList.innerHTML = '';
            servers.slice(0, 20).forEach((server, i) => {
                const item = document.createElement('div');
                item.className = 'server-item';
                item.innerHTML = `${i+1}. ${server.host}:${server.port} - ${server.latency} мс | ${server.name || ''}`;
                item.onclick = () => selectServer(server, item);
                serverList.appendChild(item);
            });
            
            serverList.style.display = 'block';
        }
        
        function selectServer(server, element) {
            document.querySelectorAll('.server-item').forEach(el => el.classList.remove('selected'));
            element.classList.add('selected');
            selectedServer = server;
        }
        
        async function toggleConnection() {
            const country = document.getElementById('countrySelect').value;
            const btn = document.getElementById('connectBtn');
            btn.disabled = true;
            
            try {
                if (isConnected) {
                    await fetch('/api/stop', { method: 'POST' });
                } else {
                    await fetch('/api/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            country: country === 'auto' ? null : country,
                            server: selectedServer
                        })
                    });
                }
                setTimeout(loadStatus, 2000);
            } catch (e) {
                console.error(e);
            }
            
            btn.disabled = false;
        }
        
        async function updateServers() {
            const btn = document.querySelector('.btn-update');
            btn.disabled = true;
            btn.innerHTML = '⏳ Обновление...';
            
            try {
                await fetch('/api/update', { method: 'POST' });
                setTimeout(() => {
                    loadCountries();
                    btn.innerHTML = '🔄 Обновить серверы';
                    btn.disabled = false;
                }, 3000);
            } catch (e) {
                console.error(e);
                btn.disabled = false;
            }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                
                const logsEl = document.getElementById('logs');
                logsEl.innerHTML = data.logs.map(line => 
                    `<div class="log-line">${line}</div>`
                ).join('');
                
                logsEl.scrollTop = logsEl.scrollHeight;
            } catch (e) {
                console.error(e);
            }
        }
    </script>
</body>
</html>
"""

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
    
    def start(self, country=None, server=None):
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
        except Exception as e:
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


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def api_status():
    return jsonify({
        "connected": controller.is_connected(),
        "server": controller.get_current_server(),
        "latency": "-"
    })


@app.route('/api/countries')
def api_countries():
    controller.load_data()
    return jsonify({"countries": controller.get_countries()})


@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.json or {}
    success = controller.start(data.get('country'), data.get('server'))
    return jsonify({"success": success})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    success = controller.stop()
    return jsonify({"success": success})


@app.route('/api/update', methods=['POST'])
def api_update():
    success = controller.update_servers()
    return jsonify({"success": success})


@app.route('/api/logs')
def api_logs():
    logs = controller.get_logs()
    return jsonify({"logs": [line.strip() for line in logs]})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌐 VLESS VPN Web Controller запущен!")
    print("=" * 60)
    print("\nОткрой в браузере: http://localhost:5000")
    print("=" * 60)
    print("\nДля выхода: Ctrl+C")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
