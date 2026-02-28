# 🖥️ Запуск GUI программы VLESS VPN

## ❓ Проблема

При нажатии на иконку в меню приложений программа не открывается.

## ✅ Решение

### Способ 1: Запуск из терминала (рекомендуется)

```bash
# Быстрый запуск
/home/kostik/vless-vpn-client/run-gui.sh

# Или напрямую
python3 /home/kostik/vless-vpn-client/vpn_gui_ultimate.py gui
```

### Способ 2: Через меню приложений

**Меню → Интернет → VLESS VPN Ultimate**

Если не работает:

1. **Обновите кэш меню:**
```bash
update-desktop-database ~/.local/share/applications
```

2. **Перезайдите в систему** (logout/login)

3. **Проверьте ярлык:**
```bash
cat ~/.local/share/applications/vless-vpn-ultimate.desktop
```

Должно быть:
```ini
Exec=/home/kostik/vless-vpn-client/run-gui.sh
```

### Способ 3: Горячая клавиша

Создайте комбинацию клавиш для запуска:

1. **Система → Настройки → Клавиатура → Ярлыки**
2. **Добавить команду:**
   - Имя: `VLESS VPN`
   - Команда: `/home/kostik/vless-vpn-client/run-gui.sh`
3. **Назначьте клавиши**, например `Ctrl+Alt+V`

## 🛠️ Устранение проблем

### Проблема: Окно не появляется

**Проверьте:**
```bash
# Переменные окружения
echo $DISPLAY
echo $XDG_SESSION_TYPE

# Должно быть:
# DISPLAY=:0
# XDG_SESSION_TYPE=x11
```

**Решение:**
```bash
export DISPLAY=:0
/home/kostik/vless-vpn-client/run-gui.sh
```

### Проблема: "No Icon set"

Это предупреждение не критично. Программа работает, просто нет иконки в трее.

### Проблема: Несколько процессов

**Очистите:**
```bash
pkill -f "vpn_gui_ultimate.py"
sleep 2

# Запустите заново
/home/kostik/vless-vpn-client/run-gui.sh
```

### Проблема: VPN уже запущен

GUI обнаружит запущенный systemd сервис и покажет "🟢 ПОДКЛЮЧЕН".

**Проверьте:**
```bash
systemctl status vless-vpn-ultimate
```

## 📁 Файлы

| Файл | Назначение |
|------|-----------|
| `~/.local/share/applications/vless-vpn-ultimate.desktop` | Ярлык в меню |
| `/home/kostik/vless-vpn-client/run-gui.sh` | Скрипт запуска |
| `/home/kostik/vless-vpn-client/vpn_gui_ultimate.py` | GUI программа |

## 🚀 Быстрые команды

```bash
# Запустить GUI
/home/kostik/vless-vpn-client/run-gui.sh

# Остановить GUI
pkill -f "vpn_gui_ultimate.py"

# Проверить статус VPN
systemctl status vless-vpn-ultimate

# Перезапустить VPN
sudo systemctl restart vless-vpn-ultimate

# Логи
tail -f ~/vless-vpn-client/logs/client.log
```

## 💡 Советы

1. **Используйте терминал** для надежного запуска
2. **Проверяйте статус** перед подключением
3. **Останавливайте старые процессы** перед новым запуском
4. **GUI видит systemd сервис** и покажет "ПОДКЛЮЧЕН", если VPN работает

---

**© 2026 VPN Client Aggregator**
