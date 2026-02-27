# 🔥 Firefox + VLESS VPN - Настройка прокси

## ⚠️ Проблема
YouTube и другие зарубежные сайты не открываются потому что:
1. VPN сервер не работает
2. Firefox не настроен на прокси

---

## ✅ Решение

### 1. Проверьте что VPN работает

```bash
# Проверьте статус
vless-vpn-ultimate status

# Должно показать:
# ✅ Подключен
# Всего серверов: 174
# Онлайн: 174
```

**Если НЕ подключен:**
```bash
# Обновите серверы
vless-vpn-ultimate update

# Переподключитесь
vless-vpn-ultimate stop
vless-vpn-ultimate start
```

### 2. Настройте Firefox

#### Вариант A: Ручная настройка

1. Откройте **Настройки** Firefox
2. Прокрутите вниз до **Параметры сети**
3. Нажмите **Настроить...**
4. Выберите **Ручная настройка прокси**
5. Заполните:
   ```
   SOCKS Сервер: 127.0.0.1
   Порт: 10808
   ```
6. ✅ Выберите **SOCKS v5**
7. ✅ **DNS через SOCKS** (важно!)
8. Нажмите **OK**

#### Вариант B: Автомическая настройка

```bash
# Создайте файл настроек
cat > /tmp/proxy_ff.txt << 'EOF'
user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "127.0.0.1");
user_pref("network.proxy.socks_port", 10808);
user_pref("network.proxy.socks_version", 5);
user_pref("network.proxy.socks_remote_dns", true);
EOF

# Примените (Firefox должен быть закрыт)
pkill firefox
cp /tmp/proxy_ff.txt ~/.mozilla/firefox/*.default-release/
```

### 3. Проверьте работу

Откройте в Firefox:
- https://www.google.com ✅
- https://www.youtube.com ✅
- https://claude.com ✅
- https://chatgpt.com ✅

---

## 🔧 Если не работает

### Проверьте прокси:

```bash
# Тест прокси
curl -x socks5h://127.0.0.1:10808 https://www.google.com

# Если ошибка - VPN не работает
```

### Перезапустите VPN:

```bash
# Остановить
vless-vpn-ultimate stop

# Подождать 3 секунды
sleep 3

# Запустить
vless-vpn-ultimate start
```

### Обновите серверы:

```bash
vless-vpn-ultimate update
```

### Выберите другой сервер:

В GUI нажмите:
1. Вкладка "Подключение"
2. Выберите другую локацию
3. Нажмите "Подключить"

---

## 🎯 Быстрая проверка

```bash
# Без прокси (должно работать)
curl https://www.google.com > /dev/null && echo "✅ Интернет есть"

# С прокси (должно работать если VPN подключен)
curl -x socks5h://127.0.0.1:10808 https://www.google.com > /dev/null && echo "✅ VPN работает"
```

---

## 📊 Статус VPN

```bash
vless-vpn-ultimate status
```

**Должно показать:**
```
✅ Подключен
Всего серверов: 174
Онлайн: 174
Прокси:
  SOCKS5: 127.0.0.1:10808
  HTTP: 127.0.0.1:10809
```

---

## ⚠️ Важно!

1. **DNS через SOCKS** - обязательно включите в настройках Firefox!
2. **SOCKS v5** - выберите версию 5
3. **VPN должен быть подключен** перед настройкой Firefox

---

**Успехов! 🚀**
