#!/bin/bash
# Wrapper script для автозапуска VPN с GUI

# Ждем полной загрузки DE
sleep 15

# Экспортируем DISPLAY для GUI
export DISPLAY=:0
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u kostik)/bus"

# Переходим в директорию
cd /home/kostik/vless-vpn-client

# Проверяем, не запущен ли уже VPN
if pgrep -f "vpn_gui_ultimate.py start" > /dev/null; then
    echo "VPN уже запущен"
    exit 0
fi

# Запускаем GUI
/usr/bin/python3 /home/kostik/vless-vpn-client/vpn_gui_ultimate.py start >> /home/kostik/vless-vpn-client/logs/autostart.log 2>&1 &
