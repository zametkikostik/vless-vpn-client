# 🔧 Настройка автозапуска VPN

## Проблема
VPN не запускался при включении, потому что:
1. В `.desktop` файле был указан запуск GUI (`vpn_gui_ultimate.py`), который требует графической среды
2. GUI не может запуститься до входа пользователя в систему
3. Было несколько дублирующихся процессов VPN

## ✅ Решение 1: Автозапуск через ~/.config/autostart (для GUI)

**Уже настроено!** Файл: `~/.config/autostart/vless-vpn-ultimate.desktop`

Используется wrapper-скрипт `start-vpn-gui.sh`, который:
- Ждет 15 секунд для загрузки DE
- Экспортирует DISPLAY для GUI
- Проверяет, не запущен ли уже VPN
- Запускает GUI-версию

**Проверка:**
```bash
cat ~/.config/autostart/vless-vpn-ultimate.desktop
```

## ✅ Решение 2: Systemd сервис (для фонового запуска)

**Требует sudo!** Запустите команду:

```bash
# Установить сервис
sudo cp /home/kostik/vless-vpn-client/vless-vpn-ultimate.service /tmp/vless-vpn-ultimate.service
sudo sed -i "s/%USER%/kostik/g" /tmp/vless-vpn-ultimate.service
sudo mv /tmp/vless-vpn-ultimate.service /etc/systemd/system/vless-vpn-ultimate.service
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable vless-vpn-ultimate

# Запустить сейчас
sudo systemctl start vless-vpn-ultimate

# Проверить статус
sudo systemctl status vless-vpn-ultimate
```

**Управление сервисом:**
```bash
# Запустить
sudo systemctl start vless-vpn-ultimate

# Остановить
sudo systemctl stop vless-vpn-ultimate

# Включить автозапуск
sudo systemctl enable vless-vpn-ultimate

# Выключить автозапуск
sudo systemctl disable vless-vpn-ultimate

# Посмотреть логи
sudo journalctl -u vless-vpn-ultimate -f
```

## 📋 Проверка автозапуска

1. **Перезагрузите систему:**
   ```bash
   sudo reboot
   ```

2. **После загрузки проверьте:**
   ```bash
   # Проверка процесса
   ps aux | grep vpn_gui_ultimate
   
   # Проверка логов
   tail -30 /home/kostik/vless-vpn-client/logs/autostart.log
   tail -30 /home/kostik/vless-vpn-client/logs/client.log
   ```

## 🛠️ Устранение проблем

### Остановить все VPN процессы:
```bash
pkill -f "vpn_gui_ultimate.py"
pkill -f "vless_client_ultimate.py"
pkill -f "xray run"
```

### Проверить логи:
```bash
tail -50 /home/kostik/vless-vpn-client/logs/client.log
```

### Тестовый запуск:
```bash
cd /home/kostik/vless-vpn-client
./start-vpn-gui.sh
```

## 📝 Файлы

| Файл | Описание |
|------|----------|
| `~/.config/autostart/vless-vpn-ultimate.desktop` | Автозапуск GUI |
| `/home/kostik/vless-vpn-client/start-vpn-gui.sh` | Wrapper-скрипт |
| `/etc/systemd/system/vless-vpn-ultimate.service` | Systemd сервис |
| `/etc/sudoers.d/vless-vpn` | Правило sudo для GUI |
| `/home/kostik/vless-vpn-client/vpn_gui_ultimate.py` | GUI программа (обновлена!) |
| `/home/kostik/vless-vpn-client/logs/client.log` | Основной лог |
| `/home/kostik/vless-vpn-client/logs/autostart.log` | Лог автозапуска |

## 📚 Дополнительная документация

- `GUI-CONTROL.md` - Управление через GUI программу
- `AUTOSTART-SETUP.md` - Полная настройка автозапуска
- `QUICK-AUTOSTART.md` - Быстрая настройка
