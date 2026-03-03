#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog - Диалог добавления источника
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt


class AddSourceDialog(QDialog):
    """Диалог добавления нового источника"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить источник")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Описание
        desc_label = QLabel(
            "Добавьте новый источник VPN конфигураций.\n"
            "Укажите URL на raw-файл с GitHub или другой подпиской."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Группа полей
        group = QGroupBox("Параметры источника")
        group_layout = QVBoxLayout(group)
        
        # Название
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: myvpn-configs")
        name_layout.addWidget(self.name_edit)
        group_layout.addLayout(name_layout)
        
        # URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://raw.githubusercontent.com/user/repo/main/subscription.txt")
        url_layout.addWidget(self.url_edit)
        group_layout.addLayout(url_layout)
        
        # Активен
        self.enabled_check = QCheckBox("Включить источник")
        self.enabled_check.setChecked(True)
        group_layout.addWidget(self.enabled_check)
        
        layout.addWidget(group)
        
        # Подсказка
        hint_label = QLabel(
            "💡 Подсказка: Для GitHub используйте raw-ссылки:\n"
            "https://raw.githubusercontent.com/USER/REPO/BRANCH/file.txt"
        )
        hint_label.setStyleSheet("color: #888; font-size: 12px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.add_button = QPushButton("Добавить")
        self.add_button.setObjectName("connectButton")
        self.add_button.clicked.connect(self._on_add)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
    
    def _on_add(self):
        """Обработчик кнопки Добавить"""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название источника")
            return
        
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL источника")
            return
        
        if not url.startswith('http://') and not url.startswith('https://'):
            QMessageBox.warning(self, "Ошибка", "URL должен начинаться с http:// или https://")
            return
        
        self.accept()
    
    def get_source(self):
        """Получить данные источника"""
        return {
            "name": self.name_edit.text().strip(),
            "url": self.url_edit.text().strip(),
            "enabled": self.enabled_check.isChecked()
        }
