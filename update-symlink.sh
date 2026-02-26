#!/bin/bash
#==============================================================================
# Скрипт обновления symlink для vpn-gui
# Запускается с sudo пользователем
#==============================================================================

echo "Обновление symlink /usr/local/bin/vpn-gui..."
ln -sf /home/kostik/vpn-client-aggregator/start-vpn-gui.sh /usr/local/bin/vpn-gui
chmod +x /usr/local/bin/vpn-gui
echo "Готово!"
ls -la /usr/local/bin/vpn-gui
