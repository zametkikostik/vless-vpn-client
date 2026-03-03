#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window - Главное окно приложения
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar,
    QGroupBox, QCheckBox, QSpinBox, QComboBox,
    QTextEdit, QSplitter, QFrame, QSizePolicy, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QStyle

import sys
from typing import Optional, Dict, List
from core.config_manager import ConfigManager
from core.server_manager import ServerManager
from core.xray_manager import XrayManager
from core.system_proxy import SystemProxyManager


class ServerLoaderThread(QThread):
    """Поток для загрузки серверов"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    
    def __init__(self, server_manager: ServerManager):
        super().__init__()
        self.server_manager = server_manager
    
    def run(self):
        import asyncio
        try:
            servers = asyncio.run(self.server_manager.load_from_sources())
            self.finished.emit(servers)
        except Exception as e:
            self.error.emit(str(e))


class ServerCheckerThread(QThread):
    """Поток для проверки серверов"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    
    def __init__(self, server_manager: ServerManager, servers: List[Dict]):
        super().__init__()
        self.server_manager = server_manager
        self.servers = servers
    
    def run(self):
        import asyncio
        try:
            def on_progress(current, total):
                self.progress.emit(current, total)
            
            servers = asyncio.run(
                self.server_manager.check_servers(
                    self.servers,
                    progress_callback=on_progress
                )
            )
            self.finished.emit(servers)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.server_manager = ServerManager(config)
        self.xray_manager = XrayManager(config)
        self.proxy_manager = SystemProxyManager(
            config.get('socks_port', 10809),
            config.get('proxy_port', 10808)
        )
        
        self.is_connected = False
        self.servers: List[Dict] = []

        self._init_ui()
        self._load_servers()
    
    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("AntiCensor VPN - FreedomLink Linux")
        self.setMinimumSize(900, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("🛡️ AntiCensor VPN")
        self.title_label.setFont(QFont("Ubuntu", 24, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Индикатор статуса
        self.status_label = QLabel("⭕ Отключено")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setProperty("class", "disconnected")
        header_layout.addWidget(self.status_label)
        
        main_layout.addLayout(header_layout)
        
        # Разделитель
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Верхняя часть - кнопка и статус
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа подключения
        connect_group = QGroupBox("Подключение")
        connect_layout = QVBoxLayout(connect_group)
        
        # Большая кнопка подключения
        self.connect_button = QPushButton("🚀 ПОДКЛЮЧИТЬСЯ")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.setMinimumHeight(80)
        self.connect_button.clicked.connect(self._toggle_connection)
        connect_layout.addWidget(self.connect_button)
        
        # Информация о текущем сервере
        self.server_info_label = QLabel("Сервер: Не выбран")
        self.server_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connect_layout.addWidget(self.server_info_label)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        connect_layout.addWidget(self.progress_bar)
        
        top_layout.addWidget(connect_group)
        
        # Настройки
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout(settings_group)
        
        # Smart Routing
        self.smart_routing_check = QCheckBox("🌐 Smart Routing (RU сайты напрямую)")
        self.smart_routing_check.setChecked(self.config.get('smart_routing', True))
        self.smart_routing_check.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.smart_routing_check)
        
        # Anti-DPI
        self.anti_dpi_check = QCheckBox("🔒 Anti-DPI защита")
        self.anti_dpi_check.setChecked(self.config.get('anti_dpi', True))
        self.anti_dpi_check.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.anti_dpi_check)
        
        # Системный прокси
        self.system_proxy_check = QCheckBox("💻 Использовать системный прокси")
        self.system_proxy_check.setChecked(self.config.get('system_proxy', True))
        self.system_proxy_check.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.system_proxy_check)
        
        # Автоподключение
        self.auto_connect_check = QCheckBox("⚡ Автоподключение при запуске")
        self.auto_connect_check.setChecked(self.config.get('auto_connect', False))
        self.auto_connect_check.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.auto_connect_check)
        
        # Порты
        ports_layout = QHBoxLayout()
        ports_layout.addWidget(QLabel("SOCKS порт:"))
        self.socks_port_spin = QSpinBox()
        self.socks_port_spin.setRange(1024, 65535)
        self.socks_port_spin.setValue(self.config.get('socks_port', 10809))
        self.socks_port_spin.valueChanged.connect(self._on_settings_changed)
        ports_layout.addWidget(self.socks_port_spin)
        
        ports_layout.addWidget(QLabel("HTTP порт:"))
        self.http_port_spin = QSpinBox()
        self.http_port_spin.setRange(1024, 65535)
        self.http_port_spin.setValue(self.config.get('proxy_port', 10808))
        self.http_port_spin.valueChanged.connect(self._on_settings_changed)
        ports_layout.addWidget(self.http_port_spin)
        
        ports_layout.addStretch()
        settings_layout.addLayout(ports_layout)
        
        top_layout.addWidget(settings_group)
        splitter.addWidget(top_widget)
        
        # Нижняя часть - список серверов
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Список серверов
        servers_group = QGroupBox("Серверы")
        servers_layout = QVBoxLayout(servers_group)
        
        # Панель инструментов
        toolbar_layout = QHBoxLayout()

        self.refresh_button = QPushButton("🔄 Обновить")
        self.refresh_button.clicked.connect(self._load_servers)
        toolbar_layout.addWidget(self.refresh_button)

        self.scan_button = QPushButton("🔍 Проверить скорость")
        self.scan_button.clicked.connect(self._check_servers)
        toolbar_layout.addWidget(self.scan_button)

        self.sources_button = QPushButton("📋 Источники")
        self.sources_button.clicked.connect(self._show_sources_dialog)
        toolbar_layout.addWidget(self.sources_button)

        self.update_button = QPushButton("🔄 Обновить приложение")
        self.update_button.clicked.connect(self._check_update)
        toolbar_layout.addWidget(self.update_button)

        self.exit_button = QPushButton("❌ Выход")
        self.exit_button.clicked.connect(self._on_exit)
        toolbar_layout.addWidget(self.exit_button)

        toolbar_layout.addStretch()
        
        # Фильтры
        toolbar_layout.addWidget(QLabel("Протокол:"))
        self.protocol_filter = QComboBox()
        self.protocol_filter.addItems(["Все", "VLESS", "VMess", "Trojan", "SS"])
        self.protocol_filter.currentTextChanged.connect(self._filter_servers)
        toolbar_layout.addWidget(self.protocol_filter)
        
        servers_layout.addLayout(toolbar_layout)
        
        # Таблица серверов
        self.servers_table = QTableWidget()
        self.servers_table.setColumnCount(5)
        self.servers_table.setHorizontalHeaderLabels([
            "Название", "Протокол", "Хост", "Порт", "Ping"
        ])
        
        header = self.servers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.servers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.servers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.servers_table.setAlternatingRowColors(True)
        self.servers_table.itemDoubleClicked.connect(self._on_server_double_click)
        
        servers_layout.addWidget(self.servers_table)
        
        bottom_layout.addWidget(servers_group)
        splitter.addWidget(bottom_widget)
        
        # Настройка splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Лог
        log_group = QGroupBox("Лог")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)

    def _load_servers(self):
        """Загрузить серверы"""
        self._log("Загрузка серверов...")
        self.refresh_button.setEnabled(False)
        
        self.loader_thread = ServerLoaderThread(self.server_manager)
        self.loader_thread.finished.connect(self._on_servers_loaded)
        self.loader_thread.error.connect(self._on_load_error)
        self.loader_thread.start()
    
    def _on_servers_loaded(self, servers: List[Dict]):
        """Серверы загружены"""
        self.servers = servers
        self._populate_servers_table()
        self.refresh_button.setEnabled(True)
        self._log(f"Загружено {len(servers)} серверов")
    
    def _on_load_error(self, error: str):
        """Ошибка загрузки"""
        self.refresh_button.setEnabled(True)
        self._log(f"Ошибка загрузки: {error}")
    
    def _check_servers(self):
        """Проверить серверы"""
        if not self.servers:
            self._log("Сначала загрузите серверы")
            return
        
        self._log("Проверка серверов...")
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.checker_thread = ServerCheckerThread(
            self.server_manager,
            self.servers.copy()
        )
        self.checker_thread.finished.connect(self._on_servers_checked)
        self.checker_thread.error.connect(self._on_check_error)
        self.checker_thread.progress.connect(self._on_check_progress)
        self.checker_thread.start()
    
    def _on_servers_checked(self, servers: List[Dict]):
        """Серверы проверены"""
        self.servers = servers
        self._populate_servers_table()
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log("Проверка завершена")
    
    def _on_check_error(self, error: str):
        """Ошибка проверки"""
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"Ошибка проверки: {error}")
    
    def _on_check_progress(self, current: int, total: int):
        """Прогресс проверки"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _populate_servers_table(self):
        """Заполнить таблицу серверов"""
        self.servers_table.setRowCount(0)
        
        # Фильтр по протоколу
        protocol_filter = self.protocol_filter.currentText()
        
        for server in self.servers:
            if protocol_filter != "Все":
                if server.get('protocol', '').upper() != protocol_filter:
                    continue
            
            row = self.servers_table.rowCount()
            self.servers_table.insertRow(row)
            
            # Название
            name = server.get('name', 'Unknown')
            self.servers_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Протокол
            protocol = server.get('protocol', 'Unknown').upper()
            self.servers_table.setItem(row, 1, QTableWidgetItem(protocol))
            
            # Хост
            host = server.get('host', 'Unknown')
            self.servers_table.setItem(row, 2, QTableWidgetItem(host))
            
            # Порт
            port = str(server.get('port', 0))
            self.servers_table.setItem(row, 3, QTableWidgetItem(port))
            
            # Ping
            ping = server.get('ping')
            if ping is not None:
                ping_item = QTableWidgetItem(f"{ping} мс")
                # Цвет в зависимости от пинга
                if ping < 100:
                    ping_item.setForeground(Qt.GlobalColor.green)
                elif ping < 300:
                    ping_item.setForeground(Qt.GlobalColor.yellow)
                else:
                    ping_item.setForeground(Qt.GlobalColor.red)
            else:
                ping_item = QTableWidgetItem("—")
            self.servers_table.setItem(row, 4, ping_item)
    
    def _filter_servers(self):
        """Фильтровать серверы"""
        self._populate_servers_table()
    
    def _toggle_connection(self):
        """Переключить подключение"""
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """Подключиться"""
        # Выбираем лучший сервер
        server = self.server_manager.get_best_server()
        
        if not server:
            # Если нет проверенных, берём первый
            if self.servers:
                server = self.servers[0]
            else:
                self._log("Нет доступных серверов")
                return
        
        self._log(f"Подключение к {server['name']}...")
        self.status_label.setText("⏳ Подключение...")
        self.status_label.setProperty("class", "connecting")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        # Генерируем конфигурацию
        routing_config = self.config.get_routing_config()
        xray_config = self.xray_manager.generate_config(
            server,
            routing_config,
            self.config.get('anti_dpi', True)
        )
        
        # Запускаем Xray
        if not self.xray_manager.start(xray_config):
            self._log("Ошибка запуска Xray")
            self._disconnect()
            return
        
        # Включаем системный прокси
        if self.config.get('system_proxy', True):
            self.proxy_manager.enable_system_proxy()
        
        self.is_connected = True
        self.connect_button.setText("❌ ОТКЛЮЧИТЬСЯ")
        self.connect_button.setObjectName("disconnectButton")
        self.connect_button.style().unpolish(self.connect_button)
        self.connect_button.style().polish(self.connect_button)
        
        self.status_label.setText("🟢 Подключено")
        self.status_label.setProperty("class", "")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.server_info_label.setText(
            f"Сервер: {server['name']} | {server['host']}:{server['port']}"
        )
        
        self._log("Подключение успешно")

        # Обновляем иконку трея
        self.tray_icon.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_DriveNetIcon
        ))
    
    def _disconnect(self):
        """Отключиться"""
        self._log("Отключение...")
        
        # Останавливаем Xray
        self.xray_manager.stop()
        
        # Отключаем системный прокси
        if self.config.get('system_proxy', True):
            self.proxy_manager.disable_system_proxy()
        
        self.is_connected = False
        self.connect_button.setText("🚀 ПОДКЛЮЧИТЬСЯ")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.style().unpolish(self.connect_button)
        self.connect_button.style().polish(self.connect_button)
        
        self.status_label.setText("⭕ Отключено")
        self.status_label.setProperty("class", "disconnected")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.server_info_label.setText("Сервер: Не выбран")

        self._log("Отключено")

        # Обновляем иконку трея
        self.tray_icon.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        ))
    
    def _on_server_double_click(self, item):
        """Двойной клик по серверу"""
        row = item.row()
        if row < len(self.servers):
            server = self.servers[row]
            self._log(f"Выбран сервер: {server['name']}")
            self.server_info_label.setText(
                f"Сервер: {server['name']} | {server['host']}:{server['port']}"
            )

    def _show_sources_dialog(self):
        """Показать диалог управления источниками"""
        from gui.sources_dialog import SourcesDialog
        dialog = SourcesDialog(self, self.config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Источники обновлены, перезагружаем
            self._log("Источники обновлены")
            self._load_servers()

    def _on_settings_changed(self):
        """Настройки изменены"""
        self.config.set('smart_routing', self.smart_routing_check.isChecked())
        self.config.set('anti_dpi', self.anti_dpi_check.isChecked())
        self.config.set('system_proxy', self.system_proxy_check.isChecked())
        self.config.set('auto_connect', self.auto_connect_check.isChecked())
        self.config.set('socks_port', self.socks_port_spin.value())
        self.config.set('proxy_port', self.http_port_spin.value())
        self.config.save()

    def _check_update(self):
        """Проверка обновлений приложения"""
        import subprocess
        
        self._log("Проверка обновлений...")
        
        try:
            # Проверяем, установлен ли из GitHub
            result = subprocess.run(
                ['git', '-C', '/opt/anticensor-vpn', 'fetch', 'origin', 'main'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self._log("❌ Не найдено Git репозитория")
                QMessageBox.information(
                    self, "Обновление",
                    "Приложение установлено не из GitHub.\n"
                    "Для автообновления используйте:\n"
                    "sudo ./scripts/install-from-github.sh"
                )
                return
            
            # Сравниваем версии
            current = subprocess.run(
                ['git', '-C', '/opt/anticensor-vpn', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            latest = subprocess.run(
                ['git', '-C', '/opt/anticensor-vpn', 'rev-parse', 'origin/main'],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            if current == latest:
                self._log("✅ Установлена последняя версия")
                QMessageBox.information(
                    self, "Обновление",
                    "✅ У вас последняя версия!"
                )
            else:
                reply = QMessageBox.question(
                    self, "Обновление",
                    "Доступно обновление! Загрузить и установить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._log("Загрузка обновления...")
                    update_result = subprocess.run(
                        ['sudo', '/opt/anticensor-vpn/scripts/update-from-github.sh'],
                        capture_output=True,
                        text=True
                    )
                    
                    if update_result.returncode == 0:
                        self._log("✅ Обновление установлено")
                        QMessageBox.information(
                            self, "Обновление",
                            "✅ Обновление успешно!\nПерезапустите приложение."
                        )
                    else:
                        self._log(f"❌ Ошибка обновления: {update_result.stderr}")
                        QMessageBox.critical(
                            self, "Обновление",
                            f"Ошибка обновления:\n{update_result.stderr}"
                        )
                        
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
            QMessageBox.critical(
                self, "Обновление",
                f"Ошибка проверки обновлений:\n{str(e)}"
            )

    def _on_exit(self):
        """Выход"""
        if self.is_connected:
            self._disconnect()
        QApplication.quit()

    def closeEvent(self, event):
        """Обработка закрытия"""
        # Закрываем приложение полностью
        self._on_exit()

    def _log(self, message: str):
        """Добавить сообщение в лог"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
