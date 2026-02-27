# 🚀 VLESS VPN Ultimate - Git Deployment Guide

## 📦 Production Ready APK

### ✨ Функции
- 🔒 **DPI Bypass** - Обход DPI (фрагментация, padding, TLS мимикрия)
- 🛡️ **Чебурнет Resistance** - Устойчивость к блокировкам
- 🌐 **Server Scanner** - Сканирование из всех источников
- 📱 **Android App** - Production готовое приложение
- 🚀 **Auto-start** - Автозапуск при старте системы

---

## 🎯 Быстрое развёртывание в Git

### 1. Добавление файлов

```bash
cd /home/kostik/vless-vpn-client

# Добавить все новые файлы
git add -A

# Проверить что добавлено
git status
```

### 2. Коммит

```bash
git commit -m "feat: VLESS VPN Ultimate - Production Ready

- DPI Bypass для Чебурнета (фрагментация, padding, TLS мимикрия)
- Сканер серверов из всех источников (GitHub, aggregators)
- Android приложение с production сборкой
- Автозапуск и интеграция в систему
- GUI интерфейс с полным функционалом
- GitHub Actions для автоматической сборки APK

Version: 4.0.0
Status: Production Ready ✅"
```

### 3. Push в репозиторий

```bash
# Отправить в main ветку
git push origin main

# Или создать отдельную ветку
git checkout -b ultimate-vpn
git push -u origin ultimate-vpn
```

---

## 📱 Публикация Android APK

### Вариант 1: GitHub Releases (Автоматически)

```bash
# Создать тег версии
git tag v4.0.0

# Отправить тег
git push origin v4.0.0
```

GitHub Actions автоматически:
1. ✅ Соберёт APK (Debug + Release)
2. ✅ Соберёт App Bundle для Google Play
3. ✅ Создаст релиз на GitHub
4. ✅ Прикрепит APK файлы к релизу

**APK будет доступен в:** https://github.com/zametkikostik/vless-vpn-client/releases

### Вариант 2: Ручная сборка

```bash
cd mobile-client

# Production APK
flutter build apk --release --flavor production

# App Bundle для Google Play
flutter build appbundle --release --flavor production
```

Файлы будут в:
```
mobile-client/build/app/outputs/flutter-apk/
├── app-production-release.apk
└── app-production-release-arm64-v8a.apk

mobile-client/build/app/outputs/bundle/productionRelease/
└── app-release.aab
```

---

## 🔐 Настройка GitHub Secrets

Для автоматической подписи APK добавьте секреты:

1. Перейдите в: `Settings` → `Secrets and variables` → `Actions`

2. Добавьте секреты:

| Secret | Value |
|--------|-------|
| `ANDROID_KEYSTORE_BASE64` | Base64 keystore файла |
| `ANDROID_KEY_ALIAS` | `vless-vpn` |
| `ANDROID_KEY_PASSWORD` | Пароль от keystore |

### Получение Base64 keystore:

```bash
# Конвертация в Base64
base64 -w 0 mobile-client/android/vless-vpn.keystore > keystore_base64.txt

# Копирование содержимого
cat keystore_base64.txt
```

---

## 📊 Структура репозитория

```
vless-vpn-client/
├── .github/workflows/
│   └── android-build.yml       # GitHub Actions для APK
├── mobile-client/               # Flutter приложение
│   ├── android/
│   │   ├── key.properties      # ⚠️ В .gitignore!
│   │   └── vless-vpn.keystore  # ⚠️ В .gitignore!
│   ├── lib/
│   │   ├── main.dart           # Точка входа
│   │   ├── screens/
│   │   │   ├── home_screen.dart
│   │   │   ├── servers_screen.dart
│   │   │   └── settings_screen.dart
│   │   └── providers/
│   │       ├── vpn_provider.dart
│   │       └── server_provider.dart
│   └── pubspec.yaml
├── vless_client_ultimate.py    # Desktop клиент
├── vpn_gui_ultimate.py         # Desktop GUI
├── install-ultimate.sh         # Скрипт установки
├── README-ULTIMATE.md          # Документация
└── QUICK-START-ULTIMATE.md     # Быстрый старт
```

---

## 🎨 Версионирование

### pubspec.yaml

```yaml
version: 4.0.0+1  # MAJOR.MINOR.PATCH+BUILD
```

