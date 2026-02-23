#!/usr/bin/env python3
"""
VLESS VPN Client - SIMPLE GUI
Простой интерфейс с БОЛЬШОЙ кнопкой подключения!
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QGroupBox, QSystemTrayIcon, QMenu,
                                  QAction, QStatusBar, QMessageBox)
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
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


class VPNClientSimpleGUI(QMainWindow):
    """Простой GUI с большой кнопкой"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.is_connected = False
        self.init_ui()
        self.start_monitoring()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🔒 VLESS VPN Client - SIMPLE")
        self.setMinimumSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Заголовок
        header = QLabel("🔒 VLESS VPN Client\nПростая версия")
        header.setFont(QFont("Arial", 24, QFont.Bold))
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

        # Статус
        self.status_label = QLabel("⚪ НЕ ПОДКЛЮЧЕН")
        self.status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin: 15px;
            }
        """)
        main_layout.addWidget(self.status_label)

        # БОЛЬШАЯ КНОПКА ПОДКЛЮЧЕНИЯ
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
        main_layout.addWidget(self.connect_btn)

        # Режим
        mode_group = QGroupBox("⚙️ Режим работы")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🌐 Full - Весь трафик через VPN", "full")
        self.mode_combo.addItem("🔀 Split - РФ напрямую", "split")
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # Логи
        log_group = QGroupBox("📋 Логи")
        log_layout = QVBoxLayout()
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
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Строка состояния
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")

        # Трей
        self.init_tray()

        # Таймер
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.load_logs()

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

        # Остановить старое
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True, timeout=3)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True, timeout=3)
        time.sleep(2)

        # Запустить
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

        # Чтение логов
        def read_log():
            for line in self.worker.stdout:
                self.log(line.strip())
        
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("⏳ ПОДКЛЮЧЕНИЕ...")
        self.status_label.setText("🟡 ПОДКЛЮЧЕНИЕ...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f39c12;
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin: 15px;
            }
        """)

    def stop_vpn(self):
        """Остановка VPN"""
        self.log("🛑 Остановка VPN...")
        subprocess.run(["pkill", "-f", "vless-vpn"], capture_output=True)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True)
        
        self.is_connected = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")
        self.status_label.setText("⚪ НЕ ПОДКЛЮЧЕН")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin: 15px;
            }
        """)
        self.statusBar.showMessage("VPN отключен")

    def update_status(self):
        """Обновление статуса"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "xray"],
                capture_output=True
            )
            connected = result.returncode == 0
            
            if connected and not self.is_connected:
                self.is_connected = True
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("⏹️ ОТКЛЮЧИТЬ")
                self.connect_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                        color: white;
                        border-radius: 15px;
                        padding: 20px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #a93226);
                    }
                """)
                self.status_label.setText("🟢 ПОДКЛЮЧЕН")
                self.status_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #2ecc71);
                        color: white;
                        padding: 30px;
                        border-radius: 15px;
                        margin: 15px;
                    }
                """)
                self.statusBar.showMessage("✅ VPN подключен")
                self.log("✅ VPN подключен!")
            elif not connected and self.is_connected:
                self.is_connected = False
                self.connect_btn.setText("▶️ ПОДКЛЮЧИТЬ")
                self.status_label.setText("⚪ НЕ ПОДКЛЮЧЕН")
        except Exception:
            pass

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
                    lines = f.readlines()[-50:]
                    for line in lines:
                        self.log_text.append(line.strip())
            except Exception:
                pass

    def start_monitoring(self):
        """Мониторинг"""
        def monitor():
            while True:
                time.sleep(5)
        
        import threading
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
    app.setApplicationName("VLESS VPN Client - SIMPLE")

    window = VPNClientSimpleGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
