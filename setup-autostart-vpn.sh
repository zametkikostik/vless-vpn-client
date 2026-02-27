#!/bin/bash
# VLESS VPN Ultimate - Настройка автозапуска

set -e

echo "========================================"
echo "🚀 Настройка автозапуска VLESS VPN"
echo "========================================"

USER_NAME=$(whoami)
HOME_DIR="/home/$USER_NAME"
SERVICE_FILE="$HOME_DIR/vless-vpn-client/vless-vpn-ultimate.service"
SYSTEMD_DIR="/etc/systemd/system"
AUTOSTART_DIR="$HOME_DIR/.config/autostart"

echo ""
echo "1️⃣ Настройка systemd сервиса..."

# Копируем сервис с заменой пользователя
sudo cp "$SERVICE_FILE" /tmp/vless-vpn-ultimate.service
sudo sed -i "s/%USER%/$USER_NAME/g" /tmp/vless-vpn-ultimate.service

# Устанавливаем сервис
sudo mv /tmp/vless-vpn-ultimate.service "$SYSTEMD_DIR/vless-vpn-ultimate.service"
sudo systemctl daemon-reload

echo "✅ Systemd сервис установлен"

echo ""
echo "2️⃣ Настройка GUI автозапуска..."

# Создаем директорию
mkdir -p "$AUTOSTART_DIR"

# Создаем desktop файл
cat > "$AUTOSTART_DIR/vless-vpn-ultimate.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=VLESS VPN с обходом DPI и Чебурнета
Exec=$HOME_DIR/vless-vpn-client/vless_client_ultimate.py start --auto
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF

chmod +x "$AUTOSTART_DIR/vless-vpn-ultimate.desktop"

echo "✅ GUI автозапуск настроен"

echo ""
echo "3️⃣ Проверка статуса..."

# Проверяем статус
if systemctl is-active --quiet vless-vpn-ultimate 2>/dev/null; then
    echo "✅ Сервис уже запущен"
else
    echo "⚠️ Сервис остановлен"
fi

echo ""
echo "========================================"
echo "✅ Автозапуск настроен!"
echo "========================================"
echo ""
echo "📌 Команды управления:"
echo ""
echo "  # Запустить сервис"
echo "  sudo systemctl start vless-vpn-ultimate"
echo ""
echo "  # Остановить сервис"
echo "  sudo systemctl stop vless-vpn-ultimate"
echo ""
echo "  # Включить автозапуск"
echo "  sudo systemctl enable vless-vpn-ultimate"
echo ""
echo "  # Выключить автозапуск"
echo "  sudo systemctl disable vless-vpn-ultimate"
echo ""
echo "  # Проверить статус"
echo "  sudo systemctl status vless-vpn-ultimate"
echo ""
echo "  # Посмотреть логи"
echo "  sudo journalctl -u vless-vpn-ultimate -f"
echo ""
echo "========================================"
