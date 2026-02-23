# 🤖 Доступ к Claude.com, ChatGPT и Lovable.dev через VPN

## ✅ Готово! Теперь доступны AI-сервисы

### 📍 Новые локации

В VPN клиенте появилась категория **🤖 AI Services**, которая включает:
- **chatgpt.com** (14 серверов) - для доступа к ChatGPT
- **claude.com** (6 серверов) - для доступа к Claude
- **claude.ai** (2 сервера) - альтернативный домен Claude
- **lovable.dev** (5 серверов) - для доступа к Lovable AI

---

## 🚀 Как подключиться

### К ChatGPT:
1. Выберите **🤖 AI Services**
2. Подключитесь к серверу
3. Откройте https://chatgpt.com

### К Claude:
1. Выберите **🤖 AI Services**
2. Подключитесь к серверу
3. Откройте https://claude.com или https://claude.ai

### К Lovable.dev:
1. Выберите **🤖 AI Services**
2. Подключитесь к серверу
3. Откройте https://lovable.dev

### Способ 2: Через командную строку

```bash
# Запустить VPN с автовыбором лучшего AI-сервера
vless-vpn start --auto --mode split

# Настроить прокси
export all_proxy=socks5://127.0.0.1:10808
export http_proxy=http://127.0.0.1:10809
export https_proxy=http://127.0.0.1:10809

# Проверить доступ
curl --proxy socks5://127.0.0.1:10808 https://claude.com -I
```

---

## 🔄 Если серверы claude.com пропали

После обновления списка серверов (`vless-vpn update`) серверы claude.com могут удалиться.

**Быстрое восстановление:**
```bash
/home/kostik/vpn-client-aggregator/enable-claude.sh
```

Или вручную:
```bash
python3 ~/vpn-client-aggregator/add-claude-servers.py
```

---

## 📊 Доступные серверы AI

### Для Lovable.dev:
- **lovable.dev:443** - стандартный HTTPS
- **lovable.dev:8443** - альтернативный HTTPS порт
- **lovable.dev:2096** - альтернативный порт
- **lovable.dev:2082** - альтернативный порт
- **lovable.dev:80** - HTTP

### Для Claude.com:
- **claude.com:443** - стандартный HTTPS, лучшая совместимость
- **claude.com:8443** - альтернативный HTTPS порт

### Для ChatGPT.com:
- **chatgpt.com:443** - лучший пинг (~6 мс)
- **chatgpt.com:8443** - альтернатива

---

## ⚙️ Настройка браузера

### Proxy SwitchyOmega (рекомендуется)

1. Установите расширение для вашего браузера
2. Создайте профиль "VPN":
   - Protocol: **SOCKS5**
   - Server: **127.0.0.1**
   - Port: **10808**
3. Включите профиль перед посещением Claude/ChatGPT

### PAC-скрипт (автовыбор)

Для автоматического переключения создайте файл `~/vpn-client/proxy-auto.pac`:

```javascript
function FindProxyForURL(url, host) {
    if (shExpMatch(host, "*.claude.com") || 
        shExpMatch(host, "*.claude.ai") ||
        shExpMatch(host, "*.chatgpt.com")) {
        return "SOCKS5 127.0.0.1:10808";
    }
    return "DIRECT";
}
```

---

## 🐛 Troubleshooting

### Claude.com или Lovable.dev не открывается

1. **Проверьте VPN:**
   ```bash
   vless-vpn status
   ```

2. **Обновите серверы:**
   ```bash
   vless-vpn update
   ./enable-claude.sh
   ```

3. **Переключитесь на другой сервер:**
   - Для Claude: claude.com:8443 вместо claude.com:443
   - Для Lovable: lovable.dev:8443 вместо lovable.dev:443

### Серверы claude.com не отображаются

Запустите скрипт добавления:
```bash
python3 ~/vpn-client-aggregator/add-claude-servers.py
```

Затем обновите список в VPN клиенте (кнопка 🔄 Обновить).

---

## 📝 Команды для быстрой проверки

```bash
# Проверить доступ к Claude
curl --proxy socks5://127.0.0.1:10808 https://claude.com -I

# Проверить доступ к ChatGPT
curl --proxy socks5://127.0.0.1:10808 https://chatgpt.com -I

# Проверить доступ к Lovable
curl --proxy socks5://127.0.0.1:10808 https://lovable.dev -I

# Проверить IP (должен быть зарубежный)
curl --proxy socks5://127.0.0.1:10808 https://api.ipify.org
```

---

## 🔐 Безопасность

- VPN использует протокол **VLESS-Reality** с шифрованием
- Трафик к AI-сервисам идёт через зашифрованный туннель
- Локальные российские сайты работают напрямую (режим split)

---

## 📞 Поддержка

При проблемах с доступом:
1. Проверьте логи: `tail -100 ~/vpn-client/logs/client.log`
2. Обновите серверы: `vless-vpn update`
3. Добавьте claude.com: `./enable-claude.sh`
