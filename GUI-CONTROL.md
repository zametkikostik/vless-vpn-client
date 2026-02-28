# 🖥️ Управление VPN через GUI программу

## ✅ Исправление внесено

Теперь GUI программа **интегрирована с systemd сервисом**:

### Как это работает:

1. **При нажатии "ПОДКЛЮЧИТЬ"**:
   - GUI проверяет, работает ли systemd сервис
   - Если сервис работает → показывает "✅ ПОДКЛЮЧЕН"
   - Если сервис остановлен → запускает через worker

2. **При нажатии "ОТКЛЮЧИТЬ"**:
   - GUI останавливает systemd сервис через `sudo systemctl stop`
   - Показывает статус "⚪ НЕ ПОДКЛЮЧЕН"

## 📋 Настройки

### 1. Правило sudo (уже настроено!)
Файл: `/etc/sudoers.d/vless-vpn`

```bash
# Разрешает управление сервисом без пароля
kostik ALL=(ALL) NOPASSWD: /bin/systemctl stop vless-vpn-ultimate, \
                           /bin/systemctl start vless-vpn-ultimate, \
                           /bin/systemctl restart vless-vpn-ultimate, \
                           /bin/systemctl status vless-vpn-ultimate
```

### 2. Запуск GUI

**Вариант A: Из меню приложений**
```
Меню → Интернет → VLESS VPN Ultimate
```

**Вариант B: Из терминала**
```bash
python3 /home/kostik/vless-vpn-client/vpn_gui_ultimate.py gui
```

**Вариант C: Автозапуск при входе**
Файл: `~/.config/autostart/vless-vpn-ultimate.desktop`

## 🔄 Сценарии использования

### Сценарий 1: VPN работает через systemd (автозапуск)
```
1. Система загрузилась → systemd запустил VPN
2. Вы открыли GUI → видит "✅ ПОДКЛЮЧЕН"
3. Нажали "ОТКЛЮЧИТЬ" → сервис остановлен
4. Нажали "ПОДКЛЮЧИТЬ" → сервис запущен
```

### Сценарий 2: Ручное управление через GUI
```
1. Остановите сервис: sudo systemctl stop vless-vpn-ultimate
2. Откройте GUI
3. Нажмите "ПОДКЛЮЧИТЬ" → запустится worker
```

## 🛠️ Команды управления

### Через терминал:
```bash
# Статус
systemctl status vless-vpn-ultimate

# Запустить
sudo systemctl start vless-vpn-ultimate

# Остановить
sudo systemctl stop vless-vpn-ultimate

# Перезапустить
sudo systemctl restart vless-vpn-ultimate

# Логи
sudo journalctl -u vless-vpn-ultimate -f
```

### Через GUI:
```
▶️ ПОДКЛЮЧИТЬ  → Подключение
⏹️ ОТКЛЮЧИТЬ   → Отключение
```

## 📊 Статусы в GUI

| Статус | Значение |
|--------|----------|
| 🟢 ПОДКЛЮЧЕН | VPN активен, трафик идет через VPN |
| ⚪ НЕ ПОДКЛЮЧЕН | VPN отключен, прямой интернет |
| 🛡️ DPI Bypass: АКТИВЕН | Обход DPI работает |
| 🛡️ DPI Bypass: ГОТОВ | Обход DPI готов к работе |

## ⚠️ Важно!

**Не запускайте несколько экземпляров одновременно!**

Если VPN уже работает через systemd, GUI это обнаружит и покажет статус подключения. Не нужно нажимать "ПОДКЛЮЧИТЬ" повторно.

## 🐛 Устранение проблем

### GUI не видит запущенный сервис
```bash
# Проверьте статус
systemctl status vless-vpn-ultimate

# Перезапустите GUI
pkill -f vpn_gui_ultimate.py
python3 /home/kostik/vless-vpn-client/vpn_gui_ultimate.py gui
```

### Сервис не останавливается через GUI
```bash
# Проверьте правило sudo
sudo -l | grep vless-vpn

# Остановите вручную
sudo systemctl stop vless-vpn-ultimate
```

### Конфликт процессов
```bash
# Остановить всё
sudo systemctl stop vless-vpn-ultimate
pkill -f vpn_gui_ultimate.py
pkill -f xray

# Запустить через systemd
sudo systemctl start vless-vpn-ultimate
```

## 📁 Файлы

| Файл | Описание |
|------|----------|
| `/home/kostik/vless-vpn-client/vpn_gui_ultimate.py` | GUI программа |
| `/etc/systemd/system/vless-vpn-ultimate.service` | Systemd сервис |
| `/etc/sudoers.d/vless-vpn` | Правило sudo для управления |
| `~/.config/autostart/vless-vpn-ultimate.desktop` | Автозапуск GUI |
| `/home/kostik/vless-vpn-client/logs/client.log` | Основной лог |
