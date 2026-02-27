#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
GUI Interface - Графический интерфейс пользователя (PyQt5)

© 2026 VPN Client Aggregator
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                  QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                  QComboBox, QSystemTrayIcon, QMenu, QAction,
                                  QStatusBar, QProgressBar, QMessageBox,
                                  QCheckBox, QTabWidget, QGridLayout, QGroupBox,
                                  QScrollArea, QSpinBox, QLineEdit, QFileDialog,
                                  QFormLayout, QSplitter, QFrame, QStyle)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
    from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QBrush, QDesktopServices
    HAVE_PYQT5 = True
except ImportError:
    HAVE_PYQT5 = False
    print("❌ PyQt5 не установлен. Установите: pip3 install PyQt5")
    sys.exit(1)

# Импорты локальных модулей
from vpn_controller import VPNController
from config_manager import ConfigManager
from domain_lists import DomainListsLoader

# =============================================================================
# КОНСТАНТЫ
# =============================================================================

HOME = Path.home()
BASE_DIR = HOME / "vpn-client-aggregator"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Создание директорий
for d in [CONFIG_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================================
# WORKER ПОТОК ДЛЯ VPN ОПЕРАЦИЙ
# =============================================================================

class VPNWorker(QThread):
    """Рабочий поток для VPN операций"""

    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(bool)

    def __init__(self, command: str = "start"):
        super().__init__()
        self.command = command
        self.controller: Optional[VPNController] = None

    def set_controller(self, controller: VPNController):
        self.controller = controller

    def run(self):
        if not self.controller:
            self.finished_signal.emit(False)
            return

        try:
            import asyncio
            
            if self.command == "start":
                # Запускаем в новом event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.controller.start())
                finally:
                    loop.close()
            elif self.command == "stop":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.controller.stop())
                finally:
                    loop.close()
            elif self.command == "restart":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.controller.restart())
                finally:
                    loop.close()
            else:
                result = False

            self.finished_signal.emit(result)

        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка: {e}")
            import traceback
            self.log_signal.emit(f"📋 {traceback.format_exc()}")
            self.finished_signal.emit(False)


# =============================================================================
# ГЛАВНОЕ ОКНО
# =============================================================================

