#!/bin/bash
# Установка VLESS VPN Client GUI для Linux Mint

set -e

echo "=============================================="
echo "VLESS VPN Client GUI - Установка"
echo "=============================================="

if [ "$1" = "--uninstall" ]; then
    echo "Удаление..."
    sudo rm -f /usr/local/bin/vpn-gui
    sudo rm -f /opt/vpn-client-gui/vpn_gui.py
    sudo rm -f ~/.config/autostart/vpn-client-gui.desktop
    rm -f /home/kostik/vpn-client-aggregator/start-vpn-gui.sh
    echo "✅ Удалено"
    exit 0
fi

echo "[1/3] Установка PyQt5..."
# Пробуем через apt сначала
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-pyqt5 || {
        echo "apt не удался, пробуем pip..."
        pip3 install PyQt5
    }
else
    pip3 install PyQt5
fi

echo "[2/3] Копирование файлов..."
sudo mkdir -p /opt/vpn-client-gui
sudo cp /home/kostik/vpn-client-aggregator/vpn_gui.py /opt/vpn-client-gui/
sudo cp /home/kostik/vpn-client-aggregator/start-vpn-gui.sh /opt/vpn-client-gui/
sudo chmod +x /opt/vpn-client-gui/*.py /opt/vpn-client-gui/*.sh

# Создаем symlink
sudo ln -sf /opt/vpn-client-gui/start-vpn-gui.sh /usr/local/bin/vpn-gui
sudo chmod +x /usr/local/bin/vpn-gui

echo "[3/3] Создание ярлыка в меню..."

# Ярлык для меню приложений
sudo mkdir -p /usr/share/applications
sudo cat > /usr/share/applications/vpn-client-gui.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=VLESS VPN Client
Comment=VPN клиент с графическим интерфейсом
Exec=/usr/local/bin/vpn-gui
Icon=network-workgroup
Categories=Network;Utility;
Keywords=vpn;proxy;internet;
Terminal=false
StartupNotify=true
EOF

# Копируем в локальное меню
mkdir -p ~/.local/share/applications
cp /usr/share/applications/vpn-client-gui.desktop ~/.local/share/applications/

echo ""
echo "=============================================="
echo "✅ Установка завершена!"
echo "=============================================="
echo ""
echo "Запуск:"
echo "  vpn-gui                    # Из терминала"
echo "  Меню приложений → VLESS VPN Client"
echo ""
echo "Удаление:"
echo "  sudo /home/kostik/vpn-client-aggregator/install-gui.sh --uninstall"
echo ""

# Предложение запустить
read -p "Запустить VPN Client сейчас? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    /usr/local/bin/vpn-gui &
fi
