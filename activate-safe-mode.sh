#!/bin/bash
# VLESS VPN - Safe Mode (Безопасный режим)
# Маскировка под легитимный трафик

set -e

echo "========================================"
echo "🛡️ VLESS VPN - SAFE MODE"
echo "========================================"
echo ""

USER_NAME=$(whoami)
HOME_DIR="/home/$USER_NAME"
BASE_DIR="$HOME_DIR/vless-vpn-client"

echo "1️⃣ Проверка..."

# Проверяем XRay
if [ ! -f "$HOME_DIR/vpn-client/bin/xray" ]; then
    echo "❌ XRay не найден!"
    exit 1
fi

echo "✅ Проверка пройдена"
echo ""

echo "2️⃣ Остановка текущего VPN..."
sudo systemctl stop vless-vpn-ultimate 2>/dev/null || true
sudo systemctl stop vless-stealth 2>/dev/null || true
pkill -f "xray run" 2>/dev/null || true
sleep 2
echo "✅ Остановлено"
echo ""

echo "3️⃣ Генерация безопасной конфигурации..."

# Конфигурация с маскировкой под легитимный трафик
cat > "$BASE_DIR/config/safe-config.json" << 'JSONEOF'
{
  "log": {
    "level": "warning",
    "access": "/home/kostik/vless-vpn-client/logs/xray_access.log",
    "error": "/home/kostik/vless-vpn-client/logs/xray_error.log"
  },
  "inbounds": [
    {
      "port": 10808,
      "protocol": "socks",
      "settings": {
        "auth": "noauth",
        "udp": true,
        "ip": "127.0.0.1"
      }
    },
    {
      "port": 10809,
      "protocol": "http",
      "settings": {
        "allowTransparent": false
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "your-server.com",
            "port": 443,
            "users": [
              {
                "id": "your-uuid-here",
                "encryption": "none",
                "flow": "xtls-rprx-vision"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "api.gosuslugi.ru:443",
          "serverNames": ["api.gosuslugi.ru"],
          "fingerprint": "chrome",
          "publicKey": "your-public-key",
          "shortId": "your-short-id",
          "spiderX": "/api/v2/portal/oidc"
        },
        "sockopt": {
          "tcpNoDelay": true,
          "tcpKeepAliveInterval": 30,
          "mark": 255
        }
      }
    }
  ],
  "dns": {
    "servers": [
      "https://dns.yandex.ru/dns-query",
      "https://common.dot.sber.ru/dns-query",
      "1.1.1.1"
    ],
    "queryStrategy": "UseIPv4"
  },
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "domain": [
          "geosite:category-gov-ru",
          "geosite:yandex",
          "geosite:vk"
        ],
        "outboundTag": "direct"
      }
    ]
  }
}
JSONEOF

echo "✅ Конфигурация создана"
echo ""

echo "4️⃣ Настройка безопасного режима..."

# Создаем systemd сервис для safe mode
cat > /tmp/vless-safe.service << EOF
[Unit]
Description=VLESS VPN Safe Mode
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
ExecStart=$HOME_DIR/vpn-client/bin/xray run -c $BASE_DIR/config/safe-config.json
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

sudo cp /tmp/vless-safe.service /etc/systemd/system/vless-safe.service
sudo systemctl daemon-reload

echo "✅ Настройка завершена"
echo ""

echo "5️⃣ Запуск..."
sudo systemctl enable vless-safe
sudo systemctl start vless-safe

sleep 5

echo ""
echo "========================================"
echo "✅ SAFE MODE АКТИВИРОВАН!"
echo "========================================"
echo ""

# Проверка статуса
systemctl status vless-safe --no-pager | head -10

echo ""
echo "📌 Особенности:"
echo "  🎭 Маскировка под ГосУслуги API"
echo "  🛡️ Российские DNS серверы"
echo "  🔒 Прямой доступ к РФ сайтам"
echo "  😴 Минимальная активность"
echo ""
echo "⚠️ Важно:"
echo "  - Не используйте для запрещенных ресурсов"
echo "  - Трафик выглядит как доступ к госуслугам"
echo "  - DNS через Яндекс и Сбербанк"
echo ""
echo "📊 Команды управления:"
echo ""
echo "  # Статус"
echo "  systemctl status vless-safe"
echo ""
echo "  # Остановить"
echo "  sudo systemctl stop vless-safe"
echo ""
echo "  # Запустить"
echo "  sudo systemctl start vless-safe"
echo ""
echo "  # Логи"
echo "  sudo journalctl -u vless-safe -f"
echo ""
echo "  # Вернуться в обычный режим"
echo "  sudo systemctl stop vless-safe"
echo "  sudo systemctl start vless-vpn-ultimate"
echo ""
echo "========================================"
