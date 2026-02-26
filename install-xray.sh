#!/bin/bash
#==============================================================================
# Установка Xray-core
#==============================================================================

echo "🚀 Установка Xray-core..."

# Скачиваем скрипт установки
curl -L -o /tmp/xray-install.sh https://github.com/XTLS/Xray-install/raw/main/install-release.sh

# Делаем исполняемым
chmod +x /tmp/xray-install.sh

# Запускаем установку
bash /tmp/xray-install.sh

# Проверяем установку
echo ""
if command -v xray &> /dev/null; then
    echo "✅ Xray установлен:"
    xray version | head -1
else
    echo "❌ Не удалось установить Xray"
fi

# Очищаем
rm -f /tmp/xray-install.sh
