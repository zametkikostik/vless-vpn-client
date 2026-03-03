#!/bin/bash
# AntiCensor VPN - Обновление из GitHub

set -e

echo "🛡️ AntiCensor VPN - Обновление"
echo "================================"
echo ""

INSTALL_DIR="/opt/anticensor-vpn"

if [ ! -d "$INSTALL_DIR/.git" ]; then
    echo "❌ Репозиторий не найден. Установите приложение:"
    echo "   sudo ./scripts/install-from-github.sh"
    exit 1
fi

cd "$INSTALL_DIR"

echo "📦 Проверка обновлений..."
git fetch origin main

CURRENT=$(git rev-parse HEAD)
LATEST=$(git rev-parse origin/main)

if [ "$CURRENT" = "$LATEST" ]; then
    echo "✅ У вас последняя версия!"
    exit 0
fi

echo "📦 Найдено обновление, загружаем..."
git pull origin main

echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || true

echo ""
echo "✅ Обновление завершено!"
echo "Перезапустите приложение для применения изменений."
