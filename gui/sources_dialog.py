#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sources Dialog - Диалог управления источниками
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QCheckBox, QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.config_manager import ConfigManager
from gui.dialog import AddSourceDialog


class SourcesDialog(QDialog):
    """Диалог управления источниками"""
    
    def __init__(self, parent=None, config: ConfigManager = None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Управление источниками")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        self._init_ui()
        self._load_sources()
    
    def _init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Описание
        desc_label = QLabel(
            "Управление источниками VPN конфигураций.\n"
            "Отмечайте активные источники и добавляйте новые."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Таблица источников
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(4)
        self.sources_table.setHorizontalHeaderLabels([
            "Вкл", "Название", "URL", "Статус"
        ])
        
        header = self.sources_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.sources_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sources_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sources_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.sources_table)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Добавить")
        self.add_button.clicked.connect(self._add_source)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("➖ Удалить")
        self.remove_button.clicked.connect(self._remove_source)
        button_layout.addWidget(self.remove_button)
        
        self.test_button = QPushButton("🔍 Проверить")
        self.test_button.clicked.connect(self._test_sources)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        # Кнопки OK/Cancel
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
    
    def _load_sources(self):
        """Загрузить источники в таблицу"""
        self.sources_table.setRowCount(0)
        
        sources = self.config.get_sources()
        all_sources = self.config.get('sources', [])
        
        for source in all_sources:
            row = self.sources_table.rowCount()
            self.sources_table.insertRow(row)
            
            # Чекбокс
            enabled = source.get('enabled', True)
            check_item = QTableWidgetItem()
            check_item.setFlags(check_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            check_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            self.sources_table.setItem(row, 0, check_item)
            
            # Название
            name_item = QTableWidgetItem(source.get('name', 'Unknown'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.sources_table.setItem(row, 1, name_item)
            
            # URL
            url_item = QTableWidgetItem(source.get('url', ''))
            url_item.setFlags(url_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.sources_table.setItem(row, 2, url_item)
            
            # Статус
            status_item = QTableWidgetItem("—")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.sources_table.setItem(row, 3, status_item)
    
    def _add_source(self):
        """Добавить новый источник"""
        dialog = AddSourceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            source = dialog.get_source()
            
            # Добавляем в конфигурацию
            sources = self.config.get('sources', [])
            sources.append(source)
            self.config.set('sources', sources)
            self.config.save()
            
            # Обновляем таблицу
            self._load_sources()
            self.status_label.setText(f"✅ Добавлен источник: {source['name']}")
    
    def _remove_source(self):
        """Удалить выбранный источник"""
        current_row = self.sources_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите источник для удаления")
            return
        
        # Получаем название
        name_item = self.sources_table.item(current_row, 1)
        if name_item:
            name = name_item.text()
            
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить источник '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Удаляем из конфигурации
                sources = self.config.get('sources', [])
                sources = [s for s in sources if s.get('name') != name]
                self.config.set('sources', sources)
                self.config.save()
                
                # Обновляем таблицу
                self._load_sources()
                self.status_label.setText(f"✅ Удалён источник: {name}")
    
    def _test_sources(self):
        """Проверить доступность источников"""
        import asyncio
        import aiohttp
        
        self.status_label.setText("🔍 Проверка источников...")
        self.button_box.setEnabled(False)
        
        async def check_url(session, url):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return "✅ OK"
                    else:
                        return f"❌ HTTP {response.status}"
            except Exception as e:
                return f"❌ {str(e)[:30]}"
        
        async def test_all():
            async with aiohttp.ClientSession() as session:
                for row in range(self.sources_table.rowCount()):
                    url_item = self.sources_table.item(row, 2)
                    if url_item:
                        url = url_item.text()
                        result = await check_url(session, url)
                        
                        status_item = QTableWidgetItem(result)
                        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        
                        if result.startswith("✅"):
                            status_item.setForeground(QColor("#28a745"))
                        else:
                            status_item.setForeground(QColor("#dc3545"))
                        
                        self.sources_table.setItem(row, 3, status_item)
                        self.sources_table.repaint()
            
            self.status_label.setText("✅ Проверка завершена")
            self.button_box.setEnabled(True)
        
        # Запускаем в фоне
        from PyQt6.QtCore import QThread
        
        class TestThread(QThread):
            def __init__(self, coro):
                super().__init__()
                self.coro = coro
            
            def run(self):
                asyncio.run(self.coro)
        
        self.test_thread = TestThread(test_all())
        self.test_thread.start()
    
    def accept(self):
        """Сохранить изменения при OK"""
        # Сохраняем состояние чекбоксов
        sources = self.config.get('sources', [])
        
        for row in range(self.sources_table.rowCount()):
            check_item = self.sources_table.item(row, 0)
            name_item = self.sources_table.item(row, 1)
            
            if check_item and name_item:
                name = name_item.text()
                enabled = check_item.checkState() == Qt.CheckState.Checked
                
                # Находим источник и обновляем
                for source in sources:
                    if source.get('name') == name:
                        source['enabled'] = enabled
                        break
        
        self.config.set('sources', sources)
        self.config.save()
        
        super().accept()
