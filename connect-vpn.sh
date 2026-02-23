#!/bin/bash
# Прямое подключение к VPN (без GUI проблем)

echo "🔒 VLESS VPN - Прямое подключение"
echo "=================================="
echo ""

# 1. Остановить все VPN процессы
echo "⏹️  Остановка старых процессов..."
pkill -f "vless-vpn" 2>/dev/null || true
pkill -f "xray" 2>/dev/null || true
pkill -f "vpn_gui.py" 2>/dev/null || true
sleep 3

# 2. Очистить логи
> ~/vpn-client/logs/client.log

# 3. Запустить VPN в режиме FULL
echo "🚀 Запуск VPN в режиме FULL..."
~/.local/bin/vless-vpn start --auto --mode full &
VPN_PID=$!

echo "⏳ Ожидание подключения..."
echo ""

# 4. Мониторим подключение
for i in {1..90}; do
    STATUS=$(~/.local/bin/vless-vpn status 2>&1 | grep -E "✓ Подключен|✗ Не подключен")
    
    if echo "$STATUS" | grep -q "✓ Подключен"; then
        echo ""
        echo "✅ VPN ПОДКЛЮЧЕН!"
        echo ""
        ~/.local/bin/vless-vpn status
        echo ""
        echo "💡 Для доступа к AI-сервисам (Claude, ChatGPT, Lovable):"
        echo "   source ~/.vpn_proxy.sh"
        echo ""
        echo "📋 Логи: tail -f ~/vpn-client/logs/client.log"
        exit 0
    fi
    
    # Показываем прогресс каждые 10 секунд
    if [ $((i % 10)) -eq 0 ]; then
        echo "⏳ Подключение... ($i сек)"
        tail -3 ~/vpn-client/logs/client.log 2>/dev/null | grep -E "онлайн|Тестирование" || true
    fi
    
    sleep 1
done

echo ""
echo "⚠️  Превышено время ожидания (90 сек)"
echo ""
echo "📋 Последние логи:"
tail -20 ~/vpn-client/logs/client.log
echo ""
echo "🔧 Попробуйте ещё раз или проверьте соединение с интернетом"
exit 1
