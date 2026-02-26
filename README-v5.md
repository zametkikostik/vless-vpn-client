# 🛡️ VPN Client Aggregator v5.0

**Профессиональный VPN клиент для Linux Mint с устойчивым соединением без обрывов**

---

## 📋 Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Настройка](#настройка)
- [Команды](#команды)
- [Структура проекта](#структура-проекта)

---

## 🚀 Возможности

### Основные
- ✅ **VLESS-Reality** — современный протокол с маскировкой под HTTPS
- ✅ **Обход DPI** — многоуровневая защита (фрагментация, padding, TLS mimicry)
- ✅ **Split-tunneling** — раздельное туннелирование по категориям
- ✅ **Автопереподключение** — защита от разрывов соединения
- ✅ **GUI интерфейс** — PyQt5 с системным треем
- ✅ **Мониторинг трафика** — скорость, объём, время подключения
- ✅ **Автозагрузка списков** — из GitHub (соцсети, видео, ИИ, заблокированные)

### Обход DPI
- 📦 Фрагментация пакетов (50-200 байт)
- 🎭 Маскировка TLS fingerprint (Chrome 120+)
- 🔀 Padding (добавление случайных данных)
- 🌐 Domain fronting (использование доверенных доменов)

### Split-tunneling
| Категория | Через VPN | Напрямую |
|-----------|-----------|----------|
| Соцсети | Facebook, Instagram, Twitter, TikTok | VK, OK |
| Видео | YouTube, Vimeo, Twitch | Rutube, Kinopoisk |
| ИИ | ChatGPT, Claude, Gemini, **Lovable.dev** | YandexGPT |
| СМИ | Заблокированные издания | Российские СМИ |
| Банки | — | Сбербанк, Тинькофф, Альфа |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI Interface (PyQt5)                    │
│              vpn_gui.py - Графический интерфейс             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  VPN Controller (Контроллер)                │
│           vpn_controller.py - Управление VPN                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    VPN Engine (Ядро)                        │
│            vpn_engine.py - Запуск Xray, мониторинг          │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Config    │ │    DPI      │ │   Split     │ │ Connection  │
│   Manager   │ │   Bypass    │ │   Tunnel    │ │  Monitor    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 📦 Установка

### 1. Установка зависимостей

```bash
# Python зависимости
pip3 install PyQt5 aiohttp

# Или через apt
sudo apt update
sudo apt install python3-pyqt5 python3-aiohttp
```

### 2. Установка Xray-core

```bash
# Автоматическая установка
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"

# Проверка
xray version
```

### 3. Запуск клиента

```bash
# Через symlink (если установлен)
vpn-gui

# Или напрямую
python3 /home/kostik/vpn-client-aggregator/main.py gui
```

---

## ⚡ Быстрый старт

### 1. Запуск GUI

```bash
vpn-gui
```

### 2. Настройка сервера

1. Откройте вкладку **"Настройки сервера"**
2. Введите:
   - **Адрес сервера**: IP вашего VPS
   - **Порт**: 443
   - **UUID**: сгенерируйте кнопкой или вставьте свой
   - **SNI**: google.com
3. Нажмите **"Сохранить настройки"**

### 3. Настройка Split-tunneling

1. Откройте вкладку **"Split-tunneling"**
2. Выберите категории для VPN:
   - ✅ Соцсети
   - ✅ Видеохостинги
   - ✅ ИИ-сервисы
   - ✅ Заблокированные СМИ
3. Нажмите **"Сохранить настройки"**

### 4. Подключение

1. Вернитесь на главную вкладку
2. Нажмите **"▶️ Подключить"**
3. Дождитесь **"✅ Подключён"**

---

## 🎮 Команды

### GUI

```bash
vpn-gui              # Запуск интерфейса
```

### Консоль

```bash
# Запуск консольного интерфейса
python3 main.py console

# Проверка зависимостей
python3 main.py check

# Справка
python3 main.py help
```

### Консольный интерфейс

```
🔹 vpn> start          # Подключить VPN
🔹 vpn> stop           # Отключить VPN
🔹 vpn> restart        # Перезапустить
🔹 vpn> status         # Показать статус
🔹 vpn> stats          # Показать статистику
🔹 vpn> uuid generate  # Сгенерировать UUID
🔹 vpn> server set ... # Настроить сервер
🔹 vpn> split on       # Включить split-tunneling
🔹 vpn> quit           # Выход
```

---

## 📁 Структура проекта

```
vpn-client-aggregator/
├── main.py                     # Точка входа
├── vpn_gui.py                  # GUI интерфейс (PyQt5)
├── vpn_controller.py           # Контроллер управления
├── vpn_engine.py               # Ядро VPN
│
├── config_manager.py           # Менеджер конфигураций
├── dpi_bypass.py               # Обход DPI
├── split_tunnel.py             # Split-tunneling
├── domain_lists.py             # Загрузка списков
├── connection_monitor.py       # Автопереподключение
│
├── config/                     # Конфигурации
│   ├── client.json             # Настройки клиента
│   ├── config.json             # Конфигурация Xray
│   └── servers.json            # Список серверов
│
├── data/                       # Данные
│   ├── domain-lists.json       # Списки доменов
│   └── white_list.txt          # Белый список
│
├── logs/                       # Логи
│   ├── vpn.log                 # Логи клиента
│   ├── access.log              # Логи доступа
│   └── error.log               # Логи ошибок
│
└── scripts/                    # Скрипты
    ├── install.sh              # Установка
    └── update-lists.sh         # Обновление списков
```

---

## 🔧 Настройка

### Конфигурационные файлы

| Файл | Назначение |
|------|------------|
| `config/client.json` | Основные настройки |
| `config/config.json` | Конфигурация Xray |
| `data/domain-lists.json` | Списки доменов |

### Генерация UUID

```bash
# Через GUI
Кнопка "🎲 Сгенерировать UUID"

# Через консоль
xray uuid

# Через Python
python3 -c "from config_manager import ConfigManager; print(ConfigManager.generate_uuid())"
```

---

## 🛡️ Безопасность

- 🔐 TLS 1.3 шифрование
- 🔑 UUID генерация (secrets.uuid4)
- 🚫 Блокировка частных IP (опционально)
- 🚫 Блокировка BitTorrent (опционально)
- 🔒 Kill Switch (опционально)

---

## 📊 Мониторинг

### Статистика подключения

- Состояние подключения
- Время бесперебойной работы (uptime)
- Количество попыток переподключения
- Пройденные/неудачные health checks

### Трафик

- Скорость download/upload в реальном времени
- Общий объём трафика
- Progress bars активности

---

## ❓ Устранение проблем

### GUI не запускается

```bash
# Проверка PyQt5
python3 -c "import PyQt5"

# Переустановка
pip3 uninstall PyQt5
pip3 install PyQt5
```

### VPN не подключается

```bash
# Проверка логов
tail -f ~/vpn-client-aggregator/logs/error.log

# Проверка Xray
systemctl status xray

# Проверка конфигурации
python3 main.py console
> config show
```

### Xray не найден

```bash
# Установка
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"

# Проверка
xray version
```

---

## 🔗 Ссылки

- [Xray-core](https://github.com/XTLS/Xray-core)
- [V2Fly domain lists](https://github.com/v2fly/domain-list-community)
- [GeoIP](https://github.com/v2fly/geoip)
- [LoyalSoldier rules](https://github.com/Loyalsoldier/v2ray-rules-dat)

---

## 📝 Лицензия

MIT License — свободное использование и модификация.

---

**Версия:** 5.0  
**Дата:** 26.02.2026  
**Автор:** VPN Client Aggregator
