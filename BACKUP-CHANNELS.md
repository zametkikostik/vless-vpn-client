# 🌐 Глобальный интернет через резервные системы

## ⚠️ Важное предупреждение

**Данная информация предоставлена в образовательных целях.**
Используйте только легальные методы обхода ограничений.

## 📚 Легальные методы доступа

### 1. Официальные зеркала международных сервисов

**Российские аналоги:**
- Google → Yandex
- Facebook → VK
- Twitter → Telegram
- Instagram → VK Clips

### 2. Лицензированные VPN-сервисы

**Разрешенные в РФ:**
- Kaspersky Secure Connection
- VPN от российских провайдеров
- Корпоративные VPN (для работы)

### 3. Tor (легально, но под наблюдением)

**Установка:**
```bash
sudo apt update
sudo apt install tor
```

**Использование:**
```bash
# Запуск
sudo systemctl start tor

# Через proxy
curl --socks5 127.0.0.1:9050 https://check.torproject.org
```

## 🔧 Технические методы (на ваш страх и риск)

### 1. DNS-over-HTTPS (DoH)

**Обход DNS-блокировок:**

```python
# Яндекс DoH
"https://dns.yandex.ru/dns-query"

# Сбер DoH  
"https://common.dot.sber.ru/dns-query"

# Cloudflare (может блокироваться)
"https://1.1.1.1/dns-query"
```

**Настройка в XRay:**
```json
{
  "dns": {
    "servers": [
      "https://dns.yandex.ru/dns-query",
      "https://common.dot.sber.ru/dns-query"
    ],
    "queryStrategy": "UseIPv4"
  }
}
```

### 2. Domain Fronting

**Принцип работы:**
```
Запрос: cdn.cloudflare.com
Реальный хост: blocked-site.com
```

**Пример конфигурации:**
```json
{
  "streamSettings": {
    "tcpSettings": {
      "header": {
        "type": "http",
        "request": {
          "headers": {
            "Host": "legitimate-cdn.com"
          }
        }
      }
    }
  }
}
```

### 3. Мосты (Bridges)

**Obfs4 мосты:**
```
obfs4 <IP>:<Port> <Fingerprint> cert=<Cert> iat-mode=<Mode>
```

**Настройка в XRay:**
```json
{
  "outbounds": [
    {
      "protocol": "freedom",
      "streamSettings": {
        "sockopt": {
          "dialerProxy": "obfs4-proxy"
        }
      }
    },
    {
      "tag": "obfs4-proxy",
      "protocol": "shadowsocks",
      "settings": {
        "servers": [
          {
            "address": "bridge.example.com",
            "port": 443,
            "password": "password",
            "method": "chacha20-ietf-poly1305"
          }
        ]
      }
    }
  ]
}
```

### 4. Плагины обфускации

**v2ray-plugin:**
```bash
# Установка
go install github.com/shadowsocks/v2ray-plugin@latest

# Запуск
v2ray-plugin --server --listen 0.0.0.0 --remote_addr remote.com --remote_port 443
```

**kcptun:**
```bash
# Ускорение через UDP
kcptun -l :4000 -r remote.com:443 --mode fast2
```

## 🌍 Источники серверов

### GitHub репозитории:
- `https://github.com/Leon406/SubCrawler`
- `https://github.com/mahdibland/V2RayAggregator`
- `https://github.com/Pawdroid/Free-servers`

### Telegram каналы:
- @v2ray_configs
- @v2rayng_config
- @Outline_VPN

### Поиск по Shodan:
```
port:443 "vless" OR "vmess" OR "trojan"
```

## 🛡️ Меры безопасности

### 1. Гигиена трафика

**Не смешивайте:**
- Личные данные + VPN
- Банкинг + анонимный трафик
- Соцсети +敏感тельные запросы

### 2. Разделение трафика

```json
{
  "routing": {
    "rules": [
      {
        "domain": ["gosuslugi.ru", "sberbank.ru"],
        "outboundTag": "direct"
      },
      {
        "domain": ["geosite:geolocation-ru"],
        "outboundTag": "proxy"
      },
      {
        "ip": ["geoip:private"],
        "outboundTag": "direct"
      }
    ]
  }
}
```

### 3. Временные профили

**Создавайте разные конфигурации:**
- `config-banking.json` - только банки (прямой)
- `config-social.json` - соцсети (легитимный VPN)
- `config-stealth.json` -敏感тельное (stealth mode)

