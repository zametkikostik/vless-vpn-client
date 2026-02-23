#!/bin/bash
# Установка VLESS Client Aggregator БЕЗ root прав
# В домашнюю директорию пользователя

set -e

echo "=============================================="
echo "VLESS Client Aggregator - Установка (без sudo)"
echo "=============================================="

BASE_DIR="$HOME/vpn-client"
BIN_DIR="$BASE_DIR/bin"
DATA_DIR="$BASE_DIR/data"
LOGS_DIR="$BASE_DIR/logs"
CONFIG_DIR="$BASE_DIR/config"

echo "[1/5] Создание директорий..."
mkdir -p "$BIN_DIR" "$DATA_DIR" "$LOGS_DIR" "$CONFIG_DIR"

echo "[2/5] Установка XRay-core..."
# Определяем архитектуру
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    XRAY_ARCH="64"
elif [ "$ARCH" = "aarch64" ]; then
    XRAY_ARCH="arm64-v8a"
elif [ "$ARCH" = "armv7l" ]; then
    XRAY_ARCH="arm32-v7a"
else
    echo "Неподдерживаемая архитектура: $ARCH"
    exit 1
fi

# Скачиваем последнюю версию
echo "Загрузка XRay..."
XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
echo "Версия XRay: $XRAY_VERSION"

cd /tmp
curl -L -o xray.zip "https://github.com/XTLS/Xray-core/releases/download/$XRAY_VERSION/Xray-linux-$XRAY_ARCH.zip"
unzip -o xray.zip
mv xray "$BIN_DIR/"
mv geoip.dat geosite.dat "$BIN_DIR/" 2>/dev/null || true
chmod +x "$BIN_DIR/xray"

echo "[3/5] Копирование клиента..."
cp /home/kostik/vpn-client-aggregator/vless_client.py "$BASE_DIR/"
chmod +x "$BASE_DIR/vless_client.py"

# Создаем symlink в ~/.local/bin
mkdir -p "$HOME/.local/bin"
ln -sf "$BASE_DIR/vless_client.py" "$HOME/.local/bin/vless-vpn"
ln -sf "$BIN_DIR/xray" "$HOME/.local/bin/xray"

echo "[4/5] Инициализация файлов..."
touch "$DATA_DIR/whitelist.txt"
touch "$DATA_DIR/blacklist.txt"
echo "[]" > "$DATA_DIR/servers.json"

echo "[5/5] Настройка PATH..."

# Добавляем в ~/.bashrc если нет
if ! grep -q ".local/bin" "$HOME/.bashrc" 2>/dev/null; then
    echo "" >> "$HOME/.bashrc"
    echo "# VPN Client PATH" >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# Экспортируем для текущей сессии
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "=============================================="
echo "✓ Установка завершена!"
echo "=============================================="
echo ""
echo "Важно: Перезапустите терминал или выполните:"
echo "  source ~/.bashrc"
echo ""
echo "Команды после перезапуска терминала:"
echo "  vless-vpn start        - Подключиться"
echo "  vless-vpn stop         - Отключиться"
echo "  vless-vpn status       - Статус"
echo "  vless-vpn update       - Обновить серверы"
echo ""
echo "Для работы в фоне используйте nohup:"
echo "  nohup vless-vpn start --auto &"
echo ""
echo "Логи:"
echo "  tail -f $LOGS_DIR/client.log"
echo ""
