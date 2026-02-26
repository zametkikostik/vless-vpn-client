#!/usr/bin/env python3
"""
VLESS VPN Client GUI v4.0 - Professional Edition
Единый клиент для Linux Mint с поддержкой VLESS-Reality
Обход DPI, Split-tunneling, автозагрузка списков из GitHub

© 2026 VPN Client Aggregator
"""

import sys
import os
import subprocess
import threading
import json
import time
import socket
import signal
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QSystemTrayIcon, QMenu, QAction,
                                  QStatusBar, QProgressBar, QMessageBox,
                                  QCheckBox, QTabWidget, QGridLayout, QScrollArea,
                                  QGroupBox, QSpinBox, QLineEdit, QFileDialog,
                                  QDialog, QDialogButtonBox, QFormLayout)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
    from PyQt5.QtGui import QIcon, QFont, QDesktopServices, QPalette, QColor
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен. Установите: pip3 install PyQt5")
    sys.exit(1)

# =============================================================================
# КОНСТАНТЫ И ПУТИ
# =============================================================================
HOME = Path.home()
BASE_DIR = HOME / "vpn-client-aggregator"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
XRAY_DIR = BASE_DIR / "xray"

# Пути к исполняемым файлам
XRAY_BIN = "/usr/local/bin/xray"
VPN_GUI_LINK = "/usr/local/bin/vpn-gui"

# GitHub репозитории для списков
GITHUB_REPO = "https://raw.githubusercontent.com"
WHITE_LIST_URL = f"{GITHUB_REPO}/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
GEOIP_URL = "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat"
GEOSITE_URL = "https://github.com/v2fly/domain-list-community/releases/latest/download/geosite.dat"

# Создаём директории
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR, XRAY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================================
# ЛОГИРОВАНИЕ
# =============================================================================
class Logger:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def info(self, msg): self.log(msg, "INFO")
    def error(self, msg): self.log(msg, "ERROR")
    def warn(self, msg): self.log(msg, "WARN")
    def debug(self, msg): self.log(msg, "DEBUG")

logger = Logger(LOGS_DIR / "vpn-gui.log")

# =============================================================================
# МОНТОРИНГ ТРАФИКА
# =============================================================================
class TrafficMonitor:
    def __init__(self):
        self.upload_speed = 0
        self.download_speed = 0
        self.total_upload = 0
        self.total_download = 0
        self.last_rx = 0
        self.last_tx = 0
        self.last_check = time.time()
    
    def get_traffic_stats(self) -> tuple:
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
            
            total_rx = 0
            total_tx = 0
            
            for line in lines[2:]:
                if any(x in line for x in ['tun', 'tap', 'xray']):
                    parts = line.split(':')
                    if len(parts) > 1:
                        stats = parts[1].split()
                        total_rx += int(stats[0])
                        total_tx += int(stats[8])
            
            current_time = time.time()
            elapsed = current_time - self.last_check
            
            if elapsed > 0:
                self.download_speed = max(0, (total_rx - self.last_rx) / elapsed)
                self.upload_speed = max(0, (total_tx - self.last_tx) / elapsed)
            
            self.last_rx = total_rx
            self.last_tx = total_tx
            self.last_check = current_time
            self.total_download = total_rx
            self.total_upload = total_tx
            
            return total_rx, total_tx
        except Exception as e:
            logger.error(f"Traffic monitor error: {e}")
            return 0, 0
    
    def format_speed(self, bytes_per_sec: float) -> str:
        if bytes_per_sec > 1048576:
            return f"{bytes_per_sec / 1048576:.2f} MB/s"
        elif bytes_per_sec > 1024:
            return f"{bytes_per_sec / 1024:.2f} KB/s"
        else:
            return f"{bytes_per_sec:.0f} B/s"
    
    def format_total(self, bytes_total: int) -> str:
        if bytes_total > 1073741824:
            return f"{bytes_total / 1073741824:.2f} GB"
        elif bytes_total > 1048576:
            return f"{bytes_total / 1048576:.2f} MB"
        else:
            return f"{bytes_total / 1024:.2f} KB"

