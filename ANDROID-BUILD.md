# 🔐 Настройка подписи APK для GitHub Actions

Для публикации подписанных APK в GitHub Releases необходимо настроить keystore и GitHub Secrets.

---

## 📋 Шаг 1: Создание Keystore

### Вариант 1: Локально (рекомендуется)

```bash
keytool -genkey -v -keystore vless-vpn.keystore -alias vless-vpn -keyalg RSA -keysize 2048 -validity 10000
```

**Параметры:**
- `vless-vpn.keystore` — файл хранилища ключей
- `vless-vpn` — алиас ключа
- `10000` — срок действия в днях (~27 лет)

Вам будут предложены:
1. Пароль для хранилища (keystore password)
2. Имя и фамилия
3. Название организации
4. Пароль для ключа (key password) — можно нажать Enter для использования того же пароля

### Вариант 2: Онлайн генератор

Используйте [keystore.jks генератор](https://www.dev2qa.com/download-sample-keystore-file-jks-keystore-example/)

---

## 📋 Шаг 2: Создание key.properties

Создайте файл `mobile-client/android/key.properties`:

```properties
storePassword=ВАШ_ПАРОЛЬ_ХРАНИЛИЩА
keyPassword=ВАШ_ПАРОЛЬ_КЛЮЧА
keyAlias=vless-vpn
storeFile=vless-vpn.keystore
```

**⚠️ Важно:** Добавьте `key.properties` в `.gitignore`!

---

## 📋 Шаг 3: Настройка GitHub Secrets

### 3.1. Конвертация keystore в Base64

```bash
base64 -w 0 mobile-client/android/vless-vpn.keystore > keystore_base64.txt
```

Или на macOS:
```bash
base64 -i mobile-client/android/vless-vpn.keystore | tr -d '\n' > keystore_base64.txt
```

Скопируйте содержимое файла `keystore_base64.txt`.

### 3.2. Добавление секретов в GitHub

1. Перейдите в репозиторий на GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. **Repository secrets** → **New repository secret**

Добавьте следующие секреты:

| Название секрета | Значение |
|-----------------|----------|
| `ANDROID_KEYSTORE_BASE64` | Содержимое `keystore_base64.txt` (длинная строка) |
| `ANDROID_KEY_ALIAS` | `vless-vpn` (или ваш алиас) |
| `ANDROID_KEY_PASSWORD` | Пароль от хранилища/ключа |

---

## 📋 Шаг 4: Тестирование сборки

### Локальная сборка

```bash
cd mobile-client

# Debug сборка
flutter build apk --debug

# Release сборка (с подписью)
flutter build apk --release
```

APK файлы будут в:
```
mobile-client/build/app/outputs/flutter-apk/
├── app-debug.apk
└── app-release.apk
```

### GitHub Actions сборка

1. Сделайте push в ветку `main` или создайте тег:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. Перейдите в **Actions** → **Android APK Build**

3. Скачайте APK из артефактов или релиза

---

## 📋 Шаг 5: Публикация релиза

### Автоматическая публикация

При создании тега вида `v*` (например, `v1.0.0`, `v2.1.3`):

1. GitHub Actions автоматически соберёт APK
2. Создаст релиз на GitHub
3. Прикрепит APK файлы к релизу

### Ручная публикация

```bash
# Создайте тег
git tag v1.0.0

# Отправьте тег
git push origin v1.0.0
```

Или через GitHub UI:
1. **Releases** → **Draft a new release**
2. Выберите тег или создайте новый
3. Нажмите **Publish release**

---

## 🔧 Troubleshooting

### Ошибка: "Keystore was tampered with, or password was incorrect"

Проверьте правильность пароля в GitHub Secrets:
- `ANDROID_KEY_PASSWORD` должен совпадать с паролем хранилища

### Ошибка: "signingConfig 'release' not found"

Убедитесь, что `key.properties` существует или настроены GitHub Secrets.

### Ошибка: "Base64 decoding failed"

Проверьте, что `ANDROID_KEYSTORE_BASE64` содержит корректную Base64 строку без пробелов и переносов строк.

### APK не подписан

Проверьте, что:
1. Keystore файл существует
2. Пароли указаны верно
3. Алиас ключа совпадает

---

## 📱 Установка APK на Android

### Через USB

```bash
adb install mobile-client/build/app/outputs/flutter-apk/app-release.apk
```

### Через GitHub Releases

1. Откройте релиз на GitHub
2. Скачайте `app-release.apk`
3. Установите на устройство
4. Разрешите установку из неизвестных источников

---

## 🔐 Безопасность

- **Никогда не коммитьте** `key.properties` и `.keystore` файлы в репозиторий
- Храните резервную копию keystore в надёжном месте
- При потере keystore невозможно обновить приложение в Google Play

---

**Версия:** 1.0
**Дата:** 27.02.2026
