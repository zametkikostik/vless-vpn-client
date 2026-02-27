#!/bin/bash
# Быстрое исправление VPN

cd /home/kostik/vless-vpn-client

echo "🔧 Исправление VPN..."

# Остановить XRay
pkill -9 xray
sleep 2

# Загрузить рабочие серверы
if [ -f "data/working_reality_servers.json" ]; then
    # Взять первый рабочий сервер
    SERVER=$(python3 -c "import json; d=json.load(open('data/working_reality_servers.json')); print(d['servers'][0]['host'] if d.get('servers') else '')")
    
    if [ -n "$SERVER" ]; then
        echo "✅ Сервер найден: $SERVER"
        
        # Запустить VPN
        python3 vless_client_ultimate.py start > /tmp/vpn.log 2>&1 &
        
        sleep 8
        
        # Проверить
        if curl -x socks5h://127.0.0.1:10808 -s --connect-timeout 5 https://www.google.com > /dev/null; then
            echo "✅ VPN РАБОТАЕТ!"
            echo ""
            echo "Прокси:"
            echo "  SOCKS5: 127.0.0.1:10808"
            echo "  HTTP: 127.0.0.1:10809"
        else
            echo "❌ VPN НЕ работает"
            echo "Запустите: python3 test-reality-servers.py"
        fi
    else
        echo "❌ Нет рабочих серверов"
        echo "Запустите: python3 test-reality-servers.py"
    fi
else
    echo "❌ Файл рабочих серверов не найден"
    echo "Запустите: python3 test-reality-servers.py"
fi
