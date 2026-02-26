#!/bin/bash
#==============================================================================
# VPN Client Aggregator v5.0 - Автоматическая установка
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
echo "  🛡️  VPN Client Aggregator v5.0 — Установка"
echo "==============================================================================="
echo ""

# Проверка прав
if [[ $EUID -eq 0 ]]; then
   log_error "Не запускайте от root!"
   exit 1
fi

BASE_DIR="$HOME/vpn-client-aggregator"

#------------------------------------------------------------------------------
# 1. Проверка системы
#------------------------------------------------------------------------------
log_info "Проверка системы..."

if ! command -v python3 &> /dev/null; then
    log_error "Python3 не найден!"
    exit 1
fi

log_success "Python: $(python3 --version)"

#------------------------------------------------------------------------------
# 2. Установка зависимостей
#------------------------------------------------------------------------------
log_info "Установка зависимостей..."

# Проверка PyQt5
if python3 -c "import PyQt5" 2>/dev/null; then
    log_success "PyQt5 уже установлен"
else
    log_info "Установка PyQt5..."
    sudo apt install -y python3-pyqt5 || pip3 install PyQt5 --break-system-packages
fi

# Проверка aiohttp
if python3 -c "import aiohttp" 2>/dev/null; then
    log_success "aiohttp уже установлен"
else
    log_info "Установка aiohttp..."
    pip3 install aiohttp --break-system-packages
fi

#------------------------------------------------------------------------------
# 3. Установка Xray-core
#------------------------------------------------------------------------------
log_info "Проверка Xray-core..."

if command -v xray &> /dev/null; then
    log_success "Xray уже установлен: $(xray version | head -1)"
else
    log_info "Установка Xray-core..."
    
    # Скачивание скрипта
    curl -L -o /tmp/xray-install.sh https://github.com/XTLS/Xray-install/raw/main/install-release.sh
    chmod +x /tmp/xray-install.sh
    
    # Установка
    sudo bash /tmp/xray-install.sh
    
    # Проверка
    if command -v xray &> /dev/null; then
        log_success "Xray установлен: $(xray version | head -1)"
    else
        log_error "Не удалось установить Xray!"
        exit 1
    fi
    
    # Очистка
    rm -f /tmp/xray-install.sh
fi

#------------------------------------------------------------------------------
# 4. Создание директорий
#------------------------------------------------------------------------------
log_info "Создание директорий..."

mkdir -p "$BASE_DIR"/{config,data,logs}

log_success "Директории созданы"

#------------------------------------------------------------------------------
# 5. Обновление symlink
#------------------------------------------------------------------------------
log_info "Обновление symlink vpn-gui..."

# Создание скрипта запуска
cat > "$BASE_DIR/run-gui.sh" << 'EOF'
#!/bin/bash
unset CARGO_ENV 2>/dev/null || true
cd "$(dirname "$0")"
exec python3 vpn_gui.py "$@"
EOF

chmod +x "$BASE_DIR/run-gui.sh"

# Обновление symlink
if [ -w /usr/local/bin ]; then
    ln -sf "$BASE_DIR/run-gui.sh" /usr/local/bin/vpn-gui 2>/dev/null || true
else
    sudo ln -sf "$BASE_DIR/run-gui.sh" /usr/local/bin/vpn-gui 2>/dev/null || true
fi

log_success "vpn-gui установлен"

#------------------------------------------------------------------------------
# 6. Настройка автозапуска
#------------------------------------------------------------------------------
log_info "Настройка автозапуска..."

mkdir -p "$HOME/.config/autostart"

cat > "$HOME/.config/autostart/vpn-client.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VPN Client Aggregator
Comment=VPN Client for Linux Mint
Exec=$BASE_DIR/run-gui.sh
Icon=network-workgroup
Terminal=false
Categories=Network;Utility;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF

chmod +x "$HOME/.config/autostart/vpn-client.desktop"

log_success "Автозапуск настроен"

#------------------------------------------------------------------------------
# 7. Загрузка начальных списков
#------------------------------------------------------------------------------
log_info "Загрузка списков доменов..."

# Создание файла со списками по умолчанию
cat > "$BASE_DIR/data/domain-lists.json" << 'EOF'
{
  "social": ["facebook.com", "instagram.com", "twitter.com", "tiktok.com", "telegram.org", "whatsapp.com", "discord.com"],
  "video": ["youtube.com", "ytimg.com", "googlevideo.com", "vimeo.com", "twitch.tv"],
  "ai": ["openai.com", "chatgpt.com", "claude.ai", "anthropic.com", "gemini.google.com", "midjourney.com", "huggingface.co", "lovable.dev"],
  "blocked_media": ["meduza.io", "reuters.com", "bloomberg.com", "nytimes.com", "theguardian.com", "bbc.com"],
  "russian_services": ["vk.com", "yandex.ru", "mail.ru", "ok.ru", "gosuslugi.ru", "sberbank.ru", "tinkoff.ru"]
}
EOF

log_success "Списки доменов созданы"

#------------------------------------------------------------------------------
# 8. Проверка установки
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

if ! python3 -c "import aiohttp" 2>/dev/null; then
    log_error "aiohttp не найден!"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    log_error "Установка завершена с ошибками: $ERRORS"
    exit 1
fi

log_success "Все компоненты установлены"

#------------------------------------------------------------------------------
# 9. Финальное сообщение
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
echo "📖 Документация:"
echo "   $BASE_DIR/README-v5.md"
echo ""
echo "==============================================================================="
echo ""
