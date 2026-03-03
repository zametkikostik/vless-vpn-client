#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AntiCensor VPN Client - Main Entry Point
FreedomLink Linux v1.0.0
"""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator, QLocale
from gui.main_window import MainWindow
from core.config_manager import ConfigManager


def setup_application():
    """Настройка приложения"""
    # Включаем поддержку High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("AntiCensor VPN")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FreedomLink")
    
    # Настройка стиля
    app.setStyle("Fusion")
    
    # Тёмная тема
    from gui.theme import setup_dark_theme
    setup_dark_theme(app)
    
    return app


def main():
    """Точка входа"""
    # Инициализация конфигурации
    config = ConfigManager.get_instance()
    config.load()
    
    # Создание приложения
    app = setup_application()
    
    # Создание главного окна
    window = MainWindow(config)
    window.show()
    
    # Запуск цикла событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
