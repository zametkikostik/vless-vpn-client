# 🔥 STEALTH MODE - Полная маскировка VPN

## 📋 Возможности

### 1. Маскировка под российские сервисы

**Поддерживаемые сервисы:**
- 🏛️ **Госуслуги** (gosuslugi.ru)
- 🏦 **Сбербанк** (sberbank.ru)
- 🔍 **Яндекс** (yandex.ru)
- 💬 **VK** (vk.com)
- 📧 **Mail.ru** (mail.ru)
- 📡 **Ростелеком** (rt.ru)

**Как работает:**
```python
# Автоматическое переключение каждые 5-10 минут
Маскировка: gosuslugi → sberbank → yandex → ...
```

**TLS отпечатки:**
- User-Agent российских сервисов
- Заголовки как у российских сайтов
- TLS fingerprint (chrome, firefox, safari, ios)

### 2. Улучшенный обход DPI

**Уровни защиты:**

| Уровень | Технология | Описание |
|---------|-----------|----------|
| 1 | Фрагментация | Разбиение TLS handshake на части |
| 2 | Padding | Добавление случайных данных |
| 3 | Timing jitter | Случайные задержки между пакетами |
| 4 | Noise traffic | Фейковые HTTP запросы |
| 5 | Anti-detect | Рандомизация порядка пакетов |

**Настройки фрагментации:**
```json
{
  "fragment": {
    "packets": "tlshello",
    "length": "50-300",
    "interval": "10-100"
  }
}
```

### 3. Спящий режим

**Триггеры активации:**
- Обнаружение DPI probe
- Подозрительная активность
- Ручной триггер

**Реакция:**
```
😴 СПЯЩИЙ РЕЖИМ активирован
  ├─ Пауза VPN трафика
  ├─ Переключение на легитимный трафик
  └─ Отправка фейковых ответов
```

### 4. Резервные каналы

**Приоритеты:**
1. **VLESS Reality** (основной)
2. **Trojan-TLS** (резерв)
3. **VMess-WS** (WebSocket)
4. **Shadowsocks-2022**
5. **Hysteria2** (QUIC)

**Автоматический failover:**
```
[14:30:15] 🔄 Failover: backup_tls
[14:30:16] ✅ Подключение восстановлено
```

## 🚀 Запуск

### Быстрый старт:
```bash
python3 /home/kostik/vless-vpn-client/vpn_stealth_mode.py
```

### Интеграция с основным клиентом:

1. **Откройте** `vless_client_ultimate.py`

2. **Добавьте импорт** в начало:
```python
from vpn_stealth_mode import (
    RussianServicesMask,
    AdvancedDPIBypass,
    StealthXRayConfig
)
```

3. **Замените** генерацию конфигурации:
```python
# Было:
config = self.get_xray_config()

# Стало:
stealth = StealthXRayConfig()
config = stealth.generate_config(server)
```

## 📊 Сравнение режимов

| Режим | Обнаруживаемость | Скорость | Надежность |
|-------|-----------------|----------|------------|
| Обычный | ⚠️ Высокая | ⚡⚡⚡ | ⭐⭐⭐ |
| DPI Bypass | ⚠️ Средняя | ⚡⚡ | ⭐⭐⭐⭐ |
| **STEALTH** | ✅ Низкая | ⚡ | ⭐⭐⭐⭐⭐ |

## 🎯 Ответ на "ты кто?"

**При DPI запросе:**
```
DPI: "Кто подключился?"
VPN: "Здравствуйте, я Госуслуги!"
     ├─ User-Agent: Mozilla/5.0 ... VK/8.0
     ├─ Host: api.gosuslugi.ru
     ├─ TLS Fingerprint: Chrome 120
     └─ Заголовки: как у российского банка
```

## 🌐 Глобальный интернет через резервные системы

**Безопасные маршруты:**

### 1. Через DNS-over-HTTPS российских провайдеров:
```python
"dns": {
  "servers": [
    "https://dns.yandex.ru/dns-query",
    "https://common.dot.sber.ru/dns-query",
    "https://dns.mts.ru/dns-query"
  ]
}
```

### 2. Через доверенные домены:
```python
"routing": {
  "rules": [
    {
      "domain": ["geosite:category-gov-ru"],
      "outboundTag": "direct"  # Прямое подключение
    },
    {
      "domain": ["geosite:geolocation-ru"],
      "outboundTag": "proxy"   # Через VPN
    }
  ]
}
```

