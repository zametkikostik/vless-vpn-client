#!/bin/bash
#==============================================================================
# VLESS VPN Client — Установка для Linux Mint
# Автоматическая установка всех зависимостей и настройка
#==============================================================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "==============================================================================="
echo "  🛡️  VLESS VPN Client — Установка для Linux Mint"
echo "  Версия: 4.0 Professional"
echo "==============================================================================="
echo ""

# Проверка прав
if [[ $EUID -eq 0 ]]; then
   log_error "Не запускайте от root! Используйте sudo внутри скрипта."
   exit 1
fi

#------------------------------------------------------------------------------
# 1. Проверка системы
#------------------------------------------------------------------------------
log_info "Проверка системы..."

if ! grep -q "Linux Mint" /etc/os-release 2>/dev/null; then
    log_warn "Скрипт предназначен для Linux Mint. Другие дистрибутивы не тестировались."
fi

#------------------------------------------------------------------------------
# 2. Обновление системы
#------------------------------------------------------------------------------
log_info "Обновление пакетов..."
sudo apt update -qq

#------------------------------------------------------------------------------
# 3. Установка Python и зависимостей
#------------------------------------------------------------------------------
log_info "Установка Python зависимостей..."

if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip
fi

log_info "Установка PyQt5..."
if python3 -c "import PyQt5" 2>/dev/null; then
    log_success "PyQt5 уже установлен"
else
    sudo apt install -y python3-pyqt5 || pip3 install PyQt5
fi

#------------------------------------------------------------------------------
# 4. Установка Xray-core
#------------------------------------------------------------------------------
log_info "Проверка Xray-core..."

if command -v xray &> /dev/null; then
    log_success "Xray уже установлен: $(xray version | head -1)"
else
    log_info "Установка Xray-core..."
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"
    
    if command -v xray &> /dev/null; then
        log_success "Xray установлен: $(xray version | head -1)"
    else
        log_error "Не удалось установить Xray!"
        exit 1
    fi
fi

#------------------------------------------------------------------------------
# 5. Создание директорий
#------------------------------------------------------------------------------
log_info "Создание директорий..."

BASE_DIR="$HOME/vpn-client-aggregator"
mkdir -p "$BASE_DIR"/{config,data,logs,xray}

log_success "Директории созданы"

#------------------------------------------------------------------------------
# 6. Обновление symlink
#------------------------------------------------------------------------------
log_info "Обновление symlink vpn-gui..."

if [ -f "$BASE_DIR/update-symlink.sh" ]; then
    sudo bash "$BASE_DIR/update-symlink.sh"
    log_success "vpn-gui установлен в /usr/local/bin/vpn-gui"
else
    sudo ln -sf "$BASE_DIR/start-vpn-gui.sh" /usr/local/bin/vpn-gui
    sudo chmod +x /usr/local/bin/vpn-gui
    log_success "vpn-gui установлен (упрощённо)"
fi

#------------------------------------------------------------------------------
# 7. Настройка автозапуска
#------------------------------------------------------------------------------
log_info "Настройка автозапуска..."

cat > "$HOME/.config/autostart/vpn-client-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VLESS VPN Client
Comment=VPN Client for Linux Mint
Exec=$BASE_DIR/start-vpn-gui.sh
Icon=network-workgroup
Terminal=false
Categories=Network;Utility;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF

mkdir -p "$HOME/.config/autostart"
chmod +x "$HOME/.config/autostart/vpn-client-gui.desktop"

log_success "Автозапуск настроен"

#------------------------------------------------------------------------------
# 8. Загрузка списков доменов
#------------------------------------------------------------------------------
log_info "Загрузка списков доменов..."

WHITE_LIST="$BASE_DIR/data/white_list.txt"
if [ ! -f "$WHITE_LIST" ]; then
    wget -q -O "$WHITE_LIST" \
      "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt" \
      && log_success "Белый список загружен" \
      || log_warn "Не удалось загрузить белый список"
fi

DOMAIN_LISTS="$BASE_DIR/data/domain-lists.json"
if [ ! -f "$DOMAIN_LISTS" ]; then
    cat > "$DOMAIN_LISTS" << 'EOF'
{
  "social": ["facebook.com", "instagram.com", "twitter.com", "tiktok.com", "telegram.org", "whatsapp.com", "discord.com"],
  "video": ["youtube.com", "ytimg.com", "googlevideo.com", "vimeo.com", "twitch.tv"],
  "ai": ["openai.com", "chatgpt.com", "claude.ai", "anthropic.com", "gemini.google.com", "midjourney.com", "huggingface.co"],
  "blocked": ["meduza.io", "reuters.com", "bloomberg.com", "nytimes.com", "theguardian.com", "bbc.com"],
  "russian_direct": ["vk.com", "yandex.ru", "mail.ru", "ok.ru", "gosuslugi.ru", "sberbank.ru"]
}
EOF
    log_success "Списки доменов созданы"
fi

#------------------------------------------------------------------------------
# 9. Проверка установки
#------------------------------------------------------------------------------
log_info "Проверка установки..."

ERRORS=0

if ! command -v xray &> /dev/null; then
    log_error "Xray не найден!"
    ERRORS=$((ERRORS + 1))
fi

if ! python3 -c "import PyQt5" 2>/dev/null; then
    log_error "PyQt5 не найден!"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -f "/usr/local/bin/vpn-gui" ]; then
    log_error "vpn-gui не найден в /usr/local/bin!"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    log_error "Установка завершена с ошибками: $ERRORS"
    exit 1
fi

log_success "Все компоненты установлены"

#------------------------------------------------------------------------------
# 10. Финальное сообщение
#------------------------------------------------------------------------------
echo ""
echo "==============================================================================="
echo -e "  ${GREEN}✅ УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo "==============================================================================="
echo ""
echo "📍 Путь к клиенту: $BASE_DIR"
echo "🔗 Команда запуска: vpn-gui"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Запустите VPN GUI:"
echo "   vpn-gui"
echo ""
echo "2. В настройках укажите:"
echo "   - IP сервера VLESS"
echo "   - UUID клиента"
echo "   - Порт: 443"
echo "   - SNI: google.com"
echo ""
echo "3. Сохраните и подключитесь!"
echo ""
echo "📱 Для Android:"
echo "   Установите v2rayNG из Google Play"
echo "   Импортируйте VLESS ссылку с сервера"
echo ""
echo "📖 Документация:"
echo "   $BASE_DIR/README-VPN-GUI-v4.md"
echo "   $BASE_DIR/ANDROID-SETUP.md"
echo ""
echo "==============================================================================="
echo ""
