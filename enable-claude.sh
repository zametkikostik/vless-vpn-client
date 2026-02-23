#!/bin/bash
# Скрипт для добавления серверов claude.com после обновления VPN

echo "🔄 Добавление серверов claude.com..."
python3 /home/kostik/vpn-client-aggregator/add-claude-servers.py

echo ""
echo "✅ Готово! Теперь можно подключиться к claude.com через VPN"
echo ""
echo "📋 Инструкция:"
echo "1. Откройте VPN клиент: python3 ~/vpn-client-aggregator/vpn-client-unified.py"
echo "2. Выберите локацию: 🤖 AI Services"
echo "3. Подключитесь к серверу"
echo "4. Откройте https://claude.com в браузере"