### 3. Сегментация трафика:
```
┌─────────────────────────────────┐
│   Трафик                        │
├─────────────────────────────────┤
│ Госуслуги, банки, госорганы → Прямой  │
│ Соцсети, почта → VPN (легитимный)    │
│ Запрещенные ресурсы → VPN (stealth)  │
└─────────────────────────────────┘
```

## ⚙️ Настройка конфигурации

### Файл: `~/.vless-vpn/stealth_config.json`

```json
{
  "stealth_mode": {
    "enabled": true,
    "service_rotation": true,
    "rotation_interval": 300,
    
    "masking": {
      "primary_service": "gosuslugi",
      "fallback_services": ["sberbank", "yandex", "vk"],
      "randomize_user_agent": true
    },
    
    "dpi_bypass": {
      "fragmentation": true,
      "fragment_length_min": 50,
      "fragment_length_max": 300,
      "padding": true,
      "timing_jitter": true,
      "noise_traffic": true
    },
    
    "sleep_mode": {
      "enabled": true,
      "triggers": ["dpi_probe", "manual"],
      "response": "pause_and_legit"
    },
    
    "backup_channels": {
      "enabled": true,
      "auto_failover": true,
      "max_failovers": 5
    }
  }
}
```

## 🔍 Обнаружение и реагирование

### Детектирование проверки:

```python
def detect_dpi_probe(self):
    # Мониторинг необычных паттернов
    indicators = [
        "multiple_tls_handshakes",
        "repeated_connection_attempts",
        "packet_inspection_signatures",
        "timing_analysis_patterns"
    ]
    
    if self.check_indicators(indicators):
        self.sleep_mode.activate("dpi_probe_detected")
```

### Реакция:

| Событие | Реакция |
|---------|---------|
| DPI probe | Пауза + легитимный трафик |
| Блокировка | Failover на резерв |
| Анализ трафика | Шум + рандомизация |
| Прямое подключение | Маскировка под сервис |

## 📈 Статистика и логи

**Просмотр логов:**
```bash
# Логи маскировки
tail -f ~/vless-vpn-client/logs/stealth.log

# Логи XRay
tail -f ~/vless-vpn-client/logs/xray_access.log

# Статистика
sudo journalctl -u vless-vpn-ultimate -f
```

**Пример лога:**
```
[14:30:15] 🎭 Маскировка: gosuslugi → sberbank
[14:30:16] 🛡️ DPI Bypass: fragmentation (50-300, 10-100)
[14:30:17] 😴 СПЯЩИЙ РЕЖИМ: dpi_probe_detected
[14:30:20] 😊 ВОЗОБНОВЛЕНИЕ работы
[14:30:21] ✅ VPN ПОДКЛЮЧЕН (stealth)
```

## 🛡️ Безопасность

### Рекомендации:

1. **Не используйте** для незаконной деятельности
2. **Регулярно обновляйте** списки сервисов
3. **Мониторьте** логи на предмет аномалий
4. **Тестируйте** перед важным использованием

### Проверка маскировки:

```bash
# Проверка User-Agent
curl -A "$(python3 -c 'from vpn_stealth_mode import RussianServicesMask; m=RussianServicesMask(); print(m.get_current_config()["user_agent"])')" https://httpbin.org/headers

# Проверка TLS fingerprint
python3 -c "from vpn_stealth_mode import StealthXRayConfig; c=StealthXRayConfig(); print(c.mask.get_current_config())"
```

## 📚 Файлы

| Файл | Назначение |
|------|-----------|
| `vpn_stealth_mode.py` | Stealth модуль |
| `vless_client_ultimate.py` | Основной клиент |
| `config/config.json` | Конфигурация XRay |
| `logs/stealth.log` | Логи маскировки |

## ⚠️ Важные замечания

1. **Stealth mode** снижает скорость, но повышает анонимность
2. **Ротация сервисов** может вызвать временные разрывы
3. **Резервные каналы** требуют дополнительных серверов
4. **Спящий режим** может ложно срабатывать

## 🆘 Troubleshooting

### Проблема: Не работает маскировка
```bash
# Проверьте конфигурацию
python3 vpn_stealth_mode.py

# Перезапустите с чистыми настройками
sudo systemctl restart vless-vpn-ultimate
```

### Проблема: Частые переключения
```python
# Увеличьте интервал в stealth_config.json
"rotation_interval": 600  # 10 минут вместо 5
```

### Проблема: Шум мешает работе
```python
# Отключите шум
"noise_traffic": false
```

---

**© 2026 VPN Client Aggregator - Stealth Division**
