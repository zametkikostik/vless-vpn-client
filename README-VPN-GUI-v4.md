# 🛡️ VLESS VPN Client v4.0 - Профессиональная версия

Единый клиент для Linux Mint с поддержкой VLESS-Reality, обходом DPI и раздельным туннелированием.

---

## 📋 Содержание

1. [Возможности](#возможности)
2. [Установка](#установка)
3. [Быстрый старт](#быстрый-старт)
4. [Настройка](#настройка)
5. [Команды](#команды)
6. [Android](#android)
7. [Структура папок](#структура-папок)

---

## 🚀 Возможности

### Основные
- ✅ **VLESS-Reality** — современный протокол с маскировкой под HTTPS
- ✅ **Обход DPI** — фрагментация пакетов, TLS 1.3
- ✅ **Split-tunneling** — раздельное туннелирование по доменам
- ✅ **Автозагрузка списков** — из GitHub (соцсети, видео, ИИ)
- ✅ **GUI интерфейс** — PyQt5 с системным треем
- ✅ **Мониторинг трафика** — скорость, объём, время подключения
- ✅ **Kill Switch** — блокировка при обрыве соединения
- ✅ **Автозапуск** — при входе в систему

### Списки доменов (автозагрузка)
| Категория | Через VPN | Напрямую |
|-----------|-----------|----------|
| Соцсети | Facebook, Instagram, Twitter, TikTok, Telegram | VK, OK |
| Видео | YouTube, Vimeo, Twitch | Rutube, Kinopoisk |
| ИИ-сервисы | ChatGPT, Claude, Gemini, Midjourney | YandexGPT |
| Заблокированные | Meduza, Reuters, Bloomberg | — |
| Российские | — | Яндекс, VK, Mail.ru, Госуслуги, Сбербанк |

---

## 📦 Установка

### 1. Установка зависимостей

```bash
# PyQt5 для GUI
pip3 install PyQt5

# Или через apt
sudo apt update
sudo apt install python3-pyqt5
```

### 2. Установка Xray-core

```bash
# Автоматическая установка
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"

# Проверка
xray version
```

### 3. Обновление symlink

```bash
# Запустите от root
sudo /home/kostik/vpn-client-aggregator/update-symlink.sh

# Или вручную
sudo ln -sf /home/kostik/vpn-client-aggregator/start-vpn-gui.sh /usr/local/bin/vpn-gui
sudo chmod +x /usr/local/bin/vpn-gui
```

---

## ⚡ Быстрый старт

### Запуск GUI

```bash
# Из любого места
vpn-gui

# Или напрямую
/home/kostik/vpn-client-aggregator/start-vpn-gui.sh
```

### Первое подключение

1. Откройте **VPN GUI**
2. Вкладка **Настройки**:
   - Введите IP сервера
   - Введите UUID клиента
   - Порт: 443
   - SNI: google.com
3. Нажмите **Сохранить настройки**
4. Вкладка **Управление** → **Подключить**

---

## ⚙️ Настройка

### Конфигурационные файлы

| Файл | Назначение |
|------|------------|
| `~/vpn-client-aggregator/config/gui-config.json` | Настройки GUI |
| `~/vpn-client-aggregator/config/config.json` | Конфигурация Xray |
| `~/vpn-client-aggregator/data/domain-lists.json` | Списки доменов |
| `~/vpn-client-aggregator/logs/vpn-gui.log` | Логи |

### Загрузка списков из GitHub

Списки автоматически загружаются из:
- **White list**: https://github.com/igareck/vpn-configs-for-russia
- **GeoIP/GeoSite**: https://github.com/v2fly

Автообновление: каждые 24 часа.

---

## 🎮 Команды

### GUI

```bash
vpn-gui              # Запуск интерфейса
```

### Консольное управление

```bash
# Через vpn-controller.py
python3 ~/vpn-client-aggregator/vpn-controller.py start
python3 ~/vpn-client-aggregator/vpn-controller.py stop
python3 ~/vpn-client-aggregator/vpn-controller.py status
python3 ~/vpn-client-aggregator/vpn-controller.py restart
```

### Xray напрямую

```bash
# Статус
systemctl status xray

# Логи
journalctl -u xray -f

# Перезапуск
sudo systemctl restart xray
```

---

## 📱 Android

### Рекомендуемые приложения

1. **v2rayNG** (Google Play / GitHub)
2. **Hiddify Next** (GitHub)

### Настройка v2rayNG

1. Установите приложение
2. Импортируйте конфигурацию:
   - Скопируйте VLESS ссылку с сервера
   - В v2rayNG: **+** → **Импортировать из буфера**
3. Включите **Split-tunneling**:
   - Настройки → Режим маршрутизации → Только указанные приложения
4. Подключитесь

### Конфигурация для Android

```json
{
  "v": "2",
  "ps": "VLESS-Reality-Russia",
  "add": "<IP_СЕРВЕРА>",
  "port": "443",
  "id": "<UUID>",
  "aid": "0",
  "scy": "auto",
  "net": "tcp",
  "type": "none",
  "security": "reality",
  "pbk": "<PUBLIC_KEY>",
  "fp": "chrome",
  "sni": "google.com",
  "sid": "<SHORT_ID>",
  "flow": "xtls-rprx-vision"
}
```

---

## 📁 Структура папок

```
vpn-client-aggregator/
├── vpn-gui.py              # Главный GUI клиент
├── start-vpn-gui.sh        # Скрипт запуска
├── vpn-controller.py       # Консольное управление
├── vless_client_*.py       # VLESS клиенты (разные версии)
├── vpn-web*.py             # Веб-интерфейсы
├── config/                 # Конфигурации
│   ├── gui-config.json     # Настройки GUI
│   └── config.json         # Конфигурация Xray
├── data/                   # Данные
│   ├── domain-lists.json   # Списки доменов
│   └── white_list.txt      # Белый список
├── logs/                   # Логи
│   ├── vpn-gui.log
│   ├── access.log
│   └── error.log
└── xray/                   # Xray файлы
```

---

## 🔧 Устранение проблем

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
```

### Списки не загружаются

```bash
# Вручную загрузить
wget -O ~/vpn-client-aggregator/data/white_list.txt \
  https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt
```

---

## 📝 Лицензия

MIT License — свободное использование и модификация.

---

## 🔗 Ссылки

- [Xray-core](https://github.com/XTLS/Xray-core)
- [V2Fly domain lists](https://github.com/v2fly/domain-list-community)
- [v2rayNG](https://github.com/2dust/v2rayNG)
- [Hiddify](https://github.com/hiddify/hiddify-next)

---

**Версия:** 4.0  
**Дата:** 26.02.2026  
**Автор:** VPN Client Aggregator
