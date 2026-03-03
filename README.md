# 🛡️ AntiCensor VPN Client (FreedomLink Linux)

**Современный VPN-клиент для Linux Mint с защитой от цензуры и DPI**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Особенности

- **🚀 31 источник конфигов** — автоматический парсинг из GitHub
- **🔒 Anti-DPI защита** — фрагментация, padding, uTLS
- **🌐 Smart Routing** — российские сайты напрямую, заблокированные — через VPN
- **🎨 Современный GUI** — PyQt6, тёмная тема
- **⚡ Xray-core** — поддержка VLESS/VMess/Trojan/Reality

## 🚀 Быстрый старт

### 🔹 Установка из GitHub (Рекомендуется)

```bash
# Скачать скрипт установки
wget https://raw.githubusercontent.com/zametkikostik/vless-vpn-client/main/scripts/install-from-github.sh

# Установить (требуется sudo)
sudo bash install-from-github.sh

# Запустить
anticensor-vpn
```

**Преимущества:**
- ✅ Автоматическая установка всех зависимостей
- ✅ Установка Xray-core
- ✅ Автообновление через GUI

### 🔹 Обновление из GitHub

```bash
# Через GUI
Открыть приложение → 🔄 Обновить приложение

# Или через терминал
sudo /opt/anticensor-vpn/scripts/update-from-github.sh
```

### 🔹 Ручная установка

```bash
# Скачать репозиторий
git clone https://github.com/zametkikostik/vless-vpn-client.git
cd vless-vpn-client

# Установить зависимости
pip3 install -r requirements.txt

# Установить Xray
sudo ./scripts/install-xray.sh

# Запустить
python3 main.py
```

### 🔹 Из .deb пакета

```bash
sudo dpkg -i releases/anticensor-vpn_1.0.0_amd64.deb
sudo apt-get install -f
anticensor-vpn
```

## 📋 Источники конфигураций

31 источник включая:
- sakha1370/OpenRay
- sevcator/5ubscrpt10n
- igareck/vpn-configs-for-russia
- AvenCores/goida-vpn-configs
- И многие другие...

## 🛠️ Технологии

- **GUI:** PyQt6
- **Ядро:** Xray-core
- **Язык:** Python 3.10+
- **Платформа:** Linux Mint / Ubuntu / Debian

## 📖 Документация

- [INSTALL.md](docs/INSTALL.md) — Инструкция по установке
- [ROUTING.md](docs/ROUTING.md) — Маршрутизация и GeoIP
- [ANTI-DPI.md](docs/ANTI-DPI.md) — Anti-DPI руководство

## 📝 Лицензия

MIT License
