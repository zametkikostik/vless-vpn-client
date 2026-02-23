#!/bin/bash
# VLESS VPN Controller - Быстрый запуск

CONTROLLER="/home/kostik/vpn-client-aggregator/vpn-controller.py"

case "$1" in
    menu)
        python3 "$CONTROLLER" menu
        ;;
    status)
        python3 "$CONTROLLER" status
        ;;
    auto)
        python3 "$CONTROLLER" auto
        ;;
    *)
        echo "VLESS VPN Controller"
        echo ""
        echo "Использование:"
        echo "  $0 menu   - Меню выбора локации"
        echo "  $0 status - Показать статус"
        echo "  $0 auto   - Автовыбор сервера"
        echo ""
        echo "Или запустите без параметров для интерактивного меню"
        python3 "$CONTROLLER"
        ;;
esac
