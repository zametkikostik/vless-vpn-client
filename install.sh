#!/bin/bash
# VPN Client Aggregator - Установка
# Для Linux Mint/Ubuntu

set -e

echo "🛡️  VPN Client Aggregator - Установка"
echo "======================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите: sudo apt install python3"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Установка Xray
if ! command -v xray &> /dev/null; then
    echo "🔧 Установка Xray..."
    mkdir -p ~/vpn-client/bin
    cd ~/vpn-client/bin
    
    # Скачиваем Xray
    curl -L -o xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
    unzip -o xray.zip
    chmod +x xray
    rm xray.zip
    
    echo "✅ Xray установлен"
else
    echo "✅ Xray уже установлен"
fi

# Создание симлинков
echo "🔗 Создание симлинков..."
ln -sf $(pwd)/vless_client.py ~/.local/bin/vless-vpn 2>/dev/null || true
ln -sf $(pwd)/vpn_gui.py ~/.local/bin/vpn-gui 2>/dev/null || true
chmod +x ~/.local/bin/vless-vpn ~/.local/bin/vpn-gui 2>/dev/null || true

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p ~/vpn-client/{config,data,logs,bin}

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📚 Использование:"
echo "   GUI:      vpn-gui"
echo "   CLI:      vless-vpn start --auto"
echo "   Обновление: vless-vpn update"
echo ""
