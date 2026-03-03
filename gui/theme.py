#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Theme - Тёмная тема для приложения
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


def setup_dark_theme(app: QApplication) -> None:
    """Настроить тёмную тему"""
    
    palette = QPalette()
    
    # Цвета
    dark_gray = QColor(53, 53, 53)
    gray = QColor(127, 127, 127)
    light_gray = QColor(190, 190, 190)
    blue = QColor(42, 130, 218)
    black = QColor(35, 35, 35)
    white = QColor(255, 255, 255)
    
    # Base
    palette.setColor(QPalette.ColorRole.Window, dark_gray)
    palette.setColor(QPalette.ColorRole.WindowText, white)
    palette.setColor(QPalette.ColorRole.Base, black)
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_gray)
    palette.setColor(QPalette.ColorRole.ToolTipBase, white)
    palette.setColor(QPalette.ColorRole.ToolTipText, white)
    palette.setColor(QPalette.ColorRole.Text, white)
    palette.setColor(QPalette.ColorRole.Button, dark_gray)
    palette.setColor(QPalette.ColorRole.ButtonText, white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, blue)
    palette.setColor(QPalette.ColorRole.Highlight, blue)
    palette.setColor(QPalette.ColorRole.HighlightedText, black)
    
    app.setPalette(palette)
    
    # Стили
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a82da;
            border: 1px solid #2a82da;
        }
        
        QWidget {
            font-family: 'Ubuntu', 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        
        QPushButton {
            background-color: #2a82da;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 16px;
        }
        
        QPushButton:hover {
            background-color: #3a92ea;
        }
        
        QPushButton:pressed {
            background-color: #1a72ca;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        
        QPushButton#connectButton {
            background-color: #28a745;
            font-size: 20px;
            padding: 20px 40px;
        }
        
        QPushButton#connectButton:hover {
            background-color: #34ce57;
        }
        
        QPushButton#connectButton:disabled {
            background-color: #555555;
        }
        
        QPushButton#disconnectButton {
            background-color: #dc3545;
            font-size: 20px;
            padding: 20px 40px;
        }
        
        QPushButton#disconnectButton:hover {
            background-color: #e4606d;
        }
        
        QComboBox {
            background-color: #353535;
            color: white;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px 12px;
        }
        
        QComboBox:hover {
            border: 1px solid #2a82da;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 8px solid #ffffff;
            margin-right: 10px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #353535;
            color: white;
            border: 1px solid #555555;
            selection-background-color: #2a82da;
        }
        
        QProgressBar {
            background-color: #353535;
            border: none;
            border-radius: 6px;
            height: 8px;
        }
        
        QProgressBar::chunk {
            background-color: #2a82da;
            border-radius: 6px;
        }
        
        QTableWidget {
            background-color: #252525;
            color: white;
            border: 1px solid #555555;
            border-radius: 8px;
            gridline-color: #353535;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QTableWidget::item:selected {
            background-color: #2a82da;
        }
        
        QHeaderView::section {
            background-color: #353535;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        
        QScrollBar:vertical {
            background-color: #252525;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #252525;
            height: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #555555;
            border-radius: 6px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #666666;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QLabel#statusLabel {
            font-size: 18px;
            font-weight: bold;
            color: #28a745;
        }
        
        QLabel#statusLabel.disconnected {
            color: #dc3545;
        }
        
        QLabel#statusLabel.connecting {
            color: #ffc107;
        }
        
        QGroupBox {
            background-color: #252525;
            border: 1px solid #555555;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid #555555;
            background-color: #353535;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2a82da;
            border-color: #2a82da;
        }
        
        QSpinBox, QDoubleSpinBox {
            background-color: #353535;
            color: white;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 6px;
        }
        
        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #2a82da;
        }
    """)
