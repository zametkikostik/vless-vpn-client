#!/bin/bash
# Прямой запуск VPN - БЕЗ GUI, БЕЗ ПРОБЛЕМ!

echo "🚀 VLESS VPN - Прямой запуск"
echo "=============================="
echo ""

# Остановить старое
echo "⏹️  Остановка старых процессов..."
pkill -9 -f "vless-vpn" 2>/dev/null
pkill -9 -f "xray" 2>/dev/null
sleep 2

# Запустить XRay напрямую с лучшим сервером
echo "🔧 Получение лучшего сервера..."
SERVER=$(python3 -c "
import json
with open('/home/kostik/vpn-client/data/servers.json') as f:
    servers = json.load(f)
online = [s for s in servers if s.get('status') == 'online' and s.get('uuid')]
if online:
    best = min(online, key=lambda x: x.get('latency', 9999))
    print(f\"{best['host']}|{best['port']}|{best['uuid']}|{best.get('sni', best['host'])}\")
" 2>&1)

if [ -z "$SERVER" ]; then
    echo "❌ Не удалось получить сервер!"
    exit 1
fi

# Парсим
HOST=$(echo "$SERVER" | cut -d'|' -f1)
PORT=$(echo "$SERVER" | cut -d'|' -f2)
UUID=$(echo "$SERVER" | cut -d'|' -f3)
SNI=$(echo "$SERVER" | cut -d'|' -f4)

echo "✅ Сервер: $HOST:$PORT"
echo ""

# Создаём конфиг
echo "📝 Создание конфига..."
cat > ~/vpn-client/config/config.json << EOFCONFIG
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 10808,
      "protocol": "socks",
      "settings": {
        "auth": "noauth",
        "udp": true
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
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
      "tag": "proxy",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "$HOST",
            "port": $PORT,
            "users": [
              {
                "id": "$UUID",
                "encryption": "none",
                "flow": ""
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "serverName": "$SNI",
          "alpn": ["h2", "http/1.1"],
          "fingerprint": "chrome"
        }
      }
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": []
  }
}
EOFCONFIG

echo "✅ Конфиг создан"
echo ""

# Запуск XRay
echo "🚀 Запуск XRay..."
~/vpn-client/bin/xray run -c ~/vpn-client/config/config.json &
XRAY_PID=$!

sleep 5

# Проверка
if ps -p $XRAY_PID > /dev/null; then
    echo ""
    echo "✅ VPN ЗАПУЩЕН!"
    echo ""
    echo "📊 Информация:"
    echo "  Сервер: $HOST:$PORT"
    echo "  SOCKS5: 127.0.0.1:10808"
    echo "  HTTP: 127.0.0.1:10809"
    echo ""
    echo "🌐 Проверка:"
    echo "  curl --proxy socks5://127.0.0.1:10808 https://api.ipify.org"
    echo ""
    echo "🛑 Для остановки нажмите Ctrl+C"
    echo ""
    
    # Ждём
    wait $XRAY_PID
else
    echo "❌ XRay не запустился!"
    exit 1
fi
