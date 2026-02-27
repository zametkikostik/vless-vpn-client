# 🔧 VPN НЕ РАБОТАЕТ - Диагностика и решение

## ❗ Проблема

VPN подключен, но сайты не открываются через прокси.

---

## 🔍 Диагностика

### 1. Проверьте статус VPN

```bash
vless-vpn-ultimate status
```

**Должно показать:**
```
✅ Подключен
Всего серверов: 174
Онлайн: 174
```

### 2. Проверьте XRay

```bash
pgrep -af xray
```

**Должно показать:**
```
[PID] xray run -c config.json
```

**Если `<defunct>`** - XRay не работает!

### 3. Проверьте порты

```bash
ss -tlnp | grep 10808
```

**Должно показать:**
```
LISTEN  10808  users:(("xray",pid=XXX,fd=X))
```

### 4. Проверьте прокси

```bash
curl -x socks5h://127.0.0.1:10808 https://www.google.com
```

**Если ошибка** - прокси не работает!

---

## ✅ Решения

### Решение 1: Автоматическое исправление

```bash
cd /home/kostik/vless-vpn-client
python3 fix-vpn.py
```

Скрипт:
- ✅ Проверит серверы
- ✅ Выберет рабочий
- ✅ Пересоздаст конфиг
- ✅ Перезапустит XRay

### Решение 2: Обновить серверы

```bash
vless-vpn-ultimate update
```

После обновления:
```bash
vless-vpn-ultimate stop
vless-vpn-ultimate start
```

### Решение 3: Выбрать другой сервер (через GUI)

```bash
vless-vpn-gui gui
```

В GUI:
1. Нажмите "🔍 Скан серверов"
2. Выберите сервер с низким пингом
3. Нажмите "▶️ ПОДКЛЮЧИТЬ"

### Решение 4: Ручная перезапуск

```bash
# Остановить
pkill -f xray
vless-vpn-ultimate stop

# Подождать
sleep 5

# Запустить
vless-vpn-ultimate start
```

---

## 🔍 Почему VPN не работает?

### Причина 1: Сервер заблокирован
**Решение:** Обновите серверы и выберите другой

### Причина 2: XRay не запускается
**Решение:** Проверьте конфиг
```bash
python3 fix-vpn.py
```

### Причина 3: Неправильные параметры Reality
**Решение:** Используйте GUI для выбора сервера

### Причина 4: Брандмауэр блокирует
**Решение:** Проверьте брандмауэр
```bash
sudo ufw status
```

---

## 📊 Быстрая проверка

```bash
# 1. Интернет без VPN
curl https://www.google.com > /dev/null && echo "✅ Интернет есть"

# 2. XRay работает
pgrep -f xray && echo "✅ XRay работает"

# 3. Порт слушается
ss -tlnp | grep 10808 && echo "✅ Порт 10808 слушается"

# 4. Прокси работает
curl -x socks5h://127.0.0.1:10808 https://www.google.com > /dev/null && echo "✅ Прокси работает"
```

---

## 🎯 Настройка Firefox

### 1. Откройте настройки Firefox

### 2. Параметры сети
- Вниз до "Параметры сети"
- Нажмите "Настроить..."

### 3. Ручная настройка
- **SOCKS Сервер:** 127.0.0.1
- **Порт:** 10808
- **SOCKS v5:** ✅
- **DNS через SOCKS:** ✅

### 4. Проверьте
Откройте https://www.google.com

---

## 📞 Если ничего не помогает

### 1. Проверьте логи
```bash
tail -100 ~/vless-vpn-client/logs/client.log
```

### 2. Перезагрузите систему
```bash
sudo reboot
```

### 3. Обновите клиент
```bash
cd /home/kostik/vless-vpn-client
git pull
vless-vpn-ultimate update
```

---

## ⚡ Быстрое решение

```bash
cd /home/kostik/vless-vpn-client

# 1. Обновить серверы
vless-vpn-ultimate update

# 2. Запустить исправление
python3 fix-vpn.py

# 3. Проверить
curl -x socks5h://127.0.0.1:10808 https://www.google.com
```

---

**Успехов! 🚀**