## 📊 Сравнение методов

| Метод | Скорость | Надежность | Обнаруживаемость |
|-------|---------|-----------|-----------------|
| Прямой DNS | ⚡⚡⚡ | ⭐⭐ | ⚠️ Высокая |
| DoH | ⚡⚡⚡ | ⭐⭐⭐ | ⚠️ Средняя |
| Domain Fronting | ⚡⚡ | ⭐⭐ | ✅ Низкая |
| Obfs4 | ⚡ | ⭐⭐⭐ | ✅ Очень низкая |
| VLESS Reality | ⚡⚡ | ⭐⭐⭐⭐ | ✅ Минимальная |
| Stealth Mode | ⚡ | ⭐⭐⭐⭐⭐ | ✅ Практически нет |

## 🔍 Обнаружение и противодействие

### Сигнатуры для обнаружения:

**VPN трафик:**
- Регулярные паттерны пакетов
- Известные VPN порты
- TLS fingerprint VPN библиотек

**Меры противодействия:**
```python
# Рандомизация размера пакетов
packet_size = random.randint(100, 1500)

# Добавление шума
if random.random() < 0.1:
    send_dummy_packet()

# Случайные задержки
time.sleep(random.uniform(0.01, 0.1))
```

## 🚀 Быстрое переключение профилей

**Скрипт `switch-profile.sh`:**
```bash
#!/bin/bash

PROFILE=$1
CONFIG_DIR="$HOME/vless-vpn-client/config"

case $PROFILE in
  "banking")
    cp "$CONFIG_DIR/config-direct.json" "$CONFIG_DIR/config.json"
    ;;
  "social")
    cp "$CONFIG_DIR/config-legit.json" "$CONFIG_DIR/config.json"
    ;;
  "stealth")
    cp "$CONFIG_DIR/config-stealth.json" "$CONFIG_DIR/config.json"
    ;;
esac

sudo systemctl restart vless-vpn-ultimate
echo "✅ Переключено на: $PROFILE"
```

## 📈 Мониторинг качества

**Проверка подключения:**
```bash
# Пинг до сервера
ping -c 5 server.com

# Проверка скорости
curl -o /dev/null http://speedtest.net/file

# Проверка IP
curl https://api.ipify.org?format=json

# Проверка утечек DNS
nslookup google.com
```

## ⚖️ Юридические аспекты

### Что легально:
- ✅ Использование VPN для защиты данных
- ✅ Обход блокировок для работы
- ✅ Доступ к разрешенным ресурсам

### Что может быть проблематично:
- ⚠️ Обход блокировок запрещенных ресурсов
- ⚠️ Использование без лицензии VPN
- ⚠️ Нарушение авторских прав

### Рекомендации:
1. Используйте только для легальных целей
2. Не нарушайте законы вашей страны
3. Уважайте авторские права
4. Не распространяйте запрещенный контент

## 🆘 Экстренные меры

### При проверке:

1. **Отключите VPN немедленно:**
```bash
sudo systemctl stop vless-vpn-ultimate
pkill -f xray
```

2. **Очистите логи:**
```bash
> ~/vless-vpn-client/logs/client.log
> ~/vless-vpn-client/logs/xray_access.log
```

3. **Переключитесь на прямой режим:**
```bash
# Удалите конфигурацию VPN
rm ~/vless-vpn-client/config/config.json
```

### "Красная кнопка":
```bash
#!/bin/bash
# emergency-stop.sh
sudo systemctl stop vless-vpn-ultimate
sudo systemctl stop vless-stealth
pkill -f xray
pkill -f v2ray
pkill -f trojan
rm -f ~/vless-vpn-client/config/*.json
echo "🛑 Emergency stop completed"
```

## 📚 Дополнительные ресурсы

**Документация:**
- [XRay Official Docs](https://xtls.github.io/)
- [V2Ray Configuration](https://www.v2fly.org/)
- [Shadowsocks Guide](https://shadowsocks.org/)

**Инструменты:**
- [XRay Core](https://github.com/XTLS/Xray-core)
- [v2rayA](https://github.com/v2rayA/v2rayA)
- [Hiddify](https://github.com/hiddify/hiddify-next)

---

**⚠️ Помните:** Используйте технологии ответственно и в рамках закона!

**© 2026 VPN Client Aggregator - Educational Division**
