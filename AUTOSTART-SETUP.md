# 🚀 Автозапуск VLESS VPN при старте системы

## ✅ 3 способа настроить автозапуск

---

## Способ 1: Systemd сервис (Рекомендуется для серверов) ⭐

### Установка:

```bash
# 1. Скопируйте сервис
sudo cp ~/vless-vpn-client/vless-vpn-ultimate.service /etc/systemd/system/

# 2. Обновите пользователя в сервисе (замените kostik на ваше имя)
sudo sed -i 's/%USER%/kostik/g' /etc/systemd/system/vless-vpn-ultimate.service

# 3. Перезагрузите systemd
sudo systemctl daemon-reload

# 4. Включите автозапуск
sudo systemctl enable vless-vpn-ultimate

# 5. Запустите сервис
sudo systemctl start vless-vpn-ultimate
```

### Управление:

```bash
# Проверить статус
sudo systemctl status vless-vpn-ultimate

# Посмотреть логи
sudo journalctl -u vless-vpn-ultimate -f

# Остановить
sudo systemctl stop vless-vpn-ultimate

# Выключить автозапуск
sudo systemctl disable vless-vpn-ultimate
```

---

## Способ 2: GUI автозапуск (Для desktop) 🖥️

### Установка:

```bash
# 1. Создайте директорию
mkdir -p ~/.config/autostart

# 2. Создайте desktop файл
cat > ~/.config/autostart/vless-vpn.desktop << EOF
[Desktop Entry]
Type=Application
Name=VLESS VPN Ultimate
Comment=Автоматический запуск VPN
Exec=$HOME/vless-vpn-client/vless_client_ultimate.py start-auto
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF

# 3. Сделайте исполняемым
chmod +x ~/.config/autostart/vless-vpn.desktop
```

### Проверка:

```bash
# Проверьте что файл создан
ls -la ~/.config/autostart/vless-vpn.desktop
```

---

## Способ 3: Через команду в клиенте 🔧

### Включить автозапуск:

```bash
vless-vpn-ultimate autostart-enable
```

### Выключить автозапуск:

```bash
vless-vpn-ultimate autostart-disable
```

---

## 📊 Проверка работы

### После перезагрузки:

```bash
# Проверить что VPN работает
vless-vpn-ultimate status

# Должно показать:
# ✅ Подключен
# Всего серверов: 183
# Онлайн: 183
```

### Если не работает:

```bash
# Проверить логи systemd
sudo journalctl -u vless-vpn-ultimate -n 50

# Проверить процесс xray
pgrep -f xray

# Проверить порт
ss -tlnp | grep 10808
```

---

## 🔧 Команды для управления

| Команда | Описание |
|---------|----------|
| `vless-vpn-ultimate start` | Запустить VPN |
| `vless-vpn-ultimate start-auto` | Автозапуск (для systemd) |
| `vless-vpn-ultimate stop` | Остановить VPN |
| `vless-vpn-ultimate status` | Проверить статус |
| `vless-vpn-ultimate autostart-enable` | Включить автозапуск |
| `vless-vpn-ultimate autostart-disable` | Выключить автозапуск |

---

## 🎯 Рекомендации

### Для сервера:
Используйте **Systemd сервис** (Способ 1)

### Для desktop (Linux Mint, Ubuntu):
Используйте **GUI автозапуск** (Способ 2)

### Для быстрой настройки:
Используйте **команду клиента** (Способ 3)

---

## ⚠️ Важно

1. **Перед автозапуском** убедитесь что VPN работает вручную:
   ```bash
   vless-vpn-ultimate start
   ```

2. **Обновите серверы** перед автозапуском:
   ```bash
   vless-vpn-ultimate update
   ```

3. **Проверьте логи** если что-то не работает:
   ```bash
   tail -f ~/vless-vpn-client/logs/client.log
   ```

---

## 🎉 Готово!

Теперь VPN будет запускаться автоматически при старте системы!

**Успехов! 🚀**
