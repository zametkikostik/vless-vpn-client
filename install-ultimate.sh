#!/bin/bash
# VLESS VPN Ultimate - Установка и настройка
# Обход DPI и Чебурнета + Сканер серверов + Автозапуск

set -e

echo "========================================"
echo "🔒 VLESS VPN Ultimate - Установка"
echo "========================================"

HOME_DIR="$HOME"
BASE_DIR="$HOME_DIR/vless-vpn-client"
BIN_DIR="$HOME_DIR/.local/bin"
AUTOSTART_DIR="$HOME_DIR/.config/autostart"
APPS_DIR="$HOME_DIR/.local/share/applications"

# Создаем директории
echo "📁 Создание директорий..."
mkdir -p "$BIN_DIR"
mkdir -p "$AUTOSTART_DIR"
mkdir -p "$APPS_DIR"
mkdir -p "$BASE_DIR/data"
mkdir -p "$BASE_DIR/logs"
mkdir -p "$BASE_DIR/config"

# Копируем скрипты
echo "📦 Копирование скриптов..."
cp "$BASE_DIR/vless_client_ultimate.py" "$BIN_DIR/vless-vpn-ultimate"
chmod +x "$BIN_DIR/vless-vpn-ultimate"

cp "$BASE_DIR/vpn_gui_ultimate.py" "$BIN_DIR/vless-vpn-gui"
chmod +x "$BIN_DIR/vless-vpn-gui"

# Создаем ярлык меню приложений
echo "🎨 Создание ярлыка в меню приложений..."
cat > "$APPS_DIR/vless-vpn-ultimate.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=VLESS VPN с обходом DPI и Чебурнета
Exec=$BIN_DIR/vless-vpn-gui gui
Icon=network-vpn
Terminal=false
Categories=Network;VPN;Utility;
Keywords=vpn;vless;proxy;dpi;bypass;cheburnet;
StartupNotify=false
MimeType=
EOF

chmod +x "$APPS_DIR/vless-vpn-ultimate.desktop"

# Создаем файл автозапуска
echo "🚀 Настройка автозапуска..."
cat > "$AUTOSTART_DIR/vless-vpn-ultimate.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=VLESS VPN с обходом DPI и Чебурнета
Exec=$BIN_DIR/vless-vpn-gui gui
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=15
EOF

chmod +x "$AUTOSTART_DIR/vless-vpn-ultimate.desktop"

# Проверяем зависимости
echo "📋 Проверка зависимостей..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION"

# Проверка PyQt5
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "⚠️ PyQt5 не установлен. Установка..."
    pip3 install PyQt5 --quiet
fi

# Проверка aiohttp для сканера
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "⚠️ aiohttp не установлен. Установка..."
    pip3 install aiohttp --quiet
fi

# Проверка XRay
XRAY_BIN="$HOME_DIR/vpn-client/bin/xray"
if [ ! -f "$XRAY_BIN" ]; then
    echo "⚠️ XRay не найден. Установка..."
    
    # Создаем директорию
    mkdir -p "$HOME_DIR/vpn-client/bin"
    
    # Загружаем XRay
    cd /tmp
    curl -L -o xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
    unzip -o xray.zip
    mv xray "$XRAY_BIN"
    chmod +x "$XRAY_BIN"
    
    echo "✅ XRay установлен"
    cd -
else
    echo "✅ XRay найден"
fi

# Обновление базы серверов
echo "🔄 Первичное сканирование серверов..."
python3 "$BASE_DIR/vless_client_ultimate.py" update || echo "⚠️ Сканирование не удалось (можно запустить вручную)"

# Итоговое сообщение
echo ""
echo "========================================"
echo "✅ Установка завершена!"
echo "========================================"
echo ""
echo "📌 Команды:"
echo "   vless-vpn-gui gui     - Запуск GUI"
echo "   vless-vpn-ultimate start  - Запуск VPN (консоль)"
echo "   vless-vpn-ultimate stop   - Остановка VPN"
echo "   vless-vpn-ultimate status - Статус VPN"
echo "   vless-vpn-ultimate update - Обновить серверы"
echo "   vless-vpn-ultimate scan   - Сканировать серверы"
echo ""
echo "🎨 Меню приложений:"
echo "   Ищите 'VLESS VPN Ultimate' в меню приложений"
echo ""
echo "🚀 Автозапуск:"
echo "   VPN автоматически запускается при входе в систему"
echo ""
echo "🔧 Настройка автозапуска:"
echo "   vless-vpn-ultimate autostart-enable  - Включить"
echo "   vless-vpn-ultimate autostart-disable - Выключить"
echo ""
echo "========================================"
echo "🎉 Удачи! Обход DPI и Чебурнета активирован!"
echo "========================================"
