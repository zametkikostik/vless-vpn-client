#!/bin/bash
#==============================================================================
# ФИНАЛЬНАЯ УСТАНОВКА VPN CLIENT v4.0
# Запускается от имени root/sudo
#==============================================================================

echo "🔧 Обновление VPN Client v4.0..."

# Обновление symlink
ln -sf /home/kostik/vpn-client-aggregator/start-vpn-gui.sh /usr/local/bin/vpn-gui
chmod +x /usr/local/bin/vpn-gui

# Проверка
echo ""
echo "✅ Symlink обновлён:"
ls -la /usr/local/bin/vpn-gui

# Проверка зависимостей
echo ""
echo "📋 Проверка зависимостей..."

if command -v xray &> /dev/null; then
    echo "✅ Xray: $(xray version | head -1)"
else
    echo "❌ Xray не установлен"
fi

if python3 -c "import PyQt5" 2>/dev/null; then
    echo "✅ PyQt5 установлен"
else
    echo "❌ PyQt5 не установлен"
    echo "   Установите: pip3 install PyQt5"
fi

echo ""
echo "==============================================================================="
echo "  🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "==============================================================================="
echo ""
echo "  Запуск VPN GUI: vpn-gui"
echo "  Путь к клиенту: /home/kostik/vpn-client-aggregator"
echo "  Документация: README-VPN-GUI-v4.md"
echo ""
