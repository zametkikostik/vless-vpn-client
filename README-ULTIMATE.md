# 🔒 VLESS VPN Ultimate

**VPN клиент нового поколения с обходом DPI и Чебурнета**

© 2026 VPN Client Aggregator

---

## 🚀 Возможности

### 🔧 DPI Bypass
- **Фрагментация пакетов** (50-200 байт)
- **Padding** (добавление случайных данных)
- **TLS мимикрия** под Chrome
- **Адаптивное переключение стратегий**

### 🛡️ Устойчивость к Чебурнету
- Автоматическое обнаружение блокировки
- Множественные попытки подключения
- Переключение между стратегиями обхода
- Мультиконнект

### 🌐 Сканер серверов
- **GitHub** (White/Black списки)
- **V2Ray Aggregator**
- **Leon406 SubCrawler**
- **Pawdroid Free-servers**
- Проверка пинга в реальном времени

### 🚀 Автозапуск
- Интеграция в меню приложений
- Автозапуск при старте системы
- Системный трей

---

## 📦 Установка

### Быстрая установка

```bash
cd ~/vless-vpn-client
chmod +x install-ultimate.sh
./install-ultimate.sh
```

### Ручная установка

```bash
# Установка зависимостей
pip3 install PyQt5 aiohttp

# Копирование скриптов
cp vless_client_ultimate.py ~/.local/bin/vless-vpn-ultimate
cp vpn_gui_ultimate.py ~/.local/bin/vless-vpn-gui
chmod +x ~/.local/bin/vless-vpn-ultimate ~/.local/bin/vless-vpn-gui
```

---

## 🎮 Использование

### GUI интерфейс

```bash
vless-vpn-gui gui
```

Или найдите **"VLESS VPN Ultimate"** в меню приложений.

### Консольные команды

```bash
# Запуск VPN
vless-vpn-ultimate start

# Запуск с автоподключением
vless-vpn-ultimate start --auto

# Остановка VPN
vless-vpn-ultimate stop

# Статус
vless-vpn-ultimate status

# Обновить серверы
vless-vpn-ultimate update

# Сканировать серверы
vless-vpn-ultimate scan

# Включить автозапуск
vless-vpn-ultimate autostart-enable

# Выключить автозапуск
vless-vpn-ultimate autostart-disable
```

---

## 🔧 Настройки DPI Bypass

### Стратегии обхода

1. **Fragmentation** - Фрагментация пакетов на мелкие части
2. **Padding** - Добавление случайных данных
3. **TLS Mimicry** - Мимикрия под обычный HTTPS трафик
4. **Multipath** - Множественные подключения
5. **Adaptive Switch** - Автоматическое переключение

### Конфигурация XRay

```json
{
  "fragment": {
    "packets": "tlshello",
    "length": "50-200",
    "interval": "10-50"
  },
  "streamSettings": {
    "sockopt": {
      "tcpNoDelay": true,
      "tcpKeepAliveInterval": 30
    }
  }
}
```

---

## 🌐 Источники серверов

### White списки
- `igareck/vpn-configs-for-russia/WHITE-CIDR-RU-all.txt`
- `Vless-Reality-White-Lists-Rus-Mobile.txt`

### Black списки
- `igareck/vpn-configs-for-russia/BLACK_VLESS_RUS.txt`
- `BLACK_VLESS_RUS_mobile.txt`

### Агрегаторы
- `mahdibland/V2RayAggregator`
- `Leon406/SubCrawler`
- `Pawdroid/Free-servers`

---

## 📊 Статистика

После сканирования вы увидите:
- **Всего серверов** - общее количество
- **Онлайн** - рабочие серверы
- **Средний пинг** - средняя задержка
- **Лучший сервер** - сервер с минимальным пингом

---

## 🔍 Сканер

### Запуск сканера

```bash
vless-vpn-ultimate scan
```

### Процесс сканирования

