# 🥷 VLESS VPN - Полное руководство по маскировке

## 📋 Содержание

1. [Stealth Mode](#stealth-mode)
2. [Маскировка под российские сервисы](#маскировка-под-российские-сервисы)
3. [Обход DPI](#обход-dpi)
4. [Резервные каналы](#резервные-каналы)
5. [Экстренные меры](#экстренные-меры)

---

## 🚀 Быстрый старт

### Активация Stealth Mode:
```bash
/home/kostik/vless-vpn-client/activate-stealth-mode.sh
```

### Возврат в обычный режим:
```bash
sudo systemctl stop vless-stealth
sudo systemctl start vless-vpn-ultimate
```

---

## 🎭 Маскировка под российские сервисы

### Поддерживаемые сервисы:

| Сервис | Домены | User-Agent |
|--------|--------|------------|
| 🏛️ Госуслуги | gosuslugi.ru | Mozilla/5.0 ... Chrome/120 |
| 🏦 Сбербанк | sberbank.ru | Sberbank-Online/3.0 |
| 🔍 Яндекс | yandex.ru | YaBrowser/24.1.0 |
| 💬 VK | vk.com | VKApp/8.0.0 |
| 📧 Mail.ru | mail.ru | Mail.ru/2.0 |
| 📡 Ростелеком | rt.ru | Rostelecom/1.0 |

### Автоматическая ротация:

```python
# vpn_stealth_mode.py
mask = RussianServicesMask()
config = mask.get_current_config()

# Каждые 5-10 минут сервис автоматически меняется
# Маскировка: gosuslugi → sberbank → yandex → ...
```

### Пример ответа на DPI запрос:

```
DPI: "Кто подключился на порт 443?"

VPN отвечает:
  Host: api.gosuslugi.ru
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... VK/8.0
  Accept: text/html,application/xhtml+xml...
  Accept-Language: ru-RU,ru;q=0.9
  
  TLS Fingerprint: Chrome 120
  Cipher Suite: TLS_AES_256_GCM_SHA384
  ALPN: h2, http/1.1
```

---

## 🛡️ Обход DPI

### Уровни защиты:

#### Уровень 1: Фрагментация
```json
{
  "fragment": {
    "packets": "tlshello",
    "length": "50-300",
    "interval": "10-100"
  }
}
```

**Принцип работы:**
```
Обычный TLS handshake:
[XXXXXXXXXXXXXXXXXXXXXXXX]

Фрагментированный:
[XXX][XX][XXXXX][XXXX][XXXXXXXX]
```

#### Уровень 2: Padding
```python
# Добавление случайных данных
padding_length = random.randint(100, 2000)
padding_pattern = random.choice(["random", "zero", "space"])
```

#### Уровень 3: Timing Jitter
```python
# Случайные задержки между пакетами
jitter_ms = random.randint(10, 100)
time.sleep(jitter_ms / 1000)
```

#### Уровень 4: Noise Traffic
```python
# Фейковые HTTP запросы к легитимным сайтам
noise_requests = [
    "https://www.google.com",
    "https://www.yandex.ru",
    "https://www.cloudflare.com"
]
```

#### Уровень 5: Anti-Detect
```python
anti_detect = {
    "randomize_packet_order": True,
    "insert_dummy_packets": True,
    "variable_mss": True,
    "fake_retransmissions": True
}
```

---

## 😴 Спящий режим

### Триггеры активации:

| Триггер | Описание | Реакция |
|---------|----------|---------|
| `dpi_probe_detected` | Обнаружена проверка DPI | Пауза + легитимный трафик |
| `suspicious_activity` | Подозрительная активность | Переключение сервиса |
| `manual_trigger` | Ручной триггер | Немедленная пауза |

### Код активации:

```python
sleep_mode = SleepMode()

# Активация
sleep_mode.activate("dpi_probe_detected")

# Реакция:
# 1. Пауза всего VPN трафика
# 2. Переключение на легитимные домены
# 3. Отправка фейковых ответов

# Деактивация
sleep_mode.deactivate()
```

### Конфигурация легитимного режима:

```json
{
  "mode": "legitimate",
  "allowed_domains": [
    "gosuslugi.ru",
    "yandex.ru",
    "mail.ru",
    "vk.com",
    "sberbank-online.ru"
  ],
  "block_vpn_protocols": true,
  "log_all_connections": true
}
```

---

## 🔄 Резервные каналы

### Приоритеты каналов:

```
1️⃣ VLESS Reality (основной)
   ├─ Протокол: VLESS + Reality
   ├─ Порт: 443
   └─ Маскировка: TLS 1.3

2️⃣ Trojan-TLS (резерв)
   ├─ Протокол: Trojan
   ├─ Порт: 443
   └─ Маскировка: HTTPS

3️⃣ VMess-WS (WebSocket)
   ├─ Протокол: VMess
   ├─ Порт: 80/443
   └─ Маскировка: WebSocket

4️⃣ Shadowsocks-2022
   ├─ Протокол: Shadowsocks 2022
   ├─ Порт: 8388
   └─ Шифр: chacha20-ietf-poly1305

5️⃣ Hysteria2 (QUIC)
   ├─ Протокол: Hysteria2
   ├─ Порт: 443
   └─ Транспорт: QUIC/UDP
```

### Автоматический failover:

```python
backup = BackupChannels()

# При ошибке подключения
if connection_failed:
    next_channel = backup.failover()
    # Переключение на следующий канал
    # backup_tls → backup_ws → backup_shadowsocks → ...
```

---

## 🌐 Глобальный интернет

### DNS-over-HTTPS (DoH):

```json
{
  "dns": {
    "servers": [
      "https://dns.yandex.ru/dns-query",
      "https://common.dot.sber.ru/dns-query",
      "https://dns.mts.ru/dns-query"
    ]
  }
}
```

### Сегментация трафика:

```json
{
  "routing": {
    "rules": [
      {
        "domain": ["geosite:category-gov-ru"],
        "outboundTag": "direct"  // Госуслуги напрямую
      },
      {
        "domain": ["geosite:geolocation-ru"],
        "outboundTag": "proxy"   // РФ через VPN
      },
      {
        "domain": ["geosite:google"],
        "outboundTag": "stealth" // Google через stealth
      }
    ]
  }
}
```

### Domain Fronting:

```json
{
  "streamSettings": {
    "tcpSettings": {
      "header": {
        "type": "http",
        "request": {
          "headers": {
            "Host": "cdn.cloudflare.com"  // Фронт
          }
        }
      }
    }
  },
  "realitySettings": {
    "serverNames": ["actual-destination.com"]  // Реальный хост
  }
}
```

---

## 🛑 Экстренные меры

### Красная кнопка:

```bash
#!/bin/bash
# emergency-stop.sh

# Остановка всех сервисов
sudo systemctl stop vless-vpn-ultimate
sudo systemctl stop vless-stealth

# Убийство процессов
pkill -f xray
pkill -f v2ray
pkill -f trojan
pkill -f vless

# Очистка логов
> ~/vless-vpn-client/logs/client.log
> ~/vless-vpn-client/logs/xray_access.log
> ~/vless-vpn-client/logs/stealth.log

# Удаление конфигов
rm -f ~/vless-vpn-client/config/*.json

echo "🛑 Emergency stop completed"
```

### Быстрое переключение на прямой режим:

```bash
# Сохранить текущий конфиг
cp ~/vless-vpn-client/config/config.json ~/backup.json

# Создать прямой конфиг
cat > ~/vless-vpn-client/config/config.json << 'EOF'
{
  "inbounds": [{"port": 10808, "protocol": "socks"}],
  "outbounds": [{"protocol": "freedom"}]
}
EOF

# Перезапустить
sudo systemctl restart vless-vpn-ultimate
```

---

## 📊 Сравнение режимов

| Режим | Скорость | Надежность | Обнаруживаемость | Рекомендация |
|-------|---------|-----------|-----------------|--------------|
| **Прямой** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ Невозможно | Банки, госуслуги |
| **DPI Bypass** | ⚡⚡ | ⭐⭐⭐⭐ | ⚠️ Средняя | Соцсети, почта |
| **Stealth** | ⚡ | ⭐⭐⭐⭐⭐ | ✅ Минимальная |敏感тельное |
| **Tor** | 🐌 | ⭐⭐⭐ | ✅ Очень низкая | Анонимность |

---

## 🔧 Управление

### Переключение профилей:

```bash
# Stealth режим
/home/kostik/vless-vpn-client/activate-stealth-mode.sh

# Обычный режим
sudo systemctl start vless-vpn-ultimate

# Проверка статуса
systemctl status vless-vpn-ultimate
systemctl status vless-stealth
```

### Просмотр логов:

```bash
# Логи VPN
sudo journalctl -u vless-vpn-ultimate -f

# Логи маскировки
tail -f ~/vless-vpn-client/logs/stealth.log

# Логи XRay
tail -f ~/vless-vpn-client/logs/xray_access.log
```

### Тестирование маскировки:

```bash
# Проверка User-Agent
curl -s https://httpbin.org/headers | python3 -m json.tool

# Проверка IP
curl -s https://api.ipify.org?format=json

# Проверка DNS
nslookup google.com

# Проверка утечек
curl -s https://ipleak.net
```

---

## 📚 Файлы

| Файл | Описание |
|------|----------|
| `vpn_stealth_mode.py` | Stealth модуль |
| `activate-stealth-mode.sh` | Скрипт активации |
| `STEALTH-MODE.md` | Документация stealth |
| `BACKUP-CHANNELS.md` | Резервные каналы |
| `config/config.json` | Активная конфигурация |

---

## ⚠️ Важные предупреждения

1. **Не используйте** для незаконной деятельности
2. **Всегда имейте** план отступления
3. **Регулярно обновляйте** конфигурации
4. **Мониторьте** логи на предмет аномалий
5. **Тестируйте** перед важным использованием

---

**© 2026 VPN Client Aggregator - Stealth Division**

*Используйте технологии ответственно и в рамках закона.*
