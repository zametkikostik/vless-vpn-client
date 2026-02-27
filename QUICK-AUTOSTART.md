# ⚡ Быстрый автозапуск VLESS VPN

## 🚀 Самый простой способ (3 команды)

```bash
# 1. Создайте директорию
mkdir -p ~/.config/autostart

# 2. Создайте файл автозапуска
cat > ~/.config/autostart/vless-vpn.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=VLESS VPN
Exec=/home/kostik/vless-vpn-client/vless_client_ultimate.py start-auto
Icon=network-vpn
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# 3. Проверьте
ls -la ~/.config/autostart/vless-vpn.desktop
```

**Готово!** ✅

После перезагрузки VPN подключится автоматически.

---

## 📝 Проверка

### Перезагрузитесь:
```bash
sudo reboot
```

### После загрузки проверьте:
```bash
vless-vpn-ultimate status
```

**Должно показать:**
```
✅ Подключен
Всего серверов: 183
Онлайн: 183
```

---

## 🔧 Если нужно остановить

```bash
# Остановить VPN
vless-vpn-ultimate stop

# Удалить автозапуск
rm ~/.config/autostart/vless-vpn.desktop
```

---

## 📊 Другие способы

| Способ | Сложность | Для кого |
|--------|-----------|----------|
| **Desktop файл** | ⭐ Легко | Все пользователи |
| Systemd сервис | ⭐⭐ Средне | Серверы |
| Команда клиента | ⭐⭐ Средне | Продвинутые |

---

**Успехов! 🎉**
