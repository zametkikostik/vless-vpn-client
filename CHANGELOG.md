# 📝 Changelog

Все изменения в проекте VLESS VPN Client.

---

## [3.0.0] - 27.02.2026

### 🎉 Добавлено

- **Flutter Android приложение**
  - Полный UI с Material Design 3
  - Автоматическое подключение к серверам
  - Список серверов с проверкой пинга
  - Split-tunneling для приложений
  - Тёмная тема
  
- **GitHub Actions CI/CD**
  - Автоматическая сборка APK
  - Подпись через GitHub Secrets
  - Публикация в Releases
  - Тестирование кода

- **Документация**
  - ANDROID-BUILD.md — настройка подписи
  - DEPLOYMENT.md — production развёртывание
  - Обновлённый README.md

### 🔧 Изменено

- **server_scanner.py**
  - Исправлена синтаксическая ошибка (строка 213)
  - Улучшен парсинг Reality конфигов
  - Добавлена проверка TCP подключения

- **pubspec.yaml**
  - Добавлены зависимости: `http`, `package_info_plus`
  - Обновлены версии пакетов

- **.gitignore**
  - Добавлены Flutter/Android исключения
  - Keystore файлы исключены

### 📁 Структура

```
mobile-client/
├── lib/
│   ├── main.dart
│   ├── models/server.dart
│   ├── providers/
│   │   ├── vpn_provider.dart
│   │   └── server_provider.dart
│   ├── screens/
│   │   ├── home_screen.dart
│   │   ├── servers_screen.dart
│   │   └── settings_screen.dart
│   └── widgets/
│       ├── connection_status.dart
│       ├── server_card.dart
│       └── server_list_tile.dart
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml
│   │   │   ├── kotlin/.../MainActivity.kt
│   │   │   └── res/...
│   │   ├── build.gradle
│   │   └── proguard-rules.pro
│   ├── build.gradle
│   ├── settings.gradle
│   └── gradle.properties
└── pubspec.yaml
```

---

## [2.0.0] - 26.02.2026

### Добавлено

- SaaS архитектура
- Split-tunneling
- GUI интерфейс (PyQt5)
- Автоматическое обновление серверов

### Изменено

- Улучшена обработка ошибок
- Оптимизирован выбор сервера
- Обновлены зависимости

---

## [1.0.0] - 25.02.2026

### Добавлено

- Первый стабильный релиз
- Базовый VLESS клиент
- Интеграция с XRay
- Reality протокол

---

## Формат

- **Добавлено** — новые функции
- **Изменено** — изменения в существующих функциях
- **Удалено** — удалённые функции
- **Исправлено** — исправления ошибок

---

**[3.0.0]**: 27.02.2026
**[2.0.0]**: 26.02.2026
**[1.0.0]**: 25.02.2026
