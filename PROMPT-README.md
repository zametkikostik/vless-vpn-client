# 🤖 PROMPT для создания VPN клиента v5.0

## 📍 Назначение

Этот PROMPT предназначен для генерации **полноценного VPN клиента** на Python с:
- VLESS-Reality протоколом
- Обходом DPI (многоуровневая защита)
- Split-tunneling (раздельное туннелирование)
- Автопереподключением
- Загрузкой списков из GitHub

---

## 📁 Где находится

```
/home/kostik/vpn-client-aggregator/PROFESSIONAL-VPN-PROMPT.md
```

---

## 🚀 Как использовать

### Вариант 1: Отправить в AI (Claude/GPT)

1. Скопируй содержимое `PROFESSIONAL-VPN-PROMPT.md`
2. Отправь в ChatGPT/Claude с запросом:
   ```
   Используй этот PROMPT для генерации полноценного VPN клиента
   ```

### Вариант 2: Использовать как ТЗ

Используй как техническое задание для разработки

---

## 📋 Что включает PROMPT

| Раздел | Описание |
|--------|----------|
| **Архитектура** | Структура проекта, все файлы |
| **VLESS-Reality** | Конфигурация протокола |
| **Обход DPI** | Фрагментация, padding, маскировка |
| **Split-tunneling** | Чёрные/белые списки доменов |
| **Автопереподключение** | Защита от разрывов |
| **GUI (PyQt5)** | Интерфейс с системным треем |
| **Безопасность** | Валидация, шифрование |
| **Установка** | Скрипты для Linux Mint |

---

## 🎯 Ключевые возможности

### Обход DPI:
- ✅ Фрагментация пакетов (50-200 байт)
- ✅ Padding (случайные данные)
- ✅ TLS 1.3 маскировка
- ✅ Fingerprint: Chrome 120+

### Split-tunneling:
- ✅ **Через VPN**: YouTube, Facebook, Instagram, Twitter, TikTok, ChatGPT, Claude, **Lovable.dev**, ИИ-сервисы
- ✅ **Напрямую**: VK, Yandex, Mail.ru, Сбербанк, Госуслуги

### Автозагрузка списков:
- ✅ GitHub (igareck/vpn-configs-for-russia)
- ✅ v2fly/domain-list-community
- ✅ v2fly/geoip
- ✅ Проверка безопасности контента

### Стабильность:
- ✅ Автопереподключение (до 10 попыток)
- ✅ Мониторинг подключения (30 сек)
- ✅ Проверка через google.com/generate_204
- ✅ Mux concurrency: 8

---

## 📦 Структура созданного клиента

```
vpn-client-aggregator/
├── main.py                     # Точка входа
├── vpn_gui.py                  # GUI (PyQt5)
├── vpn_engine.py               # Xray управление
├── vpn_controller.py           # Контроллер
├── split_tunnel.py             # Split-tunneling
├── domain_lists.py             # Загрузка списков
├── config_manager.py           # Конфигурации
├── connection_monitor.py       # Автопереподключение
├── dpi_bypass.py               # Обход DPI
└── config/
    ├── client.json             # Клиент
    ├── servers.json            # Серверы
    └── rules.json              # Правила
```

---

## 🔗 GitHub обновлён

https://github.com/zametkikostik/vless-vpn-client

---

## 📝 Следующий шаг

Отправь этот PROMPT в AI для генерации кода:

```
Создай VPN клиент на Python используя этот PROMPT:
[скопировать содержимое PROFESSIONAL-VPN-PROMPT.md]
```

Или начни создавать файлы по одному согласно архитектуре в PROMPT.
