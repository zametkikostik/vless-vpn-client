#!/bin/bash
# Стабильный запуск VPN (без GUI проблем)

set -e

echo "🔒 VLESS VPN - Стабильный запуск"
echo "=================================="
echo ""

# Остановить все VPN процессы
echo "⏹️  Остановка старых процессов..."
pkill -f "vless-vpn" 2>/dev/null || true
pkill -f "xray" 2>/dev/null || true
sleep 2

# Очистить логи (опционально)
# rm -f ~/vpn-client/logs/*.log

# Запустить VPN в режиме FULL (для AI-сервисов)
echo "🚀 Запуск VPN в режиме FULL..."
~/.local/bin/vless-vpn start --auto --mode full &
VPN_PID=$!

# Ждём тестирования серверов (около 30-60 сек)
echo "⏳ Ожидание подключения (30-60 сек)..."
echo ""

# Мониторим лог
for i in {1..60}; do
    if tail -5 ~/vpn-client/logs/client.log 2>/dev/null | grep -q "Подключен"; then
        echo ""
        echo "✅ VPN ПОДКЛЮЧЕН!"
        echo ""
        ~/.local/bin/vless-vpn status
        echo ""
        echo "💡 Для доступа к AI-сервисам выполните:"
        echo "   source ~/.vpn_proxy.sh"
        echo ""
        echo "📋 Логи: tail -f ~/vpn-client/logs/client.log"
        exit 0
    fi
    sleep 1
done

echo ""
echo "⚠️  Превышено время ожидания"
echo "📋 Проверьте логи:"
tail -20 ~/vpn-client/logs/client.log