# =============================================================================
# ЗАГРУЗКА СПИСКОВ ИЗ GITHUB
# =============================================================================
class GitHubListsLoader:
    @staticmethod
    def download_file(url: str, dest: Path) -> bool:
        try:
            logger.info(f"Загрузка {url}...")
            with urllib.request.urlopen(url, timeout=30) as response:
                with open(dest, 'wb') as out_file:
                    out_file.write(response.read())
            logger.info(f"Загружено в {dest}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            return False
    
    @staticmethod
    def load_white_list() -> List[str]:
        """Загрузка белого списка доменов"""
        white_list_file = DATA_DIR / "white_list.txt"
        
        if not white_list_file.exists() or (time.time() - white_list_file.stat().st_mtime) > 86400:
            GitHubListsLoader.download_file(WHITE_LIST_URL, white_list_file)
        
        domains = []
        if white_list_file.exists():
            with open(white_list_file, 'r', encoding='utf-8') as f:
                for line in f:
                    domain = line.strip()
                    if domain and not domain.startswith('#'):
                        domains.append(domain)
        
        return list(set(domains))
    
    @staticmethod
    def load_domain_lists() -> Dict[str, List[str]]:
        """Загрузка всех списков доменов"""
        lists_file = DATA_DIR / "domain-lists.json"
        
        default_lists = {
            "social": ["facebook.com", "instagram.com", "twitter.com", "tiktok.com", "telegram.org", "whatsapp.com", "discord.com"],
            "video": ["youtube.com", "ytimg.com", "googlevideo.com", "vimeo.com", "twitch.tv"],
            "ai": ["openai.com", "chatgpt.com", "claude.ai", "anthropic.com", "gemini.google.com", "midjourney.com", "huggingface.co"],
            "blocked": ["meduza.io", "reuters.com", "bloomberg.com", "nytimes.com", "theguardian.com", "bbc.com"],
            "russian_direct": ["vk.com", "yandex.ru", "mail.ru", "ok.ru", "gosuslugi.ru", "sberbank.ru"]
        }
        
        if lists_file.exists():
            try:
                with open(lists_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        with open(lists_file, 'w', encoding='utf-8') as f:
            json.dump(default_lists, f, indent=2)
        
        return default_lists

# =============================================================================
# VPN WORKER
# =============================================================================
class VPNWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, command: str = "start", mode: str = "split"):
        super().__init__()
        self.command = command
        self.mode = mode
        self.process: Optional[subprocess.Popen] = None
    
    def run(self):
        try:
            if self.command == "start":
                self.start_vpn()
            elif self.command == "stop":
                self.stop_vpn()
            elif self.command == "restart":
                self.stop_vpn()
                time.sleep(2)
                self.start_vpn()
            elif self.command == "status":
                self.check_status()
        except Exception as e:
            logger.error(f"VPN Worker error: {e}")
            self.log_signal.emit(f"❌ Ошибка: {e}")
            self.finished_signal.emit(False)
    
    def start_vpn(self):
        self.log_signal.emit("🚀 Запуск VPN...")
        logger.info("Запуск VPN")
        
        try:
            config_file = CONFIG_DIR / "config.json"
            if not config_file.exists():
                self.log_signal.emit("❌ Конфигурация не найдена!")
                self.finished_signal.emit(False)
                return
            
            cmd = [XRAY_BIN, "run", "-c", str(config_file)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            time.sleep(3)
            
            if self.process.poll() is None:
                self.log_signal.emit("✅ VPN подключён")
                logger.info("VPN запущен успешно")
                self.status_signal.emit({"connected": True, "mode": self.mode})
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit("❌ Не удалось запустить VPN")
                self.finished_signal.emit(False)
                
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка: {e}")
            self.finished_signal.emit(False)
    
    def stop_vpn(self):
        self.log_signal.emit("🛑 Остановка VPN...")
        logger.info("Остановка VPN")
        
        try:
            subprocess.run(["pkill", "-f", "xray.*run"], timeout=5)
            time.sleep(1)
            subprocess.run(["pkill", "-9", "xray"], timeout=5)
        except:
            pass
        
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except:
                pass
        
        self.log_signal.emit("⏹️ VPN отключён")
        self.status_signal.emit({"connected": False})
        self.finished_signal.emit(True)
    
    def check_status(self):
        try:
            result = subprocess.run(
                ["pgrep", "-f", "xray.*run"],
                capture_output=True,
                text=True
            )
            connected = result.returncode == 0
            self.status_signal.emit({"connected": connected})
        except:
            self.status_signal.emit({"connected": False})

# =============================================================================
# ГЛАВНОЕ ОКНО
# =============================================================================
class VPNClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.traffic = TrafficMonitor()
        self.worker: Optional[VPNWorker] = None
        self.is_connected = False
        self.domain_lists = {}
        self.init_ui()
        self.load_config()
        self.start_traffic_monitor()
        logger.info("GUI запущен")
    
    def init_ui(self):
        self.setWindowTitle("🛡️ VLESS VPN Client v4.0")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5CBF60, stop:1 #55b05a);
            }
            QPushButton:disabled {
                background: #666666;
            }
            QPushButton#stopBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f44336, stop:1 #da190b);
            }
            QPushButton#stopBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f55548, stop:1 #e82a1e);
            }
            QTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Monospace';
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                color: #58a6ff;
                border: 2px solid #30363d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox, QSpinBox, QLineEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 8px;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                background: #0d1117;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #161b22;
                color: #8b949e;
                padding: 8px 16px;
                border: 1px solid #30363d;
            }
            QTabBar::tab:selected {
                background: #0d1117;
                color: #58a6ff;
            }
            QCheckBox {
                color: #c9d1d9;
                spacing: 8px;
            }
            QLabel {
                color: #c9d1d9;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = QHBoxLayout()
        title = QLabel("🛡️ VLESS VPN Client v4.0 Professional")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #58a6ff;")
        header.addWidget(title)
        header.addStretch()
        
        self.status_label = QLabel("⏹️ Отключён")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setStyleSheet("color: #f44336; padding: 8px 16px; background: #1e1e1e; border-radius: 4px;")
        header.addWidget(self.status_label)
        
        main_layout.addLayout(header)
        
        # Основная панель управления
        control_group = QGroupBox("🎮 Управление")
        control_layout = QGridLayout(control_group)
        
        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_btn, 0, 0)
        
        self.disconnect_btn = QPushButton("⏹️ Отключить")
        self.disconnect_btn.setObjectName("stopBtn")
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        control_layout.addWidget(self.disconnect_btn, 0, 1)
        
        self.restart_btn = QPushButton("🔄 Перезапустить")
        self.restart_btn.clicked.connect(self.restart)
        self.restart_btn.setEnabled(False)
        control_layout.addWidget(self.restart_btn, 0, 2)
        
        # Режим работы
        control_layout.addWidget(QLabel("Режим:"), 1, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Split-tunneling (умный)", "Все через VPN", "Прямое подключение"])
        control_layout.addWidget(self.mode_combo, 1, 1, 1, 2)
        
        main_layout.addWidget(control_group)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Статистика
        stats_tab = QWidget()
        stats_layout = QGridLayout(stats_tab)
        
        self.speed_label = QLabel("📊 Скорость: ↓ 0 KB/s ↑ 0 KB/s")
        self.speed_label.setFont(QFont("Monospace", 12))
        stats_layout.addWidget(self.speed_label, 0, 0)
        
        self.traffic_label = QLabel("📈 Трафик: ↓ 0 MB ↑ 0 MB")
        self.traffic_label.setFont(QFont("Monospace", 12))
        stats_layout.addWidget(self.traffic_label, 1, 0)
        
        self.uptime_label = QLabel("⏱️ Время: 00:00:00")
        self.uptime_label.setFont(QFont("Monospace", 12))
        stats_layout.addWidget(self.uptime_label, 2, 0)
        
        stats_layout.addWidget(QLabel("📥 Download:"), 3, 0)
        self.dl_progress = QProgressBar()
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setValue(0)
        stats_layout.addWidget(self.dl_progress, 3, 1)
        
        stats_layout.addWidget(QLabel("📤 Upload:"), 4, 0)
        self.ul_progress = QProgressBar()
        self.ul_progress.setRange(0, 100)
        self.ul_progress.setValue(0)
        stats_layout.addWidget(self.ul_progress, 4, 1)
        
        tabs.addTab(stats_tab, "📊 Статистика")
        
        # Вкладка 2: Настройки
        settings_tab = QWidget()
        settings_layout = QFormLayout(settings_tab)
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("IP или домен сервера")
        settings_layout.addRow("Сервер:", self.server_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(443)
        settings_layout.addRow("Порт:", self.port_input)
        
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("UUID клиента")
        settings_layout.addRow("UUID:", self.uuid_input)
        
        self.sni_input = QLineEdit()
        self.sni_input.setText("google.com")
        settings_layout.addRow("SNI:", self.sni_input)
        
        settings_layout.addRow(QLabel(""))
        
        load_lists_btn = QPushButton("📥 Загрузить списки из GitHub")
        load_lists_btn.clicked.connect(self.load_domain_lists)
        settings_layout.addRow(load_lists_btn)
        
        self.auto_update_check = QCheckBox("Автообновление списков (24ч)")
        self.auto_update_check.setChecked(True)
        settings_layout.addRow(self.auto_update_check)
        
        self.kill_switch_check = QCheckBox("Kill Switch (блокировка при обрыве)")
        settings_layout.addRow(self.kill_switch_check)
        
        self.autostart_check = QCheckBox("Автозапуск при входе")
        settings_layout.addRow(self.autostart_check)
        
        save_btn = QPushButton("💾 Сохранить настройки")
        save_btn.clicked.connect(self.save_config)
        settings_layout.addRow(save_btn)
        
        tabs.addTab(settings_tab, "⚙️ Настройки")
        
        # Вкладка 3: Списки доменов
        lists_tab = QWidget()
        lists_layout = QVBoxLayout(lists_tab)
        
        lists_layout.addWidget(QLabel("📋 Списки для раздельного туннелирования:"))
        
        self.lists_combo = QComboBox()
        self.lists_combo.addItems(["Соцсети", "Видеохостинги", "ИИ-сервисы", "Заблокированные", "РФ (напрямую)"])
        self.lists_combo.currentIndexChanged.connect(self.show_domain_list)
        lists_layout.addWidget(self.lists_combo)
        
        self.domains_text = QTextEdit()
        self.domains_text.setReadOnly(True)
        self.domains_text.setMaximumHeight(300)
        lists_layout.addWidget(self.domains_text)
        
        refresh_btn = QPushButton("🔄 Обновить списки")
        refresh_btn.clicked.connect(self.load_domain_lists)
        lists_layout.addWidget(refresh_btn)
        
        tabs.addTab(lists_tab, "📋 Списки")
        
        # Вкладка 4: Логи
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 10))
        logs_layout.addWidget(self.log_text)
        
        clear_logs_btn = QPushButton("🗑️ Очистить логи")
        clear_logs_btn.clicked.connect(self.log_text.clear)
        logs_layout.addWidget(clear_logs_btn)
        
        tabs.addTab(logs_tab, "📜 Логи")
        
        main_layout.addWidget(tabs)
        
        # Статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
        
        # Системный трей
        self.init_tray()
        
        self.show()
    
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_NetworkDrive))
        
        tray_menu = QMenu()
        
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        self.tray_toggle_action = QAction("Подключить", self)
        self.tray_toggle_action.triggered.connect(self.toggle_connection)
        tray_menu.addAction(self.tray_toggle_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def load_config(self):
        config_file = CONFIG_DIR / "gui-config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.server_input.setText(config.get('server', ''))
                self.port_input.setValue(config.get('port', 443))
                self.uuid_input.setText(config.get('uuid', ''))
                self.sni_input.setText(config.get('sni', 'google.com'))
                self.mode_combo.setCurrentIndex(config.get('mode_index', 0))
                self.auto_update_check.setChecked(config.get('auto_update', True))
                self.kill_switch_check.setChecked(config.get('kill_switch', False))
                self.autostart_check.setChecked(config.get('autostart', False))
                self.log("✅ Конфигурация загружена")
            except Exception as e:
                self.log(f"⚠️ Ошибка загрузки конфига: {e}")
    
    def save_config(self):
        config = {
            'server': self.server_input.text(),
            'port': self.port_input.value(),
            'uuid': self.uuid_input.text(),
            'sni': self.sni_input.text(),
            'mode_index': self.mode_combo.currentIndex(),
            'auto_update': self.auto_update_check.isChecked(),
            'kill_switch': self.kill_switch_check.isChecked(),
            'autostart': self.autostart_check.isChecked()
        }
        
        config_file = CONFIG_DIR / "gui-config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        self.generate_xray_config()
        self.log("✅ Конфигурация сохранена")
        QMessageBox.information(self, "Сохранено", "Настройки сохранены!")
    
    def generate_xray_config(self):
        config = {
            "log": {
                "loglevel": "warning",
                "access": str(LOGS_DIR / "access.log"),
                "error": str(LOGS_DIR / "error.log")
            },
            "inbounds": [{
                "port": 10808,
                "protocol": "socks",
                "settings": {
                    "auth": "noauth",
                    "udp": True
                }
            }],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": self.server_input.text() or "127.0.0.1",
                        "port": self.port_input.value(),
                        "users": [{
                            "id": self.uuid_input.text(),
                            "flow": "xtls-rprx-vision",
                            "encryption": "none"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "show": False,
                        "fingerprint": "chrome",
                        "serverName": self.sni_input.text(),
                        "shortId": "",
                        "spiderX": ""
                    }
                }
            }],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": []
            }
        }
        
        mode_index = self.mode_combo.currentIndex()
        if mode_index == 0:  # Split-tunneling
            self.domain_lists = GitHubListsLoader.load_domain_lists()
            vpn_domains = []
            for category in ["social", "video", "ai", "blocked"]:
                vpn_domains.extend(self.domain_lists.get(category, []))
            
            if vpn_domains:
                config["routing"]["rules"].append({
                    "type": "field",
                    "domain": vpn_domains,
                    "outboundTag": "proxy"
                })
                config["routing"]["rules"].append({
                    "type": "field",
                    "ip": ["geoip:private"],
                    "outboundTag": "direct"
                })
                config["outbounds"].append({
                    "protocol": "freedom",
                    "tag": "direct"
                })
                config["outbounds"][0]["tag"] = "proxy"
        
        config_file = CONFIG_DIR / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Xray конфигурация сгенерирована")
    
    def load_domain_lists(self):
        self.log("📥 Загрузка списков из GitHub...")
        self.domain_lists = GitHubListsLoader.load_domain_lists()
        
        white_list = GitHubListsLoader.load_white_list()
        if white_list:
            self.log(f"✅ Загружено {len(white_list)} доменов из белого списка")
        
        self.show_domain_list()
        self.log("✅ Списки загружены")
    
    def show_domain_list(self):
        index = self.lists_combo.currentIndex()
        categories = ["social", "video", "ai", "blocked", "russian_direct"]
        names = ["Соцсети", "Видеохостинги", "ИИ-сервисы", "Заблокированные", "РФ (напрямую)"]
        
        if not self.domain_lists:
            self.domain_lists = GitHubListsLoader.load_domain_lists()
        
        category = categories[index]
        domains = self.domain_lists.get(category, [])
        
        self.domains_text.setText(f"{names[index]} ({len(domains)} доменов):\n\n" + "\n".join(sorted(domains)))
    
    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        if not self.server_input.text() or not self.uuid_input.text():
            QMessageBox.warning(self, "Ошибка", "Заполните сервер и UUID!")
            return
        
        self.save_config()
        
        self.worker = VPNWorker("start", self.mode_combo.currentText())
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_connect_finished)
        self.worker.start()
        
        self.connect_btn.setEnabled(False)
        self.statusBar.showMessage("Подключение...")
    
    def disconnect(self):
        self.worker = VPNWorker("stop")
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_disconnect_finished)
        self.worker.start()
    
    def restart(self):
        self.worker = VPNWorker("restart")
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.start()
    
    def update_status(self, status: dict):
        self.is_connected = status.get("connected", False)
        
        if self.is_connected:
            self.status_label.setText("✅ Подключён")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 8px 16px; background: #1e3a1e; border-radius: 4px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)
            self.tray_toggle_action.setText("Отключить")
        else:
            self.status_label.setText("⏹️ Отключён")
            self.status_label.setStyleSheet("color: #f44336; padding: 8px 16px; background: #1e1e1e; border-radius: 4px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            self.tray_toggle_action.setText("Подключить")
    
    def on_connect_finished(self, success: bool):
        if success:
            self.statusBar.showMessage("VPN подключён")
        else:
            self.statusBar.showMessage("Ошибка подключения")
    
    def on_disconnect_finished(self, success: bool):
        self.statusBar.showMessage("VPN отключён")
        self.connect_btn.setEnabled(True)
    
    def start_traffic_monitor(self):
        self.traffic_timer = QTimer()
        self.traffic_timer.timeout.connect(self.update_traffic)
        self.traffic_timer.start(1000)
        
        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        self.uptime_timer.start(1000)
        
        self.connection_start_time = None
    
    def update_traffic(self):
        rx, tx = self.traffic.get_traffic_stats()
        
        dl_speed = self.traffic.format_speed(self.traffic.download_speed)
        ul_speed = self.traffic.format_speed(self.traffic.upload_speed)
        dl_total = self.traffic.format_total(self.traffic.total_download)
        ul_total = self.traffic.format_total(self.traffic.total_upload)
        
        self.speed_label.setText(f"📊 Скорость: ↓ {dl_speed} ↑ {ul_speed}")
        self.traffic_label.setText(f"📈 Трафик: ↓ {dl_total} ↑ {ul_total}")
        
        self.dl_progress.setValue(min(100, int(self.traffic.download_speed / 1024)))
        self.ul_progress.setValue(min(100, int(self.traffic.upload_speed / 1024)))
    
    def update_uptime(self):
        if self.is_connected:
            if not self.connection_start_time:
                self.connection_start_time = time.time()
            
            elapsed = int(time.time() - self.connection_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.uptime_label.setText(f"⏱️ Время: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.connection_start_time = None
            self.uptime_label.setText("⏱️ Время: 00:00:00")
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        logger.info(message)
        self.statusBar.showMessage(message, 5000)
    
    def closeEvent(self, event):
        if self.is_connected:
            reply = QMessageBox.question(
                self, "Выход",
                "VPN подключён. Отключить и выйти?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.disconnect()
                time.sleep(2)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

# =============================================================================
# ЗАПУСК
# =============================================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VLESS VPN Client")
    app.setOrganizationName("VPN Aggregator")
    
    window = VPNClientWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