- `4` - Major (большие изменения)
- `0` - Minor (новые функции)
- `0` - Patch (исправления)
- `+1` - Build number (увеличивать при каждой сборке)

### Git Tags

```bash
# Версия приложения
git tag v4.0.0
git push origin v4.0.0

# Pre-release
git tag v4.0.0-beta.1
git push origin v4.0.0-beta.1
```

---

## 📝 CHANGELOG

Создайте файл `CHANGELOG.md`:

```markdown
# Changelog

## [4.0.0] - 2026-02-27

### Added
- 🔒 DPI Bypass для Чебурнета
- 🌐 Сканер серверов из всех источников
- 📱 Android приложение (Production Ready)
- 🚀 Автозапуск для Linux
- 🎨 GUI интерфейс

### Changed
- Обновлён VPN клиент до Ultimate версии
- Улучшена стабильность подключения
- Оптимизирован выбор серверов

### Fixed
- Исправлены ошибки подключения
- Улучшена обработка ошибок
```

---

## 🧪 Тестирование перед релизом

### Checklist

- [ ] Flutter приложение компилируется
- [ ] APK подписан
- [ ] Desktop клиент работает
- [ ] Сканер находит серверы
- [ ] DPI Bypass активен
- [ ] Автозапуск настроен
- [ ] Документация обновлена
- [ ] Все тесты пройдены

### Команды для проверки

```bash
# Flutter анализ
cd mobile-client
flutter analyze

# Flutter тесты
flutter test

# Desktop клиент
python3 vless_client_ultimate.py status

# GUI
python3 vpn_gui_ultimate.py
```

---

## 🚀 GitHub Release Checklist

1. **Подготовка**
   - [ ] Обновлена версия в `pubspec.yaml`
   - [ ] Обновлён `CHANGELOG.md`
   - [ ] Все файлы закоммичены

2. **Создание тега**
   - [ ] `git tag v4.0.0`
   - [ ] `git push origin v4.0.0`

3. **GitHub Actions**
   - [ ] Сборка запущена (проверить в Actions)
   - [ ] APK собран успешно
   - [ ] Релиз создан

4. **Публикация**
   - [ ] Проверить релиз на GitHub
   - [ ] APK файлы прикреплены
   - [ ] Release notes корректны

---

## 📱 Установка из GitHub Releases

### На Android

1. Откройте https://github.com/zametkikostik/vless-vpn-client/releases
2. Скачайте последний релиз
3. Скачайте `vless-vpn-ultimate.apk`
4. Установите (разрешите из неизвестных источников)
5. Запустите приложение

### На Linux

```bash
# Установка
cd ~/vless-vpn-client
./install-ultimate.sh

# Запуск GUI
vless-vpn-gui gui

# Запуск CLI
vless-vpn-ultimate start
```

---

## 🔧 Troubleshooting

### GitHub Actions не собирает APK

**Проверьте:**
1. Файл `.github/workflows/android-build.yml` существует
2. Flutter версия в workflow совпадает с локальной
3. Keystore правильно сконвертирован в Base64

### APK не подписан

**Решение:**
1. Проверьте `key.properties`
2. Проверьте GitHub Secrets
3. Убедитесь что keystore существует

### Ошибка при коммите

**Решение:**
```bash
# Настроить Git пользователя
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Повторить коммит
git add -A
git commit -m "Your message"
```

---

## 📞 Поддержка

### Документация
- [README-ULTIMATE.md](README-ULTIMATE.md) - Полная документация
- [QUICK-START-ULTIMATE.md](QUICK-START-ULTIMATE.md) - Быстрый старт
- [PRODUCTION-BUILD.md](mobile-client/PRODUCTION-BUILD.md) - Production сборка

### Логи
```bash
# Desktop
tail -f ~/vless-vpn-client/logs/client.log

# GitHub Actions
Проверьте вкладку "Actions" на GitHub
```

---

## 🎉 Готово!

Ваш VLESS VPN Ultimate готов к публикации!

**Следующие шаги:**
1. ✅ Закоммитьте изменения
2. ✅ Отправьте в Git
3. ✅ Создайте тег версии
4. ✅ Дождитесь сборки GitHub Actions
5. ✅ Опубликуйте релиз

**Успехов! 🚀**
