#!/bin/bash
# AntiCensor VPN - Установка из GitHub
# Использование: ./install-from-github.sh

set -e

echo "🛡️ AntiCensor VPN - Установка из GitHub"
echo "========================================"
echo ""

REPO_URL="https://github.com/zametkikostik/vless-vpn-client.git"
INSTALL_DIR="/opt/anticensor-vpn"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите от root (sudo)$NC"
    exit 1
fi

echo -e "${GREEN}✓ Проверка прав...${NC}"

# Обновление пакетов
echo "📦 Обновление пакетов..."
apt update

# Установка зависимостей
echo "📦 Установка зависимостей..."
apt install -y \
    python3 \
    python3-pip \
    python3-pyqt6 \
    python3-aiohttp \
    python3-requests \
    python3-cryptography \
    python3-psutil \
    git \
    wget \
    curl

echo -e "${GREEN}✓ Зависимости установлены${NC}"

# Установка Xray
echo "📦 Установка Xray-core..."
if ! command -v xray &> /dev/null; then
    wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O /tmp/xray.zip
    unzip -o /tmp/xray.zip -d /usr/bin/
    chmod +x /usr/bin/xray
    rm /tmp/xray.zip
    echo -e "${GREEN}✓ Xray установлен${NC}"
else
    echo -e "${YELLOW}⚠ Xray уже установлен${NC}"
fi

# Клонируем репозиторий
echo "📦 Загрузка из GitHub..."
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠ Предыдущая версия найдена, обновляем...${NC}"
    cd "$INSTALL_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    echo -e "${GREEN}✓ Репозиторий загружен${NC}"
fi

# Установка Python зависимостей
echo "📦 Установка Python зависимостей..."
pip3 install -r "$INSTALL_DIR/requirements.txt" --break-system-packages

echo -e "${GREEN}✓ Python зависимости установлены${NC}"

# Создание симлинка
echo "📦 Создание симлинка..."
ln -sf "$INSTALL_DIR/main.py" /usr/bin/anticensor-vpn
chmod +x /usr/bin/anticensor-vpn

# Создание .desktop файла
echo "📦 Создание .desktop файла..."
cat > /usr/share/applications/anticensor-vpn.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AntiCensor VPN
Comment=VPN клиент для обхода блокировок
Exec=/usr/bin/python3 $INSTALL_DIR/main.py
Icon=network-workgroup
Categories=Network;Internet;VPN;
Terminal=false
Keywords=vpn;proxy;anticensor;privacy;
EOF

echo -e "${GREEN}✓ .desktop файл создан${NC}"

# Обновление кэша
update-desktop-database 2>/dev/null || true

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Установка завершена!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Запуск:"
echo "  anticensor-vpn"
echo ""
echo "Или через меню приложений: AntiCensor VPN"
echo ""
echo "Обновление из GitHub:"
echo "  cd $INSTALL_DIR && sudo git pull && pip3 install -r requirements.txt --break-system-packages"
echo ""
