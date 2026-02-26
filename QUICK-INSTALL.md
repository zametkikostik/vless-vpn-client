# ⚡ БЫСТРАЯ УСТАНОВКА VPN CLIENT v4.0

## ✅ Выполнено:
- Symlink обновлён: `/usr/local/bin/vpn-gui`
- Старые папки удалены
- GitHub обновлён

---

## ❌ Ошибки которые нужно исправить:

### 1. Xray не установлен
```bash
sudo bash /home/kostik/vpn-client-aggregator/install-xray.sh
```

### 2. PyQt5 установлен неправильно
```bash
sudo apt install python3-pyqt5
```

---

## 🚀 ПОЛНАЯ УСТАНОВКА (одной командой):

```bash
sudo apt install python3-pyqt5 && sudo bash /home/kostik/vpn-client-aggregator/install-xray.sh
```

---

## ✅ Проверка:

```bash
# Проверка Xray
xray version

# Проверка PyQt5
python3 -c "import PyQt5; print('OK')"

# Запуск VPN GUI
vpn-gui
```

---

## 📱 После установки:

1. Откройте **VPN GUI** командой `vpn-gui`
2. Вкладка **Настройки**:
   - Сервер: IP вашего VPS
   - UUID: сгенерируйте через `xray uuid`
   - Порт: 443
   - SNI: google.com
3. Нажмите **Сохранить настройки**
4. Нажмите **Подключить**

---

## 🔗 GitHub:
https://github.com/zametkikostik/vless-vpn-client
