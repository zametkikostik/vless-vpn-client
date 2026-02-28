#!/bin/bash
# VLESS VPN - Активация STEALTH MODE
# Полная маскировка и обход DPI

set -e

echo "========================================"
echo "🥷 VLESS VPN - STEALTH MODE"
echo "========================================"
echo ""

USER_NAME=$(whoami)
HOME_DIR="/home/$USER_NAME"
BASE_DIR="$HOME_DIR/vless-vpn-client"

echo "1️⃣ Проверка зависимостей..."

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi

# Проверяем XRay
if [ ! -f "$HOME_DIR/vpn-client/bin/xray" ]; then
    echo "❌ XRay не найден!"
    exit 1
fi

echo "✅ Зависимости установлены"
echo ""

echo "2️⃣ Остановка текущего VPN..."
sudo systemctl stop vless-vpn-ultimate 2>/dev/null || true
pkill -f "xray run" 2>/dev/null || true
sleep 2
echo "✅ Остановлено"
echo ""

echo "3️⃣ Генерация stealth конфигурации..."

# Генерируем правильную конфигурацию
python3 "$BASE_DIR/stealth_config_gen.py" stealth

# Копируем как активную
cp "$BASE_DIR/config/stealth-config.json" "$BASE_DIR/config/config.json"

echo ""

echo "4️⃣ Запуск в stealth режиме..."

# Создаем временный сервис для stealth режима
cat > /tmp/vless-stealth.service << EOF
[Unit]
Description=VLESS VPN Stealth Mode
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
ExecStart=$HOME_DIR/vpn-client/bin/xray run -c $BASE_DIR/config/config.json
Restart=on-failure
RestartSec=10
Environment=PATH=/usr/bin:$HOME_DIR/.local/bin

# Security
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=false
ReadWritePaths=$BASE_DIR

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/vless-stealth.service /etc/systemd/system/vless-stealth.service
sudo systemctl daemon-reload
sudo systemctl enable vless-stealth
sudo systemctl start vless-stealth

echo "✅ Запущено"
echo ""

echo "5️⃣ Проверка статуса..."
sleep 5
systemctl status vless-stealth --no-pager | head -10

echo ""
echo "========================================"
echo "✅ STEALTH MODE АКТИВИРОВАН!"
echo "========================================"
echo ""
echo "📌 Особенности:"
echo "  🎭 Маскировка под российские сервисы"
echo "  🛡️ Улучшенный обход DPI"
echo "  😴 Спящий режим при проверке"
echo "  🔄 Резервные каналы"
echo ""
echo "📊 Команды управления:"
echo ""
echo "  # Статус"
echo "  systemctl status vless-stealth"
echo ""
echo "  # Остановить"
echo "  sudo systemctl stop vless-stealth"
echo ""
echo "  # Запустить"
echo "  sudo systemctl start vless-stealth"
echo ""
echo "  # Перезапустить"
echo "  sudo systemctl restart vless-stealth"
echo ""
echo "  # Логи"
echo "  sudo journalctl -u vless-stealth -f"
echo ""
echo "  # Вернуться в обычный режим"
echo "  sudo systemctl stop vless-stealth"
echo "  sudo systemctl start vless-vpn-ultimate"
echo ""
echo "========================================"
