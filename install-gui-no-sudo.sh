#!/bin/bash
# Установка VLESS VPN Client GUI БЕЗ root прав

set -e

echo "=============================================="
echo "VLESS VPN Client GUI - Установка (без sudo)"
echo "=============================================="

echo "[1/3] Установка PyQt5..."
pip3 install PyQt5

echo "[2/3] Настройка путей..."
# Проверяем что vpn-client установлен
if [ ! -f "$HOME/vpn-client/logs/client.log" ]; then
    echo "❌ Сначала установите VPN клиент:"
    echo "   /home/kostik/vpn-client-aggregator/install-no-sudo.sh"
    exit 1
fi

echo "[3/3] Создание ярлыка..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/vpn-client-gui.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VLESS VPN Client
Comment=VPN клиент с графическим интерфейсом
Exec=bash -c 'export PATH=\$HOME/.local/bin:\$PATH && python3 /home/kostik/vpn-client-aggregator/vpn_gui.py'
Icon=network-workgroup
Categories=Network;Utility;
Keywords=vpn;proxy;internet;
Terminal=false
StartupNotify=true
EOF

# Делаем скрипт запускаемым
chmod +x /home/kostik/vpn-client-aggregator/vpn_gui.py
chmod +x /home/kostik/vpn-client-aggregator/start-vpn-gui.sh

echo ""
echo "=============================================="
echo "✅ Установка завершена!"
echo "=============================================="
echo ""
echo "Запуск:"
echo "  1. Через меню приложений: VLESS VPN Client"
echo "  2. Из терминала:"
echo "     /home/kostik/vpn-client-aggregator/start-vpn-gui.sh"
echo ""
echo "Если PyQt5 не установился, выполните:"
echo "  pip3 install PyQt5"
echo ""

# Обновляем кэш меню
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo "Готово!"
