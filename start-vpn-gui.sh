#!/bin/bash
#==============================================================================
# VLESS VPN GUI Launcher v4.0
# Запуск VPN клиента с проверкой зависимостей
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VPN_GUI_SCRIPT="$SCRIPT_DIR/vpn-gui.py"
PYTHON_BIN="python3"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка Python
if ! command -v $PYTHON_BIN &> /dev/null; then
    log_error "Python3 не найден!"
    exit 1
fi

log_info "Python: $($PYTHON_BIN --version)"

# Проверка PyQt5
if ! $PYTHON_BIN -c "import PyQt5" 2>/dev/null; then
    log_error "PyQt5 не установлен!"
    echo ""
    echo "Установите командой:"
    echo "  pip3 install PyQt5"
    echo ""
    exit 1
fi
log_success "PyQt5 установлен"

# Проверка Xray
if ! command -v xray &> /dev/null; then
    log_error "Xray не найден!"
    echo ""
    echo "Установите Xray-core:"
    echo "  bash -c \"\$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\""
    echo ""
    exit 1
fi
log_success "Xray: $(xray version | head -1)"

# Создание директорий
log_info "Создание директорий..."
mkdir -p "$SCRIPT_DIR/config"
mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/xray"

# Запуск GUI
log_info "Запуск VPN GUI..."
echo ""
exec $PYTHON_BIN "$VPN_GUI_SCRIPT" "$@"
