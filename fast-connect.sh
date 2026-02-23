#!/bin/bash
# БЫСТРОЕ ПОДКЛЮЧЕНИЕ К VPN - 5 СЕКУНД!
# Без долгого тестирования

echo "🚀 БЫСТРОЕ ПОДКЛЮЧЕНИЕ К VPN..."
echo "⏱️ Время подключения: ~5 секунд"
echo ""

# Остановить старое
pkill -9 -f "vless-vpn" 2>/dev/null
pkill -9 -f "xray" 2>/dev/null
sleep 1

# Получить сервер из кэша (с полными параметрами!)
echo "📡 Выбор сервера из кэша..."
SERVER_INFO=$(python3 << 'PYEOF'
import json
try:
    with open('/home/kostik/vpn-client/data/servers.json') as f:
        servers = json.load(f)
    
    # Найти онлайн серверы с UUID (не chatgpt.com!)
    online = [s for s in servers if s.get('status') == 'online' and s.get('uuid') and 'chatgpt' not in s.get('host', '').lower()]
    
    if online:
        # Сортировать по пингу
        online.sort(key=lambda x: x.get('latency', 9999))
        
        # Взять лучший сервер с полными параметрами
        for server in online[:10]:  # Проверить первые 10
            # Проверить что есть все параметры
            if server.get('uuid') and server.get('host') and server.get('port'):
                stream = server.get('streamSettings', {})
                security = stream.get('security', 'tls')
                tls = stream.get('tlsSettings', {})
                reality = stream.get('realitySettings', {})
                
                # Использовать первый подходящий
                host = server['host']
                port = server['port']
                uuid = server['uuid']
                sni = reality.get('serverName', tls.get('serverName', host))
                flow = server.get('flow', '')
                public_key = reality.get('publicKey', '')
                short_id = reality.get('shortId', '')
                
                print(f"{host}|{port}|{uuid}|{sni}|{flow}|{public_key}|{short_id}")
                break
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
)

if [ -z "$SERVER_INFO" ] || [[ "$SERVER_INFO" == ERROR* ]]; then
    echo "❌ Не удалось получить сервер!"
    exit 1
fi

# Парсинг
HOST=$(echo "$SERVER_INFO" | cut -d'|' -f1)
PORT=$(echo "$SERVER_INFO" | cut -d'|' -f2)
UUID=$(echo "$SERVER_INFO" | cut -d'|' -f3)
SNI=$(echo "$SERVER_INFO" | cut -d'|' -f4)
FLOW=$(echo "$SERVER_INFO" | cut -d'|' -f5)
PUBLIC_KEY=$(echo "$SERVER_INFO" | cut -d'|' -f6)
SHORT_ID=$(echo "$SERVER_INFO" | cut -d'|' -f7)

echo "✅ Сервер: $HOST:$PORT (SNI: $SNI)"

# Определить тип безопасности
if [ -n "$PUBLIC_KEY" ]; then
    SECURITY="reality"
    echo "🔒 Reality: $SNI"
else
    SECURITY="tls"
    echo "🔒 TLS: $SNI"
fi

# Создать конфиг
if [ "$SECURITY" = "reality" ]; then
    # Reality конфиг
    cat > ~/vpn-client/config/config.json << EOFCONFIG
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "port": 10808,
      "protocol": "socks",
      "settings": {"auth": "noauth", "udp": true},
      "sniffing": {"enabled": true, "destOverride": ["http", "tls"]}
    },
    {
      "port": 10809,
      "protocol": "http",
      "settings": {"allowTransparent": false}
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
                "flow": "$FLOW"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "serverName": "$SNI",
          "fingerprint": "chrome",
          "publicKey": "$PUBLIC_KEY",
          "shortId": "$SHORT_ID"
        }
      }
    }
  ]
}
EOFCONFIG
else
    # TLS конфиг
    cat > ~/vpn-client/config/config.json << EOFCONFIG
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "port": 10808,
      "protocol": "socks",
      "settings": {"auth": "noauth", "udp": true},
      "sniffing": {"enabled": true, "destOverride": ["http", "tls"]}
    },
    {
      "port": 10809,
      "protocol": "http",
      "settings": {"allowTransparent": false}
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
  ]
}
EOFCONFIG
fi

echo "✅ Конфиг создан"

# Запустить XRay напрямую (БЕЗ vless-vpn!)
echo "🚀 Запуск XRay..."
~/vpn-client/bin/xray run -c ~/vpn-client/config/config.json &
XRAY_PID=$!

# Ждём запуска
sleep 3

# Проверка
if ps -p $XRAY_PID > /dev/null 2>&1; then
    echo ""
    echo "✅ VPN ПОДКЛЮЧЕН!"
    echo ""
    echo "📊 Информация:"
    echo "  Сервер: $HOST:$PORT"
    echo "  SOCKS5: 127.0.0.1:10808"
    echo "  HTTP: 127.0.0.1:10809"
    echo "  PID: $XRAY_PID"
    echo ""
    echo "🌐 Проверка:"
    echo "  curl --proxy socks5://127.0.0.1:10808 https://api.ipify.org"
    echo ""
    echo "🛑 Для остановки:"
    echo "  pkill -f xray"
else
    echo "❌ XRay не запустился!"
    exit 1
fi
