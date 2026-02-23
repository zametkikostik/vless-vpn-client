#!/bin/bash
# Безопасное обновление репозитория (без секретных данных)

set -e

echo "🔒 Безопасное обновление репозитория..."
echo ""

# Переходим в директорию репозитория
cd ~/vpn-client-aggregator

# Проверяем, нет ли секретов в файлах
echo "🔍 Проверка на наличие секретных данных..."

# Поиск токенов GitHub
if grep -r "ghp_\|github_pat\|gho_\|ghu_" *.py 2>/dev/null; then
    echo "❌ Найдены GitHub токены! Удалите их перед коммитом."
    exit 1
fi

# Поиск API ключей
if grep -r "API_KEY.*=.*[a-zA-Z0-9]\{20,\}" *.py 2>/dev/null; then
    echo "❌ Найдены API ключи! Удалите их перед коммитом."
    exit 1
fi

# Поиск паролей
if grep -r "PASSWORD.*=.*[a-zA-Z0-9]\{8,\}" *.py 2>/dev/null; then
    echo "❌ Найдены пароли! Удалите их перед коммитом."
    exit 1
fi

echo "✅ Секретов не найдено"
echo ""

# Проверяем .gitignore
if [ ! -f .gitignore ]; then
    echo "❌ Файл .gitignore отсутствует!"
    exit 1
fi

echo "📝 .gitignore присутствует"
echo ""

# Показываем статус git
echo "📊 Статус репозитория:"
git status --short
echo ""

# Предлагаем сделать коммит
read -p "✅ Сделать коммит и отправить? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Добавляем все файлы
    git add -A
    
    # Проверяем, что не добавлены секретные файлы
    if git diff --cached --name-only | grep -E "\.log$|servers\.json|whitelist\.txt|blacklist\.txt"; then
        echo ""
        echo "⚠️  Внимание! В коммит попадают файлы с данными:"
        git diff --cached --name-only | grep -E "\.log$|servers\.json|whitelist\.txt|blacklist\.txt"
        read -p "Продолжить? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            # Исключаем секретные файлы
            git reset HEAD *.log data/servers.json data/whitelist.txt data/blacklist.txt 2>/dev/null || true
        fi
    fi
    
    # Делаем коммит
    read -p "Введите сообщение коммита: " message
    git commit -m "$message"
    
    # Отправляем
    echo "📤 Отправка в репозиторий..."
    git push origin main
    
    echo ""
    echo "✅ Репозиторий обновлён!"
else
    echo "ℹ️  Коммит отменён"
fi
