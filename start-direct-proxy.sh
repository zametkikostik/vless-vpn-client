#!/bin/bash
# Быстрый запуск прямого прокси

cd /home/kostik/vless-vpn-client

cat > config/config.json << 'CONF'
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": true}},
    {"port": 10809, "protocol": "http"}
  ],
  "outbounds": [{"protocol": "freedom"}]
}
CONF

pkill -9 xray
sleep 2
~/vpn-client/bin/xray run -c config/config.json &

sleep 3
echo "✅ ПРЯМОЙ ПРОКСИ ЗАПУЩЕН!"
echo ""
echo "Прокси:"
echo "  SOCKS5: 127.0.0.1:10808"
echo "  HTTP: 127.0.0.1:10809"
echo ""
echo "Настройте Firefox:"
echo "  SOCKS Сервер: 127.0.0.1"
echo "  Порт: 10808"
echo "  SOCKS v5"
echo ""
