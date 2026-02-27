# 🛡️ VPN Client Aggregator v5.0

[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)](https://github.com/zametkikostik/vless-vpn-client)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

Enterprise-grade VPN клиент с автоматической загрузкой серверов и обходом DPI.

## ✨ Возможности

- 🔄 **Автозагрузка серверов** из GitHub (1200+ серверов)
- 🎯 **Reality protocol** с автоматической настройкой
- 🚀 **Обход DPI** (фрагментация пакетов)
- 🔀 **Split-tunneling** (умная маршрутизация)
- 🖥️ **GUI интерфейс** (PyQt5)
- ⌨️ **CLI интерфейс** (терминал)
- 📊 **Мониторинг подключения** (автопереподключение)

## 🚀 Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/zametkikostik/vless-vpn-client.git
cd vless-vpn-client

# Установить зависимости
pip3 install -r requirements.txt

# Запустить установку
./install.sh
```

### Запуск GUI

```bash
# Через скрипт
./run-gui.sh

# Или напрямую
python3 vpn_gui.py
```

### Запуск CLI

```bash
# Подключиться (автовыбор сервера)
python3 vless_client.py start --auto

# Обновить серверы
python3 vless_client.py update

# Статус
python3 vless_client.py status
```

## 📋 Режимы работы

| Режим | Описание |
|-------|----------|
| **Split-умный (белый список)** | Только заблокированные сайты через VPN |
| **Split-tunneling** | Заблокированные + зарубежные через VPN |
| **Все через VPN** | Весь трафик через VPN |
| **Прямое подключение** | Без VPN |

## ⚙️ Настройка прокси

### В браузере (FoxyProxy/SwitchyOmega)

- **Тип:** SOCKS5
- **Host:** 127.0.0.1
- **Port:** 10808

### В терминале

```bash
export all_proxy=socks5://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10809
```

## 🔧 Автозапуск

### Через systemd

```bash
# Установить сервис
sudo cp vpn-client.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vpn-client
sudo systemctl start vpn-client
```

### Через автозагрузку

```bash
# Добавить в автозагрузку
./setup-autostart.sh
```

## 📁 Структура проекта

```
vless-vpn-client/
├── vpn_gui.py              # GUI приложение
├── vless_client.py         # CLI приложение
├── vpn_controller.py       # Контроллер
├── vpn_engine.py           # VPN двигатель
├── config_manager.py       # Управление конфигами
├── connection_monitor.py   # Мониторинг подключения
├── dpi_bypass.py           # Обход DPI
├── split_tunnel.py         # Split-tunneling
├── domain_lists.py         # Списки доменов
├── requirements.txt        # Зависимости
├── install.sh              # Скрипт установки
├── run-gui.sh              # Запуск GUI
└── vpn-client.service      # Systemd сервис
```

## 🧪 Тестирование

```bash
# Тест подключения
python3 test-connect.py

# Тест GUI
python3 test-button.py
```

## 🔒 Безопасность

- ✅ UUID не сохраняются в логах
- ✅ Поддержка Reality protocol
- ✅ Шифрование TLS
- ✅ Проверка здоровья серверов

## 🛠️ Требования

- Python 3.8+
- PyQt5 (для GUI)
- Xray-core (устанавливается автоматически)
- Linux Mint/Ubuntu (другие дистрибутивы могут требовать настройки)

## 📞 Команды CLI

| Команда | Описание |
|---------|----------|
| `start --auto` | Подключиться (автовыбор) |
| `stop` | Отключиться |
| `status` | Проверить статус |
| `update` | Обновить серверы |
| `restart` | Перезапустить |

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте на GitHub (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## ⚠️ Отказ от ответственности

Используйте на свой страх и риск. Автор не несёт ответственности за возможные последствия использования данного ПО.

## 🔗 Ссылки

- [GitHub Repository](https://github.com/zametkikostik/vless-vpn-client)
- [Xray-core Documentation](https://xtls.github.io/)
- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

---

**VPN Client Aggregator** — свободный доступ к информации без границ 🌍
