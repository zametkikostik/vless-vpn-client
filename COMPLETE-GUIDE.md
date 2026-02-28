# 🥷 VLESS VPN - Полная маскировка и безопасность

## 📋 Режимы работы

| Режим | Маскировка | Скорость | Безопасность | Когда использовать |
|-------|-----------|---------|-------------|------------------|
| **Обычный** | ❌ Нет | ⚡⚡⚡ | ⭐⭐⭐ | Доверенная сеть |
| **DPI Bypass** | ⚠️ Частичная | ⚡⚡ | ⭐⭐⭐⭐ | Соцсети, почта |
| **Stealth** | 🎭 Полная | ⚡ | ⭐⭐⭐⭐⭐ |敏感тельное |
| **Safe (ГосУслуги)** | 🏛️ Под гос.сервис | ⚡ | ⭐⭐⭐⭐⭐ | Максимальная безопасность |

---

## 🚀 Быстрая активация

### Stealth Mode (полная маскировка):
```bash
/home/kostik/vless-vpn-client/activate-stealth-mode.sh
```

### Safe Mode (под ГосУслуги):
```bash
/home/kostik/vless-vpn-client/activate-safe-mode.sh
```

### Возврат в обычный режим:
```bash
sudo systemctl stop vless-stealth vless-safe
sudo systemctl start vless-vpn-ultimate
```

---

## 🏛️ Safe Mode - Маскировка под государственные сервисы

### Что делает:

**Маскировка трафика:**
- 🎭 User-Agent: ГосУслуги Mobile
- 🌐 TLS Fingerprint: Chrome 120
- 📡 DNS: Яндекс, Сбербанк, МТС
- 🔗 Маршрутизация: РФ сайты напрямую

**Конфигурация:**
```json
{
  "realitySettings": {
    "dest": "api.gosuslugi.ru:443",
    "serverNames": ["api.gosuslugi.ru"],
    "fingerprint": "chrome",
    "spiderX": "/api/v2/portal/oidc"
  },
  "dns": {
    "servers": [
      "https://dns.yandex.ru/dns-query",
      "https://common.dot.sber.ru/dns-query"
    ]
  }
}
```

### Когда использовать:

✅ **Рекомендуется:**
- Работа в офисе
- Публичные Wi-Fi
- Во время проверок
- Для легитимных задач

⚠️ **Не рекомендуется:**
- Для запрещенных ресурсов
- В сочетании с Tor
- Для торрентов

---

## 🎭 Stealth Mode - Ультимативная маскировка

### Что делает:

**Многоуровневая защита:**
1. Фрагментация пакетов (50-300 байт)
2. Padding (100-2000 байт шума)
3. Timing jitter (10-100 мс задержки)
4. Noise traffic (фейковые запросы)
5. Anti-detect система

**Ротация сервисов:**
```
Госуслуги → Сбербанк → Яндекс → VK → Mail.ru → Ростелеком
```

### Когда использовать:

✅ **Рекомендуется:**
-敏感тельное общение
- Обход сложных блокировок
- Исследовательская работа

⚠️ **Не рекомендуется:**
- Для повседневного использования
- Когда важна скорость

---

## 🛡️ Сравнение методов обнаружения

| Метод обнаружения | Обычный | DPI Bypass | Stealth | Safe |
|------------------|---------|------------|---------|------|
| DPI анализ | ❌ Палится | ⚠️ Частично | ✅ Скрыто | ✅ Скрыто |
| TLS fingerprint | ❌ VLESS | ⚠️ Смешанный | ✅ Chrome | ✅ Chrome |
| Поведенческий | ❌ VPN | ⚠️ Странный | ✅ Норма | ✅ ГосУслуги |
| Трафик анализ | ❌ Паттерн | ⚠️ Шум | ✅ Рандом | ✅ API |

---

## 📊 Практическое применение

### Сценарий 1: Офисная работа

