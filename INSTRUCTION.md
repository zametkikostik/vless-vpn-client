# VLESS VPN Client — Полная инструкция

## 🚀 Возможности

| Функция | Описание |
|---------|----------|
| 🔄 Автозапуск | VPN запускается автоматически при загрузке системы |
| ✂️ Разделение трафика | Российские сайты напрямую, иностранные через VPN |
| 🌐 Полный режим | Весь трафик через VPN |
| 🏓 Автовыбор сервера | Тестирование и переключение на лучший сервер |
| ⚙️ White/Black list | Управление списками серверов |

---

## 📋 Команды

### Запуск VPN

```bash
# Режим 1: Разделение трафика (РЕКОМЕНДУЕТСЯ)
# Российские сайты (.ru, Яндекс, VK и т.д.) — напрямую
# Иностранные (Facebook, Google, YouTube) — через VPN
vless-vpn start --auto --mode split

# Режим 2: Весь трафик через VPN
vless-vpn start --auto --mode full
```

### Остановка

```bash
# Найти и остановить процесс
pkill -f "vless-vpn"

# Или через команду (если процесс на переднем плане)
vless-vpn stop
```

### Статус

```bash
vless-vpn status
```

### Обновление серверов

```bash
vless-vpn update
```

---

## 🔧 Настройка прокси в системе

### Временная настройка (текущая сессия)

```bash
export all_proxy=socks5://127.0.0.1:10808
export http_proxy=http://127.0.0.1:10809
export https_proxy=http://127.0.0.1:10809
```

### Постоянная настройка (добавить в ~/.bashrc)

```bash
cat >> ~/.bashrc << 'EOF'

# VPN Proxy
alias vpn-on='export all_proxy=socks5://127.0.0.1:10808 http_proxy=http://127.0.0.1:10809 https_proxy=http://127.0.0.1:10809'
alias vpn-off='unset all_proxy http_proxy https_proxy'
EOF

source ~/.bashrc

# Использование:
vpn-on   # Включить прокси
vpn-off  # Выключить прокси
```

### Для браузера

Установите расширение **Proxy SwitchyOmega**:
- Chrome: https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif
- Firefox: https://addons.mozilla.org/firefox/addon/switchyomega/

Настройте профиль:
- Protocol: SOCKS5
- Server: 127.0.0.1
- Port: 10808

---

## ✅ Проверка работы

```bash
# Настроить прокси
export all_proxy=socks5://127.0.0.1:10808

# Проверить IP (должен быть зарубежный)
curl https://api.ipify.org

# Проверить Facebook
curl https://www.facebook.com -I

# Проверить YouTube
curl https://www.youtube.com -I

# Российские сайты (в режиме split должны работать напрямую)
curl https://www.yandex.ru -I
curl https://vk.com -I
```

---

## 📁 Файлы

| Файл | Описание |
|------|----------|
| `~/vpn-client/logs/client.log` | Лог клиента |
| `~/vpn-client/data/servers.json` | Кэш серверов |
| `~/vpn-client/data/whitelist.txt` | Белый список |
| `~/vpn-client/data/blacklist.txt` | Черный список |
| `~/.config/autostart/vpn-client.desktop` | Автозапуск |

---

## 🎯 Режимы работы

### Split mode (разделение)

```
┌─────────────────────────────────────┐
│  Ваш браузер                        │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ .ru     │    │ .com, .org   │
│ Яндекс  │    │ Facebook     │
│ VK      │    │ Google       │
│ Госуслуги│   │ YouTube      │
└────┬────┘    └──────┬───────┘
     │                │
     ▼                ▼
┌──────────┐   ┌─────────────┐
│ НАПРЯМУЮ │   │ через VPN   │
│ (быстро) │   │ (обход)     │
└──────────┘   └─────────────┘
```

**Преимущества:**
- Российские сайты работают быстро
- Меньше нагрузка на VPN
- Автоматическое определение

### Full mode (полный)

```
┌─────────────────────────────────────┐
│  Ваш браузер                        │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────┐
    │ ВСЁ через VPN  │
    └───────┬────────┘
            │
            ▼
    ┌──────────────┐
    │ Зарубежный   │
    │ сервер       │
    └──────────────┘
```

**Преимущества:**
- Полный обход блокировок
- Анонимность
- Единый IP для всех сайтов

---

## 🔧 Управление списками

### Добавить сервер в blacklist

```bash
# Если сервер заблокирован или не работает
vless-vpn add-black --host bad-server.com
```

### Добавить сервер в whitelist

```bash
# Если используете выборочное подключение
vless-vpn add-white --host good-server.com
```

### Просмотр списков

```bash
cat ~/vpn-client/data/whitelist.txt
cat ~/vpn-client/data/blacklist.txt
```

---

## 🐛 Troubleshooting

### VPN не запускается

```bash
# Проверить логи
tail -f ~/vpn-client/logs/client.log

# Проверить, работает ли XRay
ps aux | grep xray

# Перезапустить
pkill -f "vless-vpn"
vless-vpn start --auto --mode split
```

### Facebook не открывается

```bash
# 1. Проверить VPN
vless-vpn status

# 2. Проверить прокси
curl --proxy socks5://127.0.0.1:10808 https://www.facebook.com -I

# 3. Если ошибка — обновить серверы
vless-vpn update

# 4. Переключиться на другой сервер
pkill -f "vless-vpn"
vless-vpn start --auto --mode split
```

### Автозапуск не работает

```bash
# Проверить файл автозапуска
cat ~/.config/autostart/vpn-client.desktop

# Проверить логи автозапуска
cat ~/vpn-client/logs/autostart.log

# Пересоздать автозапуск
/home/kostik/vpn-client-aggregator/setup-autostart.sh
```

---

## 📊 Быстрые команды

```bash
# Запустить VPN (разделение)
vless-vpn start --auto --mode split &

# Запустить VPN (полный)
vless-vpn start --auto --mode full &

# Остановить
pkill -f "vless-vpn"

# Статус
vless-vpn status

# Логи в реальном времени
tail -f ~/vpn-client/logs/client.log

# Обновить серверы
vless-vpn update
```

---

## ⚠️ Важные заметки

1. **Режим split** рекомендуется для повседневного использования
2. **Режим full** используйте для доступа к заблокированным ресурсам
3. После перезагрузки VPN запускается автоматически (через 10 секунд)
4. Для работы прокси в браузере настройте Proxy SwitchyOmega или аналог

---

## 📞 Поддержка

Логи для диагностики:
```bash
tail -100 ~/vpn-client/logs/client.log
```
