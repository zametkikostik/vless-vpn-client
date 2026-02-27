# 🛡️ VLESS VPN Client - Production

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/zametkikostik/vless-vpn-client)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Flutter](https://img.shields.io/badge/flutter-3.19+-blue.svg)](https://flutter.dev)
[![Android](https://img.shields.io/badge/android-21+-green.svg)](https://android.com)
[![CI/CD](https://github.com/zametkikostik/vless-vpn-client/actions/workflows/android-build.yml/badge.svg)](https://github.com/zametkikostik/vless-vpn-client/actions)

Enterprise-grade VPN client для протокола **VLESS с Reality-обфускацией**. Обход DPI и блокировок.

---

## 📱 Мобильное приложение (Android)

### 🚀 Быстрая установка

1. Перейдите в **[Releases](https://github.com/zametkikostik/vless-vpn-client/releases)**
2. Скачайте последнюю версию `app-release.apk`
3. Установите на Android устройство

### 🔧 Сборка из исходников

```bash
cd mobile-client

# Установка зависимостей
flutter pub get

# Debug сборка
flutter build apk --debug

# Release сборка
flutter build apk --release
```

**Полная инструкция:** [ANDROID-BUILD.md](ANDROID-BUILD.md)

---

## 💻 Desktop клиент

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/zametkikostik/vless-vpn-client.git
cd vless-vpn-client

# Установка зависимостей
pip3 install -r requirements.txt

# Установка клиента
ln -sf $(pwd)/vless_client.py ~/.local/bin/vless-vpn
chmod +x ~/.local/bin/vless-vpn
```

### Использование

```bash
# Подключение (автовыбор сервера)
vless-vpn start --auto

# Проверка статуса
vless-vpn status

# Обновление списка серверов
vless-vpn update

# Отключение
vless-vpn stop

# Запуск GUI
vpn-gui
```

---

## 🌐 Сканирование серверов

Автоматическое сканирование рабочих серверов из открытых источников:

```bash
cd vless-vpn-client
python3 server_scanner.py
```

**Источники:**
- GitHub репозитории с конфигами
- VLESS агрегаторы
- Публичные subscription URL
- Pastebin
- Telegram каналы

**Результат:**
- Найденные серверы → `vpn-client-aggregator/data/servers.json`
- Рабочие серверы → `vpn-client-aggregator/data/working_servers.json`

---

## 📁 Структура проекта

```
vless-vpn-client/
├── mobile-client/              # Flutter Android приложение
│   ├── lib/
│   │   ├── main.dart          # Точка входа
│   │   ├── models/            # Модели данных
│   │   ├── providers/         # State management
│   │   ├── screens/           # UI экраны
│   │   ├── widgets/           # Переиспользуемые виджеты
│   │   └── services/          # Сервисы
│   ├── android/               # Android конфигурация
│   └── pubspec.yaml
│
├── vless_client.py            # Основной Python клиент
├── vless_client_saas.py       # SaaS версия
├── vless_client_stable.py     # Стабильная версия
├── vpn-gui.py                 # GUI интерфейс (PyQt5)
├── server_scanner.py          # Сканер серверов
│
├── vpn-client-aggregator/     # Данные клиента
│   ├── data/
│   │   ├── servers.json       # Список серверов
│   │   └── working_servers.json
│   ├── config/
│   └── logs/
│
├── .github/workflows/
│   ├── android-build.yml      # CI/CD для Android
│   └── ci-cd.yml              # Python CI/CD
│
└── README.md                  # Эта документация
```

---

## 🔧 Конфигурация

### Директория данных

```
~/vpn-client/
├── data/
│   └── servers.json      # Кэш списка серверов
├── config/
│   └── config.json       # Конфигурация XRay
├── logs/
│   └── client.log        # Логи приложения
└── bin/
    └── xray              # Бинарный файл XRay
```

### Алгоритм выбора сервера

1. **Приоритет 1**: Low latency серверы (<100ms) с Reality протоколом
2. **Приоритет 2**: WHITE list серверы с Reality протоколом
3. **Приоритет 3**: Любые серверы с Reality протоколом и UUID

Клиент проверяет топ-5 серверов на TCP доступность и выбирает первый доступный.

---

## 📲 Android приложение

### Функции

- ✅ **Автоматическое подключение** к лучшему серверу
- ✅ **Список серверов** с проверкой пинга
- ✅ **Split-tunneling** (выбор приложений для VPN)
- ✅ **Мониторинг соединения**
- ✅ **Тёмная тема** (Material Design 3)
- ✅ **Автозапуск** после перезагрузки

### Скриншоты

| Главная | Серверы | Статус |
|---------|---------|--------|
| 🟢 Кнопка подключения | 📋 Список серверов | ⏱️ Длительность сессии |

### Настройка (Android)

1. Откройте приложение
2. Нажмите **"Загрузить серверы"**
3. Выберите сервер из списка
4. Нажмите **"ПОДКЛЮЧИТЬ"**

**Split-tunneling:**
- Настройки → Выбор приложений
- Отметьте приложения для VPN (Instagram, Telegram, YouTube)
- Российские приложения оставьте без VPN (VK, Сбербанк, Госуслуги)

---

## 🔐 Протокол VLESS + Reality

### Преимущества

| Функция | Описание |
|---------|----------|
| **Reality** | Продвинутая обфускация трафика |
| **VLESS** | Высокая производительность |
| **DPI Bypass** | Обход фильтрации провайдеров |
| **Auto-reconnect** | Автоматическое переподключение |

### Генерация ключей

```bash
# На сервере
xray uuid

# Или через клиент
python3 -c "import uuid; print(uuid.uuid4())"
```

---

## 🛠️ API Reference (Python)

```python
from vless_client import VLESSClient, VPNConfig

# Создание клиента
client = VLESSClient()

# Подключение
success = client.connect()

# Статус
status = client.status()
print(f"Connected: {status['connected']}")

# Отключение
client.disconnect()

# Обновление серверов
client.update_servers()
```

---

## 📊 Логирование

Клиент использует стандартный модуль logging Python:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] Message
```

**Уровни:**
- `INFO` - Общая информация
- `WARNING` - Предупреждения
- `ERROR` - Ошибки

---

## 🚀 CI/CD

### GitHub Actions

Автоматическая сборка при:
- Push в `main` или `develop`
- Создании тега `v*`
- Ручном запуске (workflow_dispatch)

**Артефакты:**
- `app-debug.apk` — Debug версия
- `app-release.apk` — Release версия

**Настройка подписи:** [ANDROID-BUILD.md](ANDROID-BUILD.md)

---

## 📋 Требования

### Desktop

- Python 3.8+
- XRay binary
- PyQt5 (опционально, для GUI)

### Android

- Android 5.0+ (API 21)
- Flutter 3.19+
- Java 17+

---

## 🔒 Безопасность

- ✅ **Нет логов** — клиент не сохраняет историю подключений
- ✅ **Шифрование** — VLESS с Reality протоколом
- ✅ **Open Source** — весь код открыт для аудита
- ✅ **No sudo** — установка без root прав

**Важно:** Не коммитьте файлы с секретными данными:
- `key.properties`
- `*.keystore`, `*.jks`
- `config/*.json`
- `data/servers.json`

---

## 📄 Лицензия

MIT License — см. файл [LICENSE](LICENSE).

---

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📞 Поддержка

- **Issues:** [GitHub Issues](https://github.com/zametkikostik/vless-vpn-client/issues)
- **Telegram:** @vless_vpn_support
- **Email:** support@vless-vpn.com

---

## 🔗 Полезные ссылки

- [Настройка Android](ANDROID-SETUP.md)
- [Сборка APK](ANDROID-BUILD.md)
- [Документация по установке](INSTALL.md)
- [XRay-core](https://github.com/XTLS/Xray-core)
- [VLESS спецификация](https://github.com/XTLS/Xray-core/issues/158)

---

**Версия:** 3.0.0
**Дата обновления:** 27.02.2026
**Статус:** ✅ Production Ready