```bash
# Утром активируем Safe Mode
activate-safe-mode.sh

# Работаем через весь день
# Трафик выглядит как доступ к госуслугам

# Вечером отключаем
sudo systemctl stop vless-safe
```

**Преимущества:**
- ✅ Выглядит как работа с госуслугами
- ✅DNS через российские серверы
- ✅ Минимальный риск

### Сценарий 2: Исследовательская работа

```bash
# Активируем Stealth Mode
activate-stealth-mode.sh

# Работаем с ротацией сервисов
# Каждые 5-10 минут смена маски

# После работы отключаем
sudo systemctl stop vless-stealth
```

**Преимущества:**
- ✅ Полная анонимность
- ✅ Ротация отпечатков
- ✅ Защита от анализа

### Сценарий 3: Экстренная ситуация

```bash
# КРАСНАЯ КНОПКА
pkill -f xray && pkill -f vless
sudo systemctl stop vless-vpn-ultimate vless-stealth vless-safe

# Очистка логов
> ~/vless-vpn-client/logs/*.log

# Переключение на прямой DNS
echo "nameserver 77.88.8.8" | sudo tee /etc/resolv.conf
```

---

## 🔍 Обнаружение и противодействие

### Сигнатуры для обнаружения:

**VPN трафик:**
```
❌ Регулярные паттерны
❌ Известные порты (443, 8443)
❌ VPN fingerprint
```

**Меры противодействия:**
```python
# Рандомизация
packet_size = random.randint(100, 1500)
time.sleep(random.uniform(0.01, 0.1))

# Шум
if random.random() < 0.1:
    send_dummy_request()

# Ротация
rotate_fingerprint()
```

---

## 📁 Файлы и скрипты

| Файл | Назначение | Команда |
|------|-----------|---------|
| `activate-stealth-mode.sh` | Stealth режим | `./activate-stealth-mode.sh` |
| `activate-safe-mode.sh` | Safe режим | `./activate-safe-mode.sh` |
| `vpn_stealth_mode.py` | Stealth модуль | `python3 vpn_stealth_mode.py` |
| `run-gui.sh` | Запуск GUI | `./run-gui.sh` |

---

## 🛑 Экстренные меры

### Полная остановка:

```bash
#!/bin/bash
# emergency-stop.sh

# Остановка сервисов
sudo systemctl stop vless-vpn-ultimate
sudo systemctl stop vless-stealth
sudo systemctl stop vless-safe

# Убийство процессов
pkill -f xray
pkill -f vless
pkill -f trojan

# Очистка логов
> ~/vless-vpn-client/logs/*.log
rm -f /tmp/*-config.json

# Прямой DNS
echo "nameserver 77.88.8.8" | sudo tee /etc/resolv.conf

echo "🛑 Emergency stop completed"
```

### Быстрое переключение:

```bash
# Safe → Обычный
sudo systemctl restart vless-vpn-ultimate

# Stealth → Safe
sudo systemctl stop vless-stealth
./activate-safe-mode.sh
```

---

## ⚖️ Юридическая информация

### Легально:

✅ Защита персональных данных
✅ Корпоративные VPN
✅ Исследования безопасности
✅ Журналистская деятельность

### Может быть проблематично:

⚠️ Обход блокировок запрещенных ресурсов
⚠️ Маскировка под государственные сервисы
⚠️ Нарушение авторских прав

### Рекомендации:

1. **Консультируйтесь с юристом**
2. **Документируйте цели**
3. **Не нарушайте законы**
4. **Имейте план Б**

---

## 📚 Документация

**Полные руководства:**
- `STEALTH-GUIDE.md` - Stealth режим
- `GOV-CHANNELS.md` - Государственные каналы
- `BACKUP-CHANNELS.md` - Резервные каналы
- `GUI-LAUNCH.md` - Запуск GUI

**Шпаргалки:**
- `STEALTH-CHEATSHEET.md` - Быстрая справка

---

**⚠️ Важно:** Используйте технологии ответственно и в рамках закона!

**© 2026 VPN Client Aggregator - Stealth Division**