class VPNClientWindow(QMainWindow):
    """Главное окно VPN клиента"""
    
    def __init__(self):
        super().__init__()
        
        # Инициализация контроллера
        self.controller = VPNController()
        self.controller.initialize()
        
        # Worker поток
        self.worker: Optional[VPNWorker] = None
        
        # Состояние
        self.is_connected = False
        self.connection_start_time: Optional[datetime] = None
        
        # Загрузка списков доменов
        self.domain_loader = DomainListsLoader()
        self.domain_lists = self.domain_loader.load_domain_lists()
        
        # Инициализация UI
        self.init_ui()
        self.load_config()
        self.auto_fill_server()  # Автозаполнение из загруженных серверов
        self.start_timers()

        self.log("✅ VPN Client v5.0 запущен")
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("🛡️ VPN Client Aggregator v5.0")
        self.setMinimumSize(1000, 750)
        
        # Стили
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }

            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f4c75, stop:1 #1b7bb8);
                color: #e0e0e0;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1b5a8a, stop:1 #2d8cd6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d3d5e, stop:1 #166a9e);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3a3a3a, stop:1 #4a4a4a);
                color: #888888;
            }
            QPushButton#disconnectBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8b2d3e, stop:1 #b83d4a);
            }
            QPushButton#disconnectBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a83d4e, stop:1 #d64d5a);
            }
            QPushButton#restartBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a5f7a, stop:1 #2d8f9e);
            }

            QTextEdit {
                background: rgba(20, 20, 30, 0.8);
                color: #a0d6a0;
                border: 1px solid #3a3a4a;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }

            QGroupBox {
                font-weight: bold;
                color: #7ec8e8;
                border: 2px solid #3a5a7a;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background: rgba(30, 40, 60, 0.3);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #7ec8e8;
            }

            QComboBox, QSpinBox, QLineEdit {
                background: rgba(20, 20, 30, 0.8);
                color: #c0c0c0;
                border: 1px solid #3a3a4a;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7ec8e8;
                margin-right: 10px;
            }

            QProgressBar {
                border: 2px solid #3a3a4a;
                border-radius: 8px;
                background: rgba(20, 20, 30, 0.5);
                text-align: center;
                color: #c0c0c0;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f4c75, stop:1 #1b7bb8);
                border-radius: 6px;
            }

            QTabWidget::pane {
                border: 2px solid #3a3a4a;
                border-radius: 8px;
                background: rgba(20, 20, 30, 0.3);
            }
            QTabBar::tab {
                background: rgba(20, 20, 30, 0.5);
                color: #a0a0a0;
                padding: 12px 20px;
                border: 1px solid #3a3a4a;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(30, 50, 80, 0.5);
                color: #7ec8e8;
                border-bottom: 2px solid #3a5a7a;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(40, 50, 70, 0.5);
            }

            QCheckBox {
                color: #c0c0c0;
                spacing: 10px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #3a3a4a;
                background: rgba(20, 20, 30, 0.5);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f4c75, stop:1 #1b7bb8);
                border-color: #1b7bb8;
            }

            QLabel {
                color: #b0b0b0;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #7ec8e8;
            }
            QLabel#statusLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }

            QScrollArea {
                border: 1px solid #444;
                border-radius: 5px;
                background: rgba(0, 0, 0, 0.2);
            }
        """)
        
        # Центральная панель
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("🛡️ VPN Client Aggregator v5.0")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Проверка IP
        self.ip_label = QLabel("🌐 IP: --")
        self.ip_label.setStyleSheet("QLabel { color: #7ec8e8; font-size: 14px; padding: 5px; }")
        header_layout.addWidget(self.ip_label)

        self.country_label = QLabel("📍 Страна: --")
        self.country_label.setStyleSheet("QLabel { color: #7ec8e8; font-size: 14px; padding: 5px; }")
        header_layout.addWidget(self.country_label)

        self.check_ip_btn = QPushButton("🔄 Проверить IP")
        self.check_ip_btn.setMaximumWidth(150)
        self.check_ip_btn.clicked.connect(self.check_ip_address)
        header_layout.addWidget(self.check_ip_btn)

        self.status_label = QLabel("⏹️ Отключён")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("""
            QLabel#statusLabel {
                background: #ff4444;
                color: white;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        main_layout.addLayout(header_layout)
        
        # Панель управления
        control_group = QGroupBox("🎮 Управление подключением")
        control_layout = QGridLayout(control_group)
        
        # Кнопки
        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_btn, 0, 0)
        
        self.disconnect_btn = QPushButton("⏹️ Отключить")
        self.disconnect_btn.setObjectName("disconnectBtn")
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        control_layout.addWidget(self.disconnect_btn, 0, 1)
        
        self.restart_btn = QPushButton("🔄 Перезапустить")
        self.restart_btn.setObjectName("restartBtn")
        self.restart_btn.clicked.connect(self.restart)
        self.restart_btn.setEnabled(False)
        control_layout.addWidget(self.restart_btn, 0, 2)
        
        # Режим работы
        control_layout.addWidget(QLabel("Режим работы:"), 1, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Split-умный (белый список)",
            "Split-tunneling (умный)",
            "Все через VPN",
            "Прямое подключение"
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        control_layout.addWidget(self.mode_combo, 1, 1, 1, 2)

        # Выбор сервера
        control_layout.addWidget(QLabel("🌍 Сервер:"), 2, 0)
        self.server_combo = QComboBox()
        self.server_combo.setMinimumWidth(400)
        self.server_combo.currentIndexChanged.connect(self.on_server_changed)
        self.load_servers_list()
        control_layout.addWidget(self.server_combo, 2, 1, 1, 2)

        # Кнопка сканера
        scan_btn_label = QLabel("")
        scan_btn = QPushButton("🔍 Сканировать серверы")
        scan_btn.setMaximumWidth(250)
        scan_btn.clicked.connect(self.run_server_scanner)
        control_layout.addWidget(scan_btn_label, 3, 0)
        control_layout.addWidget(scan_btn, 3, 1, 1, 1)
        control_layout.addWidget(QLabel(""), 3, 2)  # Stretch

        # Кнопка экспорта/импорта
        backup_btn = QPushButton("💾 Резервные серверы")
        backup_btn.setMaximumWidth(250)
        backup_btn.clicked.connect(self.run_backup_manager)
        control_layout.addWidget(QLabel(""), 4, 0)
        control_layout.addWidget(backup_btn, 4, 1, 1, 1)
        control_layout.addWidget(QLabel(""), 4, 2)  # Stretch

        main_layout.addWidget(control_group)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Статистика
        stats_tab = self.create_stats_tab()
        tabs.addTab(stats_tab, "📊 Статистика")
        
        # Вкладка 2: Настройки сервера
        server_tab = self.create_server_tab()
        tabs.addTab(server_tab, "⚙️ Настройки сервера")
        
        # Вкладка 3: Split-tunneling
        split_tab = self.create_split_tunnel_tab()
        tabs.addTab(split_tab, "🔀 Split-tunneling")
        
        # Вкладка 4: Списки доменов
        lists_tab = self.create_lists_tab()
        tabs.addTab(lists_tab, "📋 Списки доменов")
        
        # Вкладка 5: Логи
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📜 Логи")
        
        main_layout.addWidget(tabs)
        
        # Статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
        
        # Системный трей
        self.init_tray_icon()
        
        self.show()
    
    def create_stats_tab(self) -> QWidget:
        """Создание вкладки статистики"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # Скорость
        self.speed_label = QLabel("📊 Скорость: ↓ 0 KB/s ↑ 0 KB/s")
        self.speed_label.setFont(QFont("Courier New", 14))
        layout.addWidget(self.speed_label, 0, 0, 1, 2)
        
        # Трафик
        self.traffic_label = QLabel("📈 Трафик: ↓ 0 MB ↑ 0 MB")
        self.traffic_label.setFont(QFont("Courier New", 14))
        layout.addWidget(self.traffic_label, 1, 0, 1, 2)
        
        # Время подключения
        self.uptime_label = QLabel("⏱️ Время: 00:00:00")
        self.uptime_label.setFont(QFont("Courier New", 14))
        layout.addWidget(self.uptime_label, 2, 0, 1, 2)
        
        # Progress bars
        layout.addWidget(QLabel("📥 Download:"), 3, 0)
        self.dl_progress = QProgressBar()
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setValue(0)
        layout.addWidget(self.dl_progress, 3, 1)
        
        layout.addWidget(QLabel("📤 Upload:"), 4, 0)
        self.ul_progress = QProgressBar()
        self.ul_progress.setRange(0, 100)
        self.ul_progress.setValue(0)
        layout.addWidget(self.ul_progress, 4, 1)
        
        # Статистика подключения
        stats_group = QGroupBox("📊 Статистика подключения")
        stats_layout = QFormLayout(stats_group)
        
        self.stats_state = QLabel("Не подключено")
        stats_layout.addRow("Состояние:", self.stats_state)
        
        self.stats_attempts = QLabel("0")
        stats_layout.addRow("Попыток подключения:", self.stats_attempts)
        
        self.stats_errors = QLabel("0")
        stats_layout.addRow("Ошибок:", self.stats_errors)
        
        layout.addWidget(stats_group, 5, 0, 1, 2)
        
        layout.setRowStretch(6, 1)
        
        return tab
    
    def create_server_tab(self) -> QWidget:
        """Создание вкладки настроек сервера"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Адрес сервера
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("IP адрес или домен сервера")
        layout.addRow("Адрес сервера:", self.server_input)
        
        # Порт
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(443)
        layout.addRow("Порт:", self.port_input)
        
        # UUID
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("UUID клиента")
        layout.addRow("UUID:", self.uuid_input)
        
        # Кнопка генерации UUID
        uuid_btn_layout = QHBoxLayout()
        generate_uuid_btn = QPushButton("🎲 Сгенерировать UUID")
        generate_uuid_btn.clicked.connect(self.generate_uuid)
        uuid_btn_layout.addWidget(generate_uuid_btn)
        uuid_btn_layout.addStretch()
        layout.addRow(uuid_btn_layout)
        
        # SNI
        self.sni_input = QLineEdit()
        self.sni_input.setText("google.com")
        self.sni_input.setPlaceholderText("Домен для маскировки")
        layout.addRow("SNI (маскировка):", self.sni_input)
        
        # Flow
        self.flow_input = QComboBox()
        self.flow_input.addItems(["xtls-rprx-vision", "none"])
        self.flow_input.setCurrentText("xtls-rprx-vision")
        layout.addRow("Flow:", self.flow_input)
        
        layout.addRow(QLabel(""))  # Пустая строка
        
        # Кнопки сохранения
        save_btn = QPushButton("💾 Сохранить настройки")
        save_btn.clicked.connect(self.save_server_config)
        layout.addRow(save_btn)
        
        load_btn = QPushButton("📂 Загрузить из файла")
        load_btn.clicked.connect(self.load_config_dialog)
        layout.addRow(load_btn)
        
        return tab
    
    def create_split_tunnel_tab(self) -> QWidget:
        """Создание вкладки split-tunneling"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Включение
        self.split_enabled_check = QCheckBox("Включить split-tunneling")
        self.split_enabled_check.setChecked(True)
        layout.addWidget(self.split_enabled_check)
        
        # Категории для VPN
        vpn_group = QGroupBox("🌐 Через VPN (заблокированные ресурсы)")
        vpn_layout = QVBoxLayout(vpn_group)
        
        self.social_check = QCheckBox("Соцсети (Facebook, Instagram, Twitter, TikTok)")
        self.social_check.setChecked(True)
        vpn_layout.addWidget(self.social_check)
        
        self.video_check = QCheckBox("Видеохостинги (YouTube, Vimeo, Twitch)")
        self.video_check.setChecked(True)
        vpn_layout.addWidget(self.video_check)
        
        self.ai_check = QCheckBox("ИИ-сервисы (ChatGPT, Claude, Gemini, Lovable.dev)")
        self.ai_check.setChecked(True)
        vpn_layout.addWidget(self.ai_check)
        
        self.media_check = QCheckBox("Заблокированные СМИ")
        self.media_check.setChecked(True)
        vpn_layout.addWidget(self.media_check)
        
        layout.addWidget(vpn_group)
        
        # Категории напрямую
        direct_group = QGroupBox("🏠 Напрямую (российские сервисы)")
        direct_layout = QVBoxLayout(direct_group)
        
        self.ru_check = QCheckBox("Российские сервисы (VK, Yandex, Mail.ru)")
        self.ru_check.setChecked(True)
        direct_layout.addWidget(self.ru_check)
        
        self.bank_check = QCheckBox("Банки (Сбербанк, Тинькофф, Альфа)")
        self.bank_check.setChecked(True)
        direct_layout.addWidget(self.bank_check)
        
        self.gos_check = QCheckBox("Госуслуги и государственные сайты")
        self.gos_check.setChecked(True)
        direct_layout.addWidget(self.gos_check)
        
        layout.addWidget(direct_group)
        
        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить настройки split-tunneling")
        save_btn.clicked.connect(self.save_split_config)
        layout.addWidget(save_btn)
        
        return tab
    
    def create_lists_tab(self) -> QWidget:
        """Создание вкладки списков доменов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Выбор категории
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Категория:"))
        self.lists_combo = QComboBox()
        self.lists_combo.addItems(["Соцсети", "Видеохостинги", "ИИ-сервисы", "Заблокированные СМИ", "Российские сервисы"])
        self.lists_combo.currentIndexChanged.connect(self.show_domain_list)
        category_layout.addWidget(self.lists_combo)
        
        refresh_btn = QPushButton("🔄 Обновить списки")
        refresh_btn.clicked.connect(self.refresh_domain_lists)
        category_layout.addWidget(refresh_btn)
        
        category_layout.addStretch()
        layout.addLayout(category_layout)
        
        # Список доменов
        self.domains_text = QTextEdit()
        self.domains_text.setReadOnly(True)
        self.domains_text.setFont(QFont("Courier New", 11))
        layout.addWidget(self.domains_text)
        
        # Информация
        self.domains_info_label = QLabel("")
        layout.addWidget(self.domains_info_label)
        
        # Загрузка начального списка
        self.show_domain_list()
        
        return tab
    
    def create_logs_tab(self) -> QWidget:
        """Создание вкладки логов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 11))
        layout.addWidget(self.log_text)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Очистить логи")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 Сохранить логи")
        save_btn.clicked.connect(self.save_logs)
        btn_layout.addWidget(save_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return tab
    
    # ==========================================================================
    # ФУНКЦИОНАЛЬНОСТЬ
    # ==========================================================================

    def toggle_connection(self):
        """Переключение подключения"""
        self.log(f"🔔 toggle_connection вызван! is_connected={self.is_connected}")
        print(f"DEBUG: toggle_connection, is_connected={self.is_connected}")
        
        if self.is_connected:
            self.log("🔄 Отключение...")
            self.disconnect()
        else:
            self.log("🔄 Подключение...")
            self.connect()
    
    def connect(self):
        """Подключение к VPN"""
        self.log("🔄 Попытка подключения...")
        
        # Проверка настроек
        if not self.server_input.text() or not self.uuid_input.text():
            self.log("❌ Поля сервера или UUID пусты!")
            QMessageBox.warning(self, "Ошибка",
                              "Заполните адрес сервера и UUID!\n\n"
                              "Перейдите на вкладку 'Настройки сервера'")
            return

        self.log(f"✅ Сервер: {self.server_input.text()}:{self.port_input.value()}")
        self.log(f"✅ UUID: {self.uuid_input.text()[:8]}...")

        # Сохранение конфигурации (без сообщения)
        self.save_server_config(show_message=False)

        # Запуск worker
        self.log("🚀 Запуск VPN worker...")
        self.worker = VPNWorker("start")
        self.worker.set_controller(self.controller)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_connection_status)
        self.worker.finished_signal.connect(self.on_connect_finished)
        self.worker.start()

        self.connect_btn.setEnabled(False)
        self.statusBar.showMessage("Подключение...")
        self.log("⏳ Ожидание подключения...")
    
    def disconnect(self):
        """Отключение от VPN"""
        self.worker = VPNWorker("stop")
        self.worker.set_controller(self.controller)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_connection_status)
        self.worker.finished_signal.connect(self.on_disconnect_finished)
        self.worker.start()
    
    def restart(self):
        """Перезапуск VPN"""
        self.worker = VPNWorker("restart")
        self.worker.set_controller(self.controller)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_connection_status)
        self.worker.start()
    
    def update_connection_status(self, status: dict):
        """Обновление статуса подключения"""
        pass
    
    def on_connect_finished(self, success: bool):
        """Завершение подключения"""
        if success:
            self.is_connected = True
            self.connection_start_time = datetime.now()
            
            self.status_label.setText("✅ Подключён")
            self.status_label.setStyleSheet("""
                QLabel#statusLabel {
                    background: #44ff44;
                    color: black;
                }
            """)
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)
            
            self.statusBar.showMessage("VPN подключён")
            self.log("✅ VPN подключён")
            
            # Обновление tray
            self.tray_connect_action.setText("Отключить")
        else:
            self.statusBar.showMessage("Ошибка подключения")
            self.connect_btn.setEnabled(True)
    
    def on_disconnect_finished(self, success: bool):
        """Завершение отключения"""
        self.is_connected = False
        self.connection_start_time = None
        
        self.status_label.setText("⏹️ Отключён")
        self.status_label.setStyleSheet("""
            QLabel#statusLabel {
                background: #ff4444;
                color: white;
            }
        """)
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        
        self.statusBar.showMessage("VPN отключён")
        self.log("⏹️ VPN отключён")
        
        # Обновление tray
        self.tray_connect_action.setText("Подключить")
    
    def generate_uuid(self):
        """Генерация UUID"""
        uuid = self.controller.generate_uuid()
        self.uuid_input.setText(uuid)
        self.log(f"🎲 Сгенерирован UUID: {uuid}")
    
    def save_server_config(self, show_message=True):
        """Сохранение настроек сервера"""
        result = self.controller.configure_server(
            address=self.server_input.text(),
            port=self.port_input.value(),
            uuid=self.uuid_input.text(),
            sni=self.sni_input.text(),
            flow=self.flow_input.currentText()
        )

        if result:
            self.log("✅ Настройки сервера сохранены")
            if show_message:
                QMessageBox.information(self, "Сохранено",
                                      "Настройки сервера сохранены!")
    
    def load_config_dialog(self):
        """Диалог загрузки конфигурации"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить конфигурацию",
            str(CONFIG_DIR), "JSON файлы (*.json)"
        )
        
        if file_path:
            result = self.controller.load_config(Path(file_path))
            if result:
                self.load_config()
                self.log("✅ Конфигурация загружена")
    
    def save_split_config(self):
        """Сохранение настроек split-tunneling"""
        blacklist = []
        whitelist = []
        
        if self.social_check.isChecked():
            blacklist.append('social')
        if self.video_check.isChecked():
            blacklist.append('video')
        if self.ai_check.isChecked():
            blacklist.append('ai')
        if self.media_check.isChecked():
            blacklist.append('blocked_media')
        
        if self.ru_check.isChecked():
            whitelist.append('russian_services')
        
        result = self.controller.configure_split_tunnel(
            enabled=self.split_enabled_check.isChecked(),
            blacklist=blacklist if blacklist else None,
            whitelist=whitelist if whitelist else None
        )
        
        if result:
            self.log("✅ Настройки split-tunneling сохранены")
            QMessageBox.information(self, "Сохранено",
                                  "Настройки split-tunneling сохранены!")
    
    def show_domain_list(self):
        """Отображение списка доменов"""
        index = self.lists_combo.currentIndex()
        categories = ['social', 'video', 'ai', 'blocked_media', 'russian_services']
        names = ['Соцсети', 'Видеохостинги', 'ИИ-сервисы', 'Заблокированные СМИ', 'Российские сервисы']
        
        if index < len(categories):
            domains = self.domain_lists.get(categories[index], [])
            
            text = f"{names[index]} ({len(domains)} доменов):\n\n"
            text += "\n".join(sorted(domains))
            
            self.domains_text.setText(text)
            self.domains_info_label.setText(f"Всего доменов в категории: {len(domains)}")
    
    def refresh_domain_lists(self):
        """Обновление списков доменов"""
        self.log("🔄 Обновление списков доменов...")
        self.domain_lists = self.domain_loader.load_domain_lists()
        self.show_domain_list()
        self.log("✅ Списки доменов обновлены")
    
    def save_logs(self):
        """Сохранение логов"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить логи",
            str(LOGS_DIR / f"vpn-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"),
            "Текстовые файлы (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log(f"✅ Логи сохранены в {file_path}")
    
    def on_mode_changed(self, index: int):
        """Изменение режима работы"""
        # 0=whitelist, 1=split, 2=all, 3=direct
        modes = ["whitelist", "split", "all", "direct"]
        mode = modes[index] if index < len(modes) else "split"
        self.log(f"🔄 Режим изменён на: {self.mode_combo.currentText()}")
        
        # Сохраняем в конфиг
        config = self.controller.config_manager.load_config()
        if mode == "whitelist":
            # Белый список - только заблокированные через VPN
            config['split_tunnel']['enabled'] = True
            config['split_tunnel']['mode'] = 'whitelist'
            config['split_tunnel']['whitelist_categories'] = ['blocked_media']
            config['split_tunnel']['blacklist_categories'] = []
        elif mode == "split":
            # Split - заблокированные + зарубежные через VPN
            config['split_tunnel']['enabled'] = True
            config['split_tunnel']['mode'] = 'split'
            config['split_tunnel']['blacklist_categories'] = ['social', 'video', 'ai', 'blocked_media']
            config['split_tunnel']['whitelist_categories'] = ['russian_services']
        elif mode == "all":
            # Всё через VPN
            config['split_tunnel']['enabled'] = False
            config['split_tunnel']['mode'] = 'all'
        else:
            # Прямое подключение
            config['split_tunnel']['enabled'] = False
            config['split_tunnel']['mode'] = 'direct'
        
        self.controller.config_manager.save_config(config)

    def load_servers_list(self):
        """Загрузка списка серверов в ComboBox"""
        try:
            servers_file = Path.home() / "vpn-client-aggregator" / "data" / "servers.json"
            if servers_file.exists():
                import json
                with open(servers_file, 'r') as f:
                    servers = json.load(f)
                
                self.server_combo.clear()
                self._servers_cache = []
                
                # Группируем по странам
                countries = {}
                for server in servers[:100]:  # Берём первые 100 для производительности
                    country = server.get('country', '🌍 Другая')
                    if country not in countries:
                        countries[country] = []
                    countries[country].append(server)
                
                # Добавляем в ComboBox
                for country, country_servers in sorted(countries.items()):
                    for server in country_servers:
                        host = server.get('host', server.get('address', 'Unknown'))
                        port = server.get('port', 443)
                        name = server.get('name', '')
                        protocol = server.get('protocol', 'vless')
                        
                        # Формируем отображаемое имя
                        display_name = f"{country} | {host}:{port} | {protocol}"
                        if name:
                            display_name = f"{country} | {name} | {protocol}"
                        
                        self.server_combo.addItem(display_name)
                        self._servers_cache.append(server)
                
                self.log(f"✅ Загружено {len(self._servers_cache)} серверов")
            else:
                self.server_combo.addItem("❌ Серверы не загружены (выполните: vless_client.py update)")
                self._servers_cache = []
        except Exception as e:
            self.server_combo.addItem(f"❌ Ошибка: {e}")
            self._servers_cache = []

    def on_server_changed(self, index: int):
        """Изменение выбранного сервера"""
        if index < 0 or index >= len(self._servers_cache):
            return
        
        server = self._servers_cache[index]
        
        # Получаем параметры
        host = server.get('host', server.get('address', ''))
        port = server.get('port', 443)
        uuid = server.get('uuid', '')
        
        # Reality настройки
        stream = server.get('stream_settings', {})
        reality = stream.get('reality_settings', {})
        sni = reality.get('serverName', 'google.com')
        public_key = reality.get('publicKey', '')
        short_id = reality.get('shortId', '')
        
        # Заполняем поля
        self.server_input.setText(host)
        self.port_input.setValue(port)
        self.uuid_input.setText(uuid)
        self.sni_input.setText(sni)
        
        self.log(f"✅ Сервер выбран: {host}:{port}")

    def check_ip_address(self):
        """Проверка текущего IP адреса"""
        import aiohttp
        
        async def fetch_ip():
            try:
                self.ip_label.setText("🌐 IP: Загрузка...")
                self.country_label.setText("📍 Страна: ...")
                
                # Проверяем через ipapi.co
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://ipapi.co/json/', timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            ip = data.get('ip', 'Unknown')
                            country = data.get('country_name', 'Unknown')
                            city = data.get('city', '')
                            
                            # Определяем флаг страны
                            flag = self._get_country_flag(country)
                            
                            self.ip_label.setText(f"🌐 IP: {ip}")
                            self.country_label.setText(f"📍 Страна: {flag} {country} {f'({city})' if city else ''}")
                            
                            # Проверяем, иностранный ли IP
                            if country in ['Russia', 'Россия', 'Belarus', 'Belarus']:
                                self.ip_label.setStyleSheet("QLabel { color: #ff6b6b; font-size: 14px; padding: 5px; font-weight: bold; }")
                                self.log(f"⚠️ Российский IP: {ip}")
                            else:
                                self.ip_label.setStyleSheet("QLabel { color: #51cf66; font-size: 14px; padding: 5px; font-weight: bold; }")
                                self.log(f"✅ Иностранный IP: {ip} ({country})")
                        else:
                            self.ip_label.setText("🌐 IP: Ошибка")
                            self.country_label.setText("📍 Страна: --")
            except Exception as e:
                self.ip_label.setText("🌐 IP: Ошибка")
                self.country_label.setText("📍 Страна: --")
                self.log(f"❌ Ошибка проверки IP: {e}")
        
        # Запускаем в отдельном потоке
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(fetch_ip())
            loop.close()
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")

    def run_server_scanner(self):
        """Запуск сканера серверов"""
        from server_scanner import UltimateScanner
        
        self.log("🚀 Запуск Ultimate Scanner...")
        
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class ScannerThread(QThread):
            log_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(int, int, int)
            
            def __init__(self):
                super().__init__()
                self.scanner = UltimateScanner(progress_callback=self.log_signal.emit)
            
            def run(self):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Парсим все источники
                    loop.run_until_complete(self.scanner.parse_all_sources())
                    
                    if not self.scanner.servers:
                        self.log_signal.emit("❌ Серверы не найдены!")
                        self.finished_signal.emit(0, 0, 0)
                        return
                    
                    # Проверяем
                    loop.run_until_complete(self.scanner.check_servers())
                    
                    # Сохраняем
                    self.scanner.save_results()
                    
                    self.finished_signal.emit(
                        len(self.scanner.servers),
                        len(self.scanner.working_servers),
                        self.scanner.new_servers_count
                    )
                except Exception as e:
                    self.log_signal.emit(f"❌ Ошибка: {e}")
                    self.finished_signal.emit(0, 0, 0)
                finally:
                    loop.close()
        
        self.scanner_thread = ScannerThread()
        self.scanner_thread.log_signal.connect(self.log)
        self.scanner_thread.finished_signal.connect(self.on_scanner_finished)
        self.scanner_thread.start()
        
        self.log("⏳ Сканирование всех источников...")
    
    def on_scanner_finished(self, total: int, working: int, new: int):
        """Завершение сканера"""
        self.log(f"✅ Сканирование завершено!")
        self.log(f"📊 Найдено: {total} | Рабочих: {working} | Новых: {new}")
        
        # Перезагружаем список серверов
        self.load_servers_list()
        
        # Показываем сообщение
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Сканер завершён",
            f"📊 Найдено: {total} серверов\n"
            f"✅ Рабочих: {working}\n"
            f"🆕 Новых: {new}"
        )
    
    def run_backup_manager(self):
        """Запуск менеджера резервных серверов"""
        from backup_manager import BackupServerManager
        
        self.log("💾 Запуск Backup Manager...")
        
        from PyQt5.QtCore import QThread, pyqtSignal
        from PyQt5.QtWidgets import QMessageBox
        
        class BackupThread(QThread):
            log_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(int, str, dict)
            
            def __init__(self):
                super().__init__()
                self.manager = BackupServerManager()
            
            def run(self):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Добавляем резервные серверы
                    added = loop.run_until_complete(self.manager.add_backup_servers(100))
                    
                    # Экспортируем конфиги
                    export_file = self.manager.export_configs()
                    
                    # Создаём авто-конфиг
                    auto_config = self.manager.create_auto_switch_config()
                    
                    self.finished_signal.emit(added, export_file, auto_config)
                except Exception as e:
                    self.log_signal.emit(f"❌ Ошибка: {e}")
                    self.finished_signal.emit(0, "", {})
                finally:
                    loop.close()
        
        self.backup_thread = BackupThread()
        self.backup_thread.log_signal.connect(self.log)
        self.backup_thread.finished_signal.connect(self.on_backup_finished)
        self.backup_thread.start()
        
        self.log("⏳ Добавление резервных серверов...")
    
    def on_backup_finished(self, added: int, export_file: str, auto_config: dict):
        """Завершение backup manager"""
        self.log(f"✅ Резервные серверы готовы!")
        self.log(f"📊 Добавлено: {added} серверов")
        self.log(f"💾 Экспорт: {export_file}")
        
        # Перезагружаем список серверов
        self.load_servers_list()
        
        # Показываем сообщение
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Резервные серверы")
        msg.setText(f"✅ Резервные серверы готовы!")
        msg.setInformativeText(
            f"📊 Добавлено: {added} серверов\n"
            f"💾 Экспорт: {export_file}\n"
            f"🔄 Авто-переключение: {len(auto_config.get('auto_switch', {}).get('servers', []))} серверов"
        )
        msg.exec_()

    def _get_country_flag(self, country_name: str) -> str:
        """Получение флага страны по названию"""
        flags = {
            'Germany': '🇩🇪', 'Deutschland': '🇩🇪', 'Германия': '🇩🇪',
            'United States': '🇺🇸', 'USA': '🇺🇸', 'США': '🇺🇸',
            'Netherlands': '🇳🇱', 'Нидерланды': '🇳🇱',
            'France': '🇫🇷', 'Франция': '🇫🇷',
            'United Kingdom': '🇬🇧', 'Великобритания': '🇬🇧',
            'Finland': '🇫🇮', 'Финляндия': '🇫🇮',
            'Poland': '🇵🇱', 'Польша': '🇵🇱',
            'Latvia': '🇱🇻', 'Латвия': '🇱🇻',
            'Italy': '🇮🇹', 'Италия': '🇮🇹',
            'Spain': '🇪🇸', 'Испания': '🇪🇸',
            'Japan': '🇯🇵', 'Япония': '🇯🇵',
            'Singapore': '🇸🇬', 'Сингапур': '🇸🇬',
            'Canada': '🇨🇦', 'Канада': '🇨🇦',
            'Russia': '🇷🇺', 'Россия': '🇷🇺',
            'Belarus': '🇧🇾', 'Беларусь': '🇧🇾',
            'Kazakhstan': '🇰🇿', 'Казахстан': '🇰🇿',
        }
        return flags.get(country_name, '🌍')
    
    # ==========================================================================
    # УТИЛИТЫ
    # ==========================================================================
    
    def load_config(self):
        """Загрузка конфигурации"""
        config = self.controller.config_manager.load_config()

        server = config.get('server', {})
        self.server_input.setText(server.get('address', ''))
        self.port_input.setValue(server.get('port', 443))
        self.uuid_input.setText(server.get('uuid', ''))
        self.sni_input.setText(server.get('sni', 'google.com'))
        self.flow_input.setCurrentText(server.get('flow', 'xtls-rprx-vision'))

        split = config.get('split_tunnel', {})
        self.split_enabled_check.setChecked(split.get('enabled', True))

        self.log("✅ Конфигурация загружена")

    def auto_fill_server(self):
        """Автозаполнение сервера из загруженных списков"""
        try:
            servers_file = DATA_DIR / "servers.json"
            if servers_file.exists():
                import json
                with open(servers_file, 'r') as f:
                    servers = json.load(f)
                
                if servers and isinstance(servers, list) and len(servers) > 0:
                    # Берём первый сервер
                    server = servers[0]
                    host = server.get('host', server.get('address', ''))
                    port = server.get('port', 443)
                    uuid = server.get('uuid', '')
                    name = server.get('name', 'Unknown')
                    
                    # Заполняем поля
                    self.server_input.setText(host)
                    self.port_input.setValue(port)
                    self.uuid_input.setText(uuid)
                    
                    # Заполняем SNI если есть
                    if 'stream_settings' in server:
                        stream = server['stream_settings']
                        if 'reality_settings' in stream:
                            sni = stream['reality_settings'].get('serverName', '')
                            if sni:
                                self.sni_input.setText(sni)
                        elif 'tls_settings' in stream:
                            sni = stream['tls_settings'].get('serverName', '')
                            if sni:
                                self.sni_input.setText(sni)
                    
                    self.log(f"✅ Автозаполнение: {name} ({host}:{port})")
        except Exception as e:
            self.log(f"⚠️ Автозаполнение не удалось: {e}")
    
    def log(self, message: str):
        """Добавление записи в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.append(log_entry)
        self.statusBar.showMessage(message, 5000)
        
        # Автоскролл
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_timers(self):
        """Запуск таймеров"""
        # Таймер обновления статистики
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)
    
    def update_stats(self):
        """Обновление статистики"""
        if self.is_connected and self.connection_start_time:
            elapsed = datetime.now() - self.connection_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.setText(f"⏱️ Время: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def init_tray_icon(self):
        """Инициализация системного трея"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Пробуем создать иконку
        try:
            tray_icon_pixmap = self.style().standardIcon(QStyle.SP_DriveNetIcon)
            self.tray_icon.setIcon(tray_icon_pixmap)
        except Exception:
            # Если не получилось, создаём пустую иконку
            from PyQt5.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 120, 215))
            self.tray_icon.setIcon(QIcon(pixmap))

        tray_menu = QMenu()
        
        # Показать
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Подключить/Отключить
        self.tray_connect_action = QAction("Подключить", self)
        self.tray_connect_action.triggered.connect(self.toggle_connection)
        tray_menu.addAction(self.tray_connect_action)
        
        tray_menu.addSeparator()
        
        # Выход
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        """Активация из трея"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.is_connected:
            reply = QMessageBox.question(
                self, "Выход",
                "VPN подключён. Отключить и выйти?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.disconnect()
                time.sleep(2)
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()


# =============================================================================
# ЗАПУСК
# =============================================================================

def main():
    """Точка входа приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("VPN Client Aggregator")
    app.setOrganizationName("VPN Aggregator")
    app.setQuitOnLastWindowClosed(False)
    
    window = VPNClientWindow()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
