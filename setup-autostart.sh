#!/bin/bash
# Автозапуск VPN клиента при загрузке для Linux Mint
# Установка в ~/.config/autostart

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VPN_SCRIPT="$SCRIPT_DIR/start-vpn-user.sh"

echo "Настройка автозапуска VPN..."

# Создаем скрипт запуска
cat > "$VPN_SCRIPT" << 'EOF'
#!/bin/bash
# Скрипт запуска VPN при старте системы

# Ждем подключения сети
sleep 10

# Экспортируем PATH
export PATH="$HOME/.local/bin:$PATH"

# Запускаем VPN в фоне
nohup vless-vpn start --auto > /home/kostik/vpn-client/logs/vpn.log 2>&1 &

# Настраиваем прокси в среде (опционально)
# export all_proxy=socks5://127.0.0.1:10808
# export https_proxy=http://127.0.0.1:10809

echo "VPN запущен" >> /home/kostik/vpn-client/logs/autostart.log
date >> /home/kostik/vpn-client/logs/autostart.log
EOF

chmod +x "$VPN_SCRIPT"

# Создаем .desktop файл для автозагрузки
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/vpn-client.desktop << EOF
[Desktop Entry]
Type=Application
Exec=$VPN_SCRIPT
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=VPN Client
Comment=Запуск VLESS VPN при загрузке
EOF

echo ""
echo "✓ Автозапуск настроен!"
echo ""
echo "Проверка:"
echo "  ls -la ~/.config/autostart/vpn-client.desktop"
echo ""
echo "Для проверки после перезагрузки:"
echo "  tail -f ~/vpn-client/logs/autostart.log"
echo ""
echo "Чтобы отключить автозапуск:"
echo "  rm ~/.config/autostart/vpn-client.desktop"
echo ""