1. **Парсинг источников** - загрузка из всех источников
2. **Проверка пинга** - тестирование каждого сервера
3. **Сортировка** - по пингу (лучшие первыми)
4. **Сохранение** - в `servers.json`

---

## 🚀 Автозапуск

### Включение

```bash
vless-vpn-ultimate autostart-enable
```

### Выключение

```bash
vless-vpn-ultimate autostart-disable
```

### Файлы автозапуска

- `~/.config/autostart/vless-vpn-ultimate.desktop`
- `~/.local/share/applications/vless-vpn-ultimate.desktop`

---

## 📋 Логи

Логи сохраняются в:
```
~/vless-vpn-client/logs/client.log
```

### Просмотр логов

```bash
tail -f ~/vless-vpn-client/logs/client.log
```

---

## 🛡️ Безопасность

### Проверка серверов

- ✅ Только Reality протокол
- ✅ Проверка пинга перед подключением
- ✅ Автоматическое переключение при блокировке
- ✅ Без логов и телеметрии

### DPI Bypass статистика

```bash
vless-vpn-ultimate status
```

Показывает:
- Текущая стратегия
- Количество переключений
- Обнаружено блокировок
- Успешных обходов

---

## 🎨 GUI Функции

### Вкладка "Подключение"
- Большая кнопка подключения
- Статус подключения
- DPI Bypass индикатор
- Выбор локации
- Статистика серверов

### Вкладка "Сканер"
- Запуск сканирования
- Логи сканирования
- Результаты проверки

### Вкладка "Логи"
- Просмотр логов в реальном времени
- Фильтрация по уровню

### Системный трей
- Быстрый доступ
- Управление подключением
- Уведомления

---

## 🔧 Решение проблем

### VPN не подключается

1. Обновите серверы:
   ```bash
   vless-vpn-ultimate update
   ```

2. Проверьте XRay:
   ```bash
   ~/vpn-client/bin/xray version
   ```

3. Посмотрите логи:
   ```bash
   tail -100 ~/vless-vpn-client/logs/client.log
   ```

### GUI не запускается

1. Установите PyQt5:
   ```bash
   pip3 install PyQt5
   ```

2. Проверьте зависимости:
   ```bash
   python3 -c "import PyQt5; import aiohttp"
   ```

### Сканер не находит серверы

1. Проверьте интернет соединение
2. Попробуйте позже (источники могут быть недоступны)
3. Используйте ручное добавление серверов

---

## 📝 Структура проекта

```
vless-vpn-client/
├── vless_client_ultimate.py    # Основной клиент
├── vpn_gui_ultimate.py         # GUI интерфейс
├── install-ultimate.sh         # Скрипт установки
├── data/
│   └── servers.json            # База серверов
├── logs/
│   └── client.log              # Логи
├── config/
│   └── config.json             # Конфиг XRay
└── README-ULTIMATE.md          # Документация
```

---

## 🎯 Быстрый старт

```bash
# 1. Установка
./install-ultimate.sh

# 2. Запуск GUI
vless-vpn-gui gui

# 3. Подключение
# Нажмите "▶️ ПОДКЛЮЧИТЬ"

# 4. Проверка
vless-vpn-ultimate status
```

---

## 📞 Поддержка

### Документация
- [Официальная документация](README.md)
- [DPI Bypass](dpi_bypass.py)
- [Сканер](server_scanner.py)

### Логи
```bash
# Просмотр в реальном времени
tail -f ~/vless-vpn-client/logs/client.log
```

---

## 🎉 Особенности

✅ **Обход DPI** - многоуровневая защита  
✅ **Чебурнет** - адаптивное переключение стратегий  
✅ **Сканер** - все источники в одном месте  
✅ **Автозапуск** - интеграция в систему  
✅ **GUI** - удобный интерфейс  
✅ **Без логов** - полная приватность  

---

**Приятного использования! 🚀**
