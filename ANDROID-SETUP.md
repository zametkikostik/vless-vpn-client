# 📱 Android VPN — Настройка v2rayNG / Hiddify

Полная инструкция по настройке VPN на Android смартфоне для обхода блокировок.

---

## 📋 Содержание

1. [Установка приложения](#установка-приложения)
2. [Импорт конфигурации](#импорт-конфигурации)
3. [Настройка Split-tunneling](#настройка-split-tunneling)
4. [Списки приложений](#списки-приложений)
5. [Устранение проблем](#устранение-проблем)

---

## 📲 Установка приложения

### Вариант 1: v2rayNG (рекомендуется)

**Источники:**
- [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang)
- [GitHub Releases](https://github.com/2dust/v2rayNG/releases)

**Преимущества:**
- ✅ Легковесное
- ✅ Поддержка VLESS-Reality
- ✅ Split-tunneling по приложениям
- ✅ Автозапуск

### Вариант 2: Hiddify Next

**Источники:**
- [GitHub Releases](https://github.com/hiddify/hiddify-next/releases)
- [Google Play](https://play.google.com/store/apps/details?id=app.hiddify.com)

**Преимущества:**
- ✅ Современный интерфейс
- ✅ Автовыбор лучшего сервера
- ✅ Встроенные списки обхода
- ✅ Поддержка подписок

---

## 🔗 Импорт конфигурации

### Шаг 1: Получение VLESS ссылки

На сервере выполните:
```bash
cat /root/vless-link.txt
```

Или сгенерируйте новую:
```bash
xray uuid
```

### Шаг 2: Импорт в v2rayNG

1. Откройте v2rayNG
2. Нажмите **+** (добавить профиль)
3. Выберите **Импортировать из буфера**
4. Вставьте VLESS ссылку
5. Нажмите **✓** (сохранить)

### Шаг 3: Импорт в Hiddify

1. Откройте Hiddify
2. Нажмите **+** → **Import from clipboard**
3. Или отсканируйте QR код камерой

---

## ⚙️ Настройка Split-tunneling

### v2rayNG

1. **Настройки** → **Режим маршрутизации**
2. Выберите **Только указанные приложения**
3. Нажмите **Выбрать приложения**
4. Отметьте приложения для VPN:

```
✅ Соцсети:
   - Facebook
   - Instagram
   - Twitter (X)
   - TikTok
   - Telegram
   - WhatsApp
   - Discord

✅ Видео:
   - YouTube
   - Vimeo
   - Twitch

✅ ИИ-сервисы:
   - ChatGPT
   - Claude
   - Gemini
   - Midjourney
   - Браузеры (Chrome, Firefox)

❌ Российские приложения (напрямую):
   - VK
   - OK
   - Яндекс
   - Сбербанк
   - Госуслуги
   - 2ГИС
```

5. Сохраните настройки

### Hiddify

1. **Settings** → **Routing**
2. Выберите **Custom rules**
3. Добавьте домены для VPN:
   ```
   youtube.com
   googlevideo.com
   instagram.com
   facebook.com
   twitter.com
   tiktok.com
   openai.com
   anthropic.com
   ```
4. Сохраните

---

## 🎯 Списки приложений

### Через VPN (обязательно)

| Категория | Приложения |
|-----------|------------|
| **Соцсети** | Facebook, Instagram, Twitter, TikTok, LinkedIn, Pinterest |
| **Мессенджеры** | Telegram, WhatsApp, Signal, Viber |
| **Видео** | YouTube, Vimeo, Twitch, Netflix |
| **ИИ** | ChatGPT, Claude, Gemini, Perplexity |
| **Браузеры** | Chrome, Firefox, Edge, Brave |
| **Почта** | Gmail, Outlook, ProtonMail |

### Напрямую (без VPN)

| Категория | Приложения |
|-----------|------------|
| **РФ Соцсети** | VK, OK |
| **РФ Сервисы** | Яндекс (все), Mail.ru, Rambler |
| **Банки** | Сбербанк, Тинькофф, Альфа, ВТБ |
| **Госуслуги** | Госуслуги, Налог.ру, ПФР |
| **Карты** | 2ГИС, Яндекс.Карты |
| **Такси** | Яндекс.Такси, Ситимобил |
| **Еда** | Яндекс.Еда, Delivery Club |

---

## 🔧 Дополнительные настройки

### v2rayNG

```
Настройки → Дополнительные:

✅ Обход LAN
✅ IPv6
✅ Сниффирование
✅ Отключить Cleartext
✅ Перезапускать при изменении сети

Режим батареи:
❌ Не оптимизировать (для автозапуска)
```

### Hiddify

```
Settings → Advanced:

✅ Enable Fragment
✅ Enable Noise
✅ Auto Connect
✅ Bypass LAN
✅ Enable IPv6
```

---

## 🚀 Быстрое подключение

### v2rayNG

1. Откройте приложение
2. Нажмите на сервер
3. Нажмите **V** (кнопка подключения)
4. Дождитесь **Connected**

### Hiddify

1. Откройте приложение
2. Выберите сервер
3. Нажмите **Connect**
4. Дождитесь зелёного индикатора

---

## 🛡️ Обход блокировок

### Если VPN блокируется

**v2rayNG:**
1. Настройки → **Режим обхода**
2. Включите **Fragment**
3. Установите:
   - Fragment length: 100-300
   - Fragment interval: 10-50

**Hiddify:**
1. Settings → **Fragment**
2. Enable: **ON**
3. Pattern: `tlshello`
4. Length: `100-200`

### Если не работает YouTube

1. Очистите кэш YouTube
2. Переустановите приложение
3. Проверьте Split-tunneling
4. Смените сервер

---

## 📊 Мониторинг

### Статистика трафика

**v2rayNG:**
- Главный экран → скорость ↑↓
- Долгое нажатие → статистика

**Hiddify:**
- Главный экран → график
- Settings → Traffic statistics

### Проверка подключения

```
1. Откройте браузер
2. Перейдите на 2ip.ru
3. Проверьте IP и страну
4. YouTube должен работать
```

---

## ❓ Устранение проблем

### "Не удаётся подключиться"

1. Проверьте интернет
2. Перезапустите приложение
3. Проверьте конфигурацию
4. Смените сервер

### "YouTube не работает"

1. Проверьте Split-tunneling
2. Очистите кэш
3. Обновите приложение

### "Быстро садится батарея"

1. Отключите автозапуск
2. Настройки → Экономия батареи
3. Отключите фоновые приложения

### "VPN отключается"

1. Настройки → Не оптимизировать батарею
2. Закрепите в памяти
3. Отключите энергосбережение

---

## 📥 QR код для импорта

Сгенерируйте QR код на сервере:

```bash
# Если есть ссылка
qrencode -o vless-qr.png "vless://UUID@IP:443?..."

# Или скопируйте в онлайн генератор
https://www.qr-code-generator.com/
```

Отсканируйте камерой в приложении.

---

## 🔗 Полезные ссылки

- [v2rayNG GitHub](https://github.com/2dust/v2rayNG)
- [Hiddify GitHub](https://github.com/hiddify/hiddify-next)
- [Xray-core](https://github.com/XTLS/Xray-core)
- [VLESS спецификация](https://github.com/XTLS/Xray-core/issues/158)

---

**Версия:** 1.0  
**Дата:** 26.02.2026
