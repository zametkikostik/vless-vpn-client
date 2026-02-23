#!/usr/bin/env python3
"""
VLESS VPN Client - Графический интерфейс
Для Linux Mint
"""

import sys
import os
import subprocess
import threading
import json
import time
from pathlib import Path
from datetime import datetime

# Проверка доступности PyQt5
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QProgressBar, QMessageBox,
                                  QCheckBox, QTabWidget, QSplitter)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("PyQt5 не установлен. Установите: pip3 install PyQt5")

# Пути
HOME = Path.home()
BASE_DIR = HOME / "vpn-client"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CLIENT_SCRIPT = HOME / ".local" / "bin" / "vless-vpn"

class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, command="start", mode="split"):
        super().__init__()
        self.command = command
        self.mode = mode
    
    def run(self):
        try:
            env = os.environ.copy()
            env["PATH"] = f"{HOME}/.local/bin:" + env.get("PATH", "")
            
            if self.command == "start":
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
                self.log_signal.emit("VPN остановлен")
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
                
            elif self.command == "update":
                cmd = [str(CLIENT_SCRIPT), "update"]
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
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
            self.finished_signal.emit(False)


class VPNClientGUI(QMainWindow):
    """Основное окно приложения с выбором локаций"""
    
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
        self.setWindowTitle("VLESS VPN Client")
        self.setMinimumSize(800, 600)
        
        # Центральное окно
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        header = QLabel("🔒 VLESS VPN Client")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2ecc71; padding: 10px;")
        main_layout.addWidget(header)
        
        # Статус подключения
        self.status_label = QLabel("⚪ Не подключен")
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Вкладка "Основное"
        main_tab = QWidget()
        tabs.addTab(main_tab, "🏠 Основное")
        main_tab_layout = QVBoxLayout(main_tab)
        
        # Выбор режима
        mode_group = QGroupBox("Режим работы")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🔀 Split - РФ напрямую, остальное через VPN", "split")
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN (рекомендуется для AI)", "full")
        self.mode_combo.setCurrentIndex(1)  # По умолчанию FULL для AI-сервисов
        
        # Чекбокс для AI-сервисов
        self.ai_mode_check = QCheckBox("🤖 AI-режим (Claude, ChatGPT, Lovable) - автоматически FULL")
        self.ai_mode_check.setChecked(True)
        self.ai_mode_check.stateChanged.connect(self.on_ai_mode_changed)
        mode_layout.addWidget(self.ai_mode_check)
        
        mode_layout.addWidget(QLabel("💡 Для Claude.com и Lovable.dev используйте Full режим!"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        main_tab_layout.addWidget(mode_group)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.setFont(QFont("Arial", 12, QFont.Bold))
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
        
        self.update_btn = QPushButton("🔄 Обновить серверы")
        self.update_btn.setFont(QFont("Arial", 10))
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
        
        main_tab_layout.addLayout(btn_layout)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel("Загрузка информации...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        main_tab_layout.addWidget(stats_group)
        
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
        
        # Автозапуск
        autostart_group = QGroupBox("Автозапуск")
        autostart_layout = QVBoxLayout()
        
        self.autostart_check = QCheckBox("Запускать VPN при загрузке системы")
        self.autostart_check.setChecked(self.check_autostart())
        self.autostart_check.stateChanged.connect(self.toggle_autostart)
        autostart_layout.addWidget(self.autostart_check)
        
        autostart_group.setLayout(autostart_layout)
        settings_layout.addWidget(autostart_group)
        
        # Информация
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Версия: 1.0.0"))
        info_layout.addWidget(QLabel("Протокол: VLESS-Reality"))
        info_layout.addWidget(QLabel("Порт SOCKS5: 10808"))
        info_layout.addWidget(QLabel("Порт HTTP: 10809"))
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
        self.timer.start(5000)  # Каждые 5 секунд
        
        # Загрузка логов
        self.load_logs()
        
    def init_tray(self):
        """Инициализация системного трея"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        # Иконка (если есть)
        # self.tray_icon.setIcon(QIcon("icon.png"))
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
        """Обработка клика по трею"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            
    def toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self.stop_vpn()
        else:
            self.start_vpn()
            
    def start_vpn(self):
        """Запуск VPN"""
        mode = self.mode_combo.currentData()
        self.log(f"Запуск VPN в режиме {mode.upper()}...")
        
        # Остановить старые процессы если есть
        try:
            subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
            subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
            time.sleep(1)
        except Exception:
            pass
        
        self.worker = VPNWorker("start", mode)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_start_finished)
        self.worker.start()
        
        self.connect_btn.setEnabled(True)  # Оставляем кнопку активной
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
        self.worker.finished_signal.connect(lambda: self.log("✅ Серверы обновлены"))
        self.worker.start()
        
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
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            self.statusBar.showMessage("VPN подключен")
            
            # Автоматическая настройка прокси для AI-сервисов
            self.setup_proxy_for_ai()

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
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.status_label.setText("⚪ Не подключен")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.statusBar.showMessage("VPN отключен")
        
    def update_status(self):
        """Обновление статуса"""
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
            self.stats_label.setText(output)
            
            # Проверка подключения
            if "✓ Подключен" in output or "Подключен:" in output:
                if not self.is_connected:
                    self.is_connected = True
                    self.connect_btn.setText("⏹️ Отключить")
                    self.status_label.setText("🟢 Подключен")
            elif "✗ Не подключен" in output:
                if self.is_connected:
                    self.is_connected = False
                    self.connect_btn.setText("▶️ Подключить")
                    self.status_label.setText("⚪ Не подключен")
                    
        except Exception as e:
            pass  # Тихо игнорируем ошибки статуса
            
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def load_logs(self):
        """Загрузка последних логов"""
        log_file = LOGS_DIR / "client.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]  # Последние 100 строк
                    for line in lines:
                        self.log_text.append(line.strip())
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
                
    def check_autostart(self):
        """Проверка автозапуска"""
        autostart_file = HOME / ".config" / "autostart" / "vpn-client.desktop"
        return autostart_file.exists()
        
    def toggle_autostart(self, state):
        """Переключение автозапуска"""
        script_path = Path(__file__).resolve().parent / "start-vpn-gui.sh"
        autostart_dir = HOME / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        autostart_file = autostart_dir / "vpn-client-gui.desktop"
        
        if state == Qt.Checked:
            desktop_entry = f"""[Desktop Entry]
Type=Application
Exec={script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=VLESS VPN Client
Comment=Запуск VPN клиента при загрузке
"""
            with open(autostart_file, "w") as f:
                f.write(desktop_entry)
            self.log("✅ Автозапуск включен")
        else:
            if autostart_file.exists():
                autostart_file.unlink()
            self.log("✅ Автозапуск выключен")
            
    def start_monitoring(self):
        """Запуск мониторинга процесса (только логирование)"""
        def monitor():
            while True:
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "vless-vpn"],
                        capture_output=True
                    )
                    connected = result.returncode == 0
                    # Только обновляем статус, не вызываем update_status()
                    if connected != self.is_connected:
                        self.is_connected = connected
                        if connected:
                            self.log("✅ VPN подключен (обнаружен процесс)")
                        else:
                            self.log("⚠️ VPN отключен (процесс не найден)")
                            self.connect_btn.setText("▶️ Подключить")
                except Exception as e:
                    pass
                import time
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def load_countries(self):
        """Загрузка списка стран из servers.json"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if not servers_file.exists():
                self.stats_label.setText("❌ Файл servers.json не найден.\nНажмите 🔄 Обновить серверы")
                return
            
            with open(servers_file, encoding='utf-8') as f:
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
                
                # Проверка на AI сервисы
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
                    countries[country] = 0
                countries[country] += 1
            
            # Сортировка по количеству серверов
            countries = dict(sorted(countries.items(), key=lambda x: x[1], reverse=True))
            self.countries = countries
            
            # Обновление статистики
            total_servers = sum(countries.values())
            total_countries = len(countries)
            ai_servers = countries.get("🤖 AI Services", 0)
            
            stats_text = f"📊 Статистика серверов:\n\n"
            stats_text += f"🌍 Всего серверов: {total_servers}\n"
            stats_text += f"🌐 Локаций: {total_countries}\n"
            if ai_servers > 0:
                stats_text += f"🤖 AI Services: {ai_servers} (ChatGPT, Claude, Lovable)\n"
            
            stats_text += f"\nТоп локаций:\n"
            for country, count in list(countries.items())[:5]:
                stats_text += f"  {country}: {count}\n"
            
            self.stats_label.setText(stats_text)
            self.log(f"✅ Загружено {total_countries} локаций, {total_servers} серверов")
            
        except Exception as e:
            self.stats_label.setText(f"❌ Ошибка загрузки: {e}")
            self.log(f"Ошибка загрузки стран: {e}")
    
    def on_ai_mode_changed(self, state):
        """Обработка переключения AI-режима"""
        if state == Qt.Checked:
            # Включить AI-режим - автоматически FULL
            self.mode_combo.setCurrentIndex(1)  # Full режим
            self.mode_combo.setEnabled(False)  # Заблокировать выбор
            self.log("✅ AI-режим включен - используется FULL режим для Claude/ChatGPT/Lovable")
        else:
            # Выключить AI-режим - разрешить выбор
            self.mode_combo.setEnabled(True)
            self.log("ℹ️ AI-режим выключен - можно выбрать режим вручную")
    
    def setup_proxy_for_ai(self):
        """Автоматическая настройка прокси для AI-сервисов"""
        try:
            # Настройка прокси в текущей сессии
            proxy_script = f"""
export all_proxy=socks5://127.0.0.1:10808
export http_proxy=http://127.0.0.1:10809
export https_proxy=http://127.0.0.1:10809
echo "✅ Прокси настроен для AI-сервисов"
"""
            # Сохраняем в файл для удобства
            proxy_file = Path.home() / ".vpn_proxy.sh"
            with open(proxy_file, 'w') as f:
                f.write(proxy_script)
            proxy_file.chmod(0o755)
            
            self.log("✅ Прокси настроен: socks5://127.0.0.1:10808")
            self.log("💡 Для доступа к Claude/Lovable используйте команду:")
            self.log(f"   source {proxy_file}")
            
        except Exception as e:
            self.log(f"⚠️ Не удалось настроить прокси: {e}")
        
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


def main():
    if not HAVE_PYQT5:
        print("=" * 60)
        print("❌ PyQt5 не установлен!")
        print("=" * 60)
        print("\nУстановите PyQt5 одной из команд:\n")
        print("  sudo apt install python3-pyqt5")
        print("  или")
        print("  pip3 install PyQt5")
        print("\n" + "=" * 60)
        sys.exit(1)
        
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
