# 🔐 Production APK Сборка - Настройка

## 📋 Быстрый старт

### 1. Создание Keystore (локально)

```bash
cd mobile-client/android

# Создание keystore для подписи
keytool -genkey -v \
  -keystore vless-vpn.keystore \
  -alias vless-vpn \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

**Вам будут предложены:**
- Пароль для хранилища (keystore password) - запомните его!
- Имя и фамилия
- Название организации
- Пароль для ключа (можно тот же)

### 2. Создание key.properties

```bash
cd mobile-client/android

cat > key.properties << EOF
storePassword=ВАШ_ПАРОЛЬ
keyPassword=ВАШ_ПАРОЛЬ
keyAlias=vless-vpn
storeFile=vless-vpn.keystore
EOF
```

### 3. Локальная сборка APK

```bash
cd mobile-client

# Debug версия
flutter build apk --debug

# Production Release
flutter build apk --release --flavor production

# App Bundle для Google Play
flutter build appbundle --release --flavor production
```

**APK файлы будут в:**
```
mobile-client/build/app/outputs/flutter-apk/
├── app-debug.apk
├── app-production-release.apk
└── app-production-release-arm64-v8a.apk (для 64-bit устройств)
```

---

## 🚀 GitHub Actions - Автоматическая сборка

### Настройка секретов GitHub

1. **Сконвертируйте keystore в Base64:**

```bash
# Linux
base64 -w 0 mobile-client/android/vless-vpn.keystore > keystore_base64.txt

# macOS
base64 -i mobile-client/android/vless-vpn.keystore | tr -d '\n' > keystore_base64.txt
```

2. **Добавьте секреты в GitHub:**

Перейдите в: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret Name | Value |
|-------------|-------|
| `ANDROID_KEYSTORE_BASE64` | Содержимое `keystore_base64.txt` |
| `ANDROID_KEY_ALIAS` | `vless-vpn` |
| `ANDROID_KEY_PASSWORD` | Ваш пароль от keystore |

### Автоматическая публикация релиза

При создании тега вида `v*`:

```bash
# Создайте тег версии
git tag v4.0.0

# Отправьте тег
git push origin v4.0.0
```

GitHub Actions автоматически:
1. Соберёт APK (Debug + Release)
2. Соберёт App Bundle для Google Play
3. Создаст релиз на GitHub
4. Прикрепит все APK файлы к релизу

---

## 📱 Установка APK на Android

### Через USB (ADB)

```bash
adb install mobile-client/build/app/outputs/flutter-apk/app-production-release.apk
```

### Через GitHub Releases

1. Откройте https://github.com/zametkikostik/vless-vpn-client/releases
2. Скачайте последний релиз
3. Скачайте `vless-vpn-ultimate.apk` или `app-production-release.apk`
4. Установите на устройство
5. Разрешите установку из неизвестных источников

---

## 🔧 Production конфигурация

### AndroidManifest.xml

Файл: `mobile-client/android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- Интернет -->
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    
    <!-- VPN -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>
    
    <!-- Уведомления -->
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    
    <!-- Background service -->
    <uses-permission android:name="android.permission.WAKE_LOCK"/>
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
    
    <application
        android:label="VLESS VPN"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme"
              />
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        
        <!-- Don't delete the meta-data below -->
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
```

### build.gradle настройки

Файл: `mobile-client/android/app/build.gradle`

```gradle
android {
    compileSdkVersion 34
    ndkVersion flutter.ndkVersion

    defaultConfig {
        applicationId "com.vless.vpn.client"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
        multiDexEnabled true
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    flavorDimensions "default"
    productFlavors {
        production {
            dimension "default"
            applicationIdSuffix ""
            resValue "string", "app_name", "VLESS VPN"
        }
        dev {
            dimension "default"
            applicationIdSuffix ".dev"
            resValue "string", "app_name", "VLESS VPN Dev"
        }
    }
}
```

---

## 🛡️ ProGuard правила

Файл: `mobile-client/android/app/proguard-rules.pro`

```proguard
# Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# Google
-keep class com.google.** { *; }
-keep class com.android.** { *; }

# VLESS VPN
-keep class com.vless.vpn.** { *; }
-dontwarn com.vless.vpn.**

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep custom view constructors
-keepclasseswithmembers class * {
    public <init>(android.content.Context, android.util.AttributeSet);
}
-keepclasseswithmembers class * {
    public <init>(android.content.Context, android.util.AttributeSet, int);
}

# Keep enum
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep parcelable
-keep class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator *;
}
```

---

## 📊 Верификация APK

### Проверка подписи

```bash
# Проверка подписи APK
apksigner verify --verbose mobile-client/build/app/outputs/flutter-apk/app-production-release.apk

# Информация о подписи
apksigner verify --print-certs mobile-client/build/app/outputs/flutter-apk/app-production-release.apk
```

### Проверка версии

```bash
# Информация о APK
aapt dump badging mobile-client/build/app/outputs/flutter-apk/app-production-release.apk | grep -E "package:|sdkVersion:"
```

---

## 🔐 Безопасность

### ⚠️ НИКОГДА НЕ КОММИТЬТЕ:

- `mobile-client/android/key.properties` ❌
- `mobile-client/android/app/*.keystore` ❌
- `mobile-client/android/app/*.jks` ❌

### Добавьте в .gitignore:

```gitignore
# Android
mobile-client/android/*.keystore
mobile-client/android/*.jks
mobile-client/android/key.properties
mobile-client/android/local.properties

# Build
mobile-client/build/
```

### Резервное копирование

Сохраните keystore в надёжном месте:
- Зашифрованное облачное хранилище
- USB флешка
- Менеджер паролей (как файл)

**При потере keystore невозможно обновить приложение в Google Play!**

---

## 📦 Google Play Console

### Подготовка к публикации

1. Соберите App Bundle:
   ```bash
   flutter build appbundle --release --flavor production
   ```

2. Файл будет в:
   ```
   mobile-client/build/app/outputs/bundle/productionRelease/app-release.aab
   ```

3. Загрузите в Google Play Console

### Версионирование

В `pubspec.yaml`:
```yaml
version: 4.0.0+1  # MAJOR.MINOR.PATCH+BUILD_NUMBER
```

- `4.0.0` - версия для пользователя
- `+1` - внутренний номер сборки (увеличивайте при каждой сборке)

---

## 🐛 Troubleshooting

### Ошибка: "SigningConfig 'release' not found"

**Решение:**
1. Убедитесь что `key.properties` существует
2. Или настройте GitHub Secrets

### Ошибка: "Keystore was tampered with, or password was incorrect"

**Решение:**
Проверьте правильность паролей в `key.properties` или GitHub Secrets

### Ошибка: "Base64 decoding failed"

**Решение:**
Убедитесь что `ANDROID_KEYSTORE_BASE64` содержит корректную строку без пробелов

### APK не устанавливается

**Решение:**
1. Разрешите установку из неизвестных источников
2. Проверьте что APK подписан
3. Удалите старую версию приложения

---

## 📝 Чеклист перед релизом

- [ ] Keystore создан и сохранён
- [ ] `key.properties` настроен локально
- [ ] GitHub Secrets добавлены
- [ ] Версия в `pubspec.yaml` обновлена
- [ ] Тесты пройдены
- [ ] CHANGELOG обновлён
- [ ] Тег версии создан
- [ ] Релиз на GitHub опубликован

---

**Версия:** 4.0.0  
**Дата:** 27.02.2026  
**Статус:** Production Ready ✅
