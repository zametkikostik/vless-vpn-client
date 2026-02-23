#!/bin/bash
# Скрипт установки VLESS Client Aggregator для Linux Mint
# Запускать от root или с sudo

set -e

echo "=============================================="
echo "VLESS Client Aggregator - Установка"
echo "=============================================="

BASE_DIR="/opt/vpn-client-aggregator"
LINK_DIR="/usr/local/bin/vless-vpn"

# Проверка на root
if [ "$EUID" -ne 0 ]; then 
    echo "Запустите скрипт с sudo: sudo ./install.sh"
    exit 1
fi

echo "[1/6] Установка зависимостей..."
apt-get update
apt-get install -y python3 python3-pip curl unzip systemd

echo "[2/6] Установка XRay-core..."
# Скачиваем последнюю версию XRay
XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
echo "Версия XRay: $XRAY_VERSION"

# Определяем архитектуру
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    XRAY_ARCH="64"
elif [ "$ARCH" = "aarch64" ]; then
    XRAY_ARCH="arm64-v8a"
elif [ "$ARCH" = "armv7l" ]; then
    XRAY_ARCH="arm32-v7a"
else
    echo "Неподдерживаемая архитектура: $ARCH"
    exit 1
fi

# Скачиваем и устанавливаем XRay
cd /tmp
curl -L -o xray.zip "https://github.com/XTLS/Xray-core/releases/download/$XRAY_VERSION/Xray-linux-$XRAY_ARCH.zip"
unzip -o xray.zip
mv xray /usr/local/bin/
mv xray geoip.dat geosite.dat /usr/local/bin/ 2>/dev/null || true
chmod +x /usr/local/bin/xray

echo "[3/6] Копирование файлов клиента..."
mkdir -p "$BASE_DIR"/{config,logs,scripts,data}
cp /home/kostik/vpn-client-aggregator/vless_client.py "$BASE_DIR/"
chmod +x "$BASE_DIR/vless_client.py"

# Создаем символическую ссылку
ln -sf "$BASE_DIR/vless_client.py" "$LINK_DIR"
chmod +x "$LINK_DIR"

echo "[4/6] Создание службы systemd..."
cat > /etc/systemd/system/vless-vpn.service << 'EOF'
[Unit]
Description=VLESS VPN Client Aggregator
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vpn-client-aggregator
ExecStart=/usr/bin/python3 /opt/vpn-client-aggregator/vless_client.py start --auto
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vless-vpn

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "[5/6] Инициализация файлов..."
# Создаем пустые списки
touch "$BASE_DIR/data/whitelist.txt"
touch "$BASE_DIR/data/blacklist.txt"
touch "$BASE_DIR/data/servers.json"
echo "[]" > "$BASE_DIR/data/servers.json"

# Права доступа
chmod 644 "$BASE_DIR/data/"*
chmod 755 "$BASE_DIR"

echo "[6/6] Проверка установки..."
echo ""
echo "Проверка XRay:"
xray version | head -2

echo ""
echo "Проверка клиента:"
python3 "$BASE_DIR/vless_client.py" --help | head -5

echo ""
echo "=============================================="
echo "✓ Установка завершена!"
echo "=============================================="
echo ""
echo "Команды управления:"
echo "  sudo systemctl start vless-vpn     - Запустить VPN"
echo "  sudo systemctl stop vless-vpn      - Остановить VPN"
echo "  sudo systemctl status vless-vpn    - Статус VPN"
echo "  sudo systemctl enable vless-vpn    - Автозапуск при загрузке"
echo ""
echo "Ручное управление:"
echo "  vless-vpn start        - Подключиться"
echo "  vless-vpn stop         - Отключиться"
echo "  vless-vpn status       - Показать статус"
echo "  vless-vpn update       - Обновить список серверов"
echo ""
echo "Настройка прокси в системе:"
echo "  export http_proxy=http://127.0.0.1:10809"
echo "  export https_proxy=http://127.0.0.1:10809"
echo "  export all_proxy=socks5://127.0.0.1:10808"
echo ""
echo "Логи:"
echo "  journalctl -u vless-vpn -f"
echo "  tail -f /opt/vpn-client-aggregator/logs/client.log"
echo ""
