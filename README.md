# 🔒 VLESS VPN Client - AI Ready

VPN клиент с обходом DPI и блокировок. Поддержка AI-сервисов: Claude, ChatGPT, Lovable.

## 🚀 Возможности

- ✅ **AI-режим** - автоматическая настройка для Claude, ChatGPT, Lovable
- ✅ **Обход блокировок** — VLESS-Reality протокол
- ✅ **25+ AI серверов** — chatgpt.com, claude.com, lovable.dev
- ✅ **14 стран** — Германия, США, Нидерланды, Франция и др.
- ✅ **Автовыбор сервера** — подключение к лучшему по задержке
- ✅ **Разделение трафика** — РФ напрямую, остальное через VPN
- ✅ **GUI приложение** — удобный интерфейс
- ✅ **Веб-интерфейс** — управление из браузера
- ✅ **Автозапуск** — при загрузке системы
- ✅ **White/Black списки** — управление серверами

## 📦 Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/zametkikostik/vless-vpn-client.git
cd vless-vpn-client
```

### 2. Запустить установщик

```bash
chmod +x install-no-sudo.sh
./install-no-sudo.sh
```

### 3. Перезапустить терминал

```bash
source ~/.bashrc
```

## 🎯 Использование

### GUI Приложение (рекомендуется)

```bash
~/vpn-client-aggregator/start-vpn-gui.sh
```

**Для доступа к AI-сервисам:**
1. ✅ Убедитесь, что "🤖 AI-режим" включён (по умолчанию)
2. Нажмите "▶️ Подключить"
3. Откройте https://claude.com, https://chatgpt.com, https://lovable.dev

**Важно:** AI-режим автоматически использует FULL режим для доступа к AI-сервисам!

### Веб-интерфейс

Открыть в браузере: **http://localhost:5000**

Или через вкладку "Веб-доступ" в GUI приложении.

### Терминал

```bash
# Автовыбор лучшего сервера
vpn-ctrl auto

# Меню выбора локации
vpn-ctrl

# Проверка статуса
vpn-ctrl status
```

## 🌍 Доступные локации

- 🇩🇪 Germany (127 серверов)
- 🇳🇱 Netherlands (38 серверов)
- 🇺🇸 USA (14 серверов)
- 🇵🇱 Poland (13 серверов)
- 🇪🇪 Estonia (12 серверов)
- 🇱🇻 Latvia (5 серверов)
- 🇫🇷 France (4 серверов)
- 🇬🇧 UK (3 серверов)
- 🇰🇿 Kazakhstan (3 серверов)
- 🇱🇹 Lithuania (3 серверов)
- 🇧🇾 Belarus (2 серверов)
- 🇸🇪 Sweden (2 серверов)
- 🇫🇮 Finland (2 серверов)
- 🌍 Other (774 серверов)

## 🔧 Настройка прокси в браузере

### FoxyProxy (Firefox/Chrome)

1. Установить расширение [FoxyProxy](https://addons.mozilla.org/firefox/addon/foxyproxy-standard/)
2. Настройки:
   - Proxy Type: **SOCKS5**
   - Proxy IP: **127.0.0.1**
   - Port: **10808**
   - ✅ SOCKS Proxy?
   - ✅ DNS through proxy

### Системный прокси

```bash
export all_proxy=socks5://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10809
```

## 📁 Структура проекта

```
vless-vpn-client/
├── vpn-client-unified.py    # Основное приложение (GUI + Web)
├── vpn-controller.py        # Контроллер локаций
├── vpn-ctrl.sh             # Быстрый запуск
├── vless_client_v2.py      # VPN клиент v2.0
├── install.sh              # Установка с sudo
├── install-no-sudo.sh      # Установка без sudo
├── README.md               # Этот файл
└── INSTRUCTION.md          # Полная документация
```

## 🐛 Решение проблем

### VPN не подключается

```bash
# Обновить список серверов
vpn-ctrl
# 4 (Обновить список серверов)

# Перезапустить VPN
pkill -f "vless-vpn"
pkill -f "xray"
vpn-ctrl auto
```

### Проверить логи

```bash
tail -30 ~/vpn-client/logs/client.log
```

### Facebook не открывается

1. Проверить VPN: `vpn-ctrl status`
2. Настроить прокси в браузере (FoxyProxy)
3. Проверить: `curl --socks5 127.0.0.1:10808 https://www.facebook.com -I`

## 📊 Команды

| Команда | Описание |
|---------|----------|
| `python3 vpn-client-unified.py` | Запуск GUI приложения |
| `vpn-ctrl auto` | Автовыбор сервера |
| `vpn-ctrl` | Меню выбора локации |
| `vpn-ctrl status` | Проверка статуса |
| `pkill -f "vless-vpn"` | Остановить VPN |

## ⚠️ Важное

- **Это не новый протокол** — используется VLESS-Reality (XRay-core)
- **Нет 100% гарантии** — зависит от провайдера и региона
- **Используйте на свой страх и риск** — проверяйте законодательство вашей страны

## 📄 Лицензия

MIT License

## 🤝 Поддержка

Создавайте Issue в GitHub репозитории при возникновении проблем.

---

**Протокол:** VLESS-Reality  
**Порты:** SOCKS5 (10808), HTTP (10809)  
**Режим:** Split (РФ напрямую, остальное через VPN)
