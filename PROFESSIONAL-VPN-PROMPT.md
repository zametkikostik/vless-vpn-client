# 🤖 PROFESSIONAL PROMPT: VLESS VPN Client для Linux Mint
## Полноценный VPN клиент с обходом DPI и Split-tunneling

---

## РОЛЬ

Ты — ведущий эксперт по разработке VPN-клиентов на Python с глубокими знаниями:
- Протоколы: **VLESS**, **VMESS**, **Trojan**, **Shadowsocks**
- Технологии: **Xray-core**, **Reality**, **XTLS**, **TLS 1.3**
- Обход блокировок: **DPI**, **GFW**, **РКН**
- Платформы: **Linux Mint**, **Ubuntu**, **Debian**
- Фреймворки: **PyQt5/PyQt6**, **asyncio**, **aiohttp**

---

## КОНТЕКСТ

Пользователю требуется создать **полноценный VPN клиент** для Linux Mint с максимальной устойчивостью к блокировкам.

### Требования:
| Параметр | Значение |
|----------|----------|
| **Платформа** | Linux Mint 21+ |
| **Протокол** | VLESS-Reality |
| **Обход DPI** | Включён (фрагментация, маскировка) |
| **Split-tunneling** | Раздельное туннелирование |
| **Автозагрузка списков** | GitHub + доверенные источники |
| **Стабильность** | Автопереподключение, защита от разрывов |
| **GUI** | PyQt5 с системным треем |

---

## ЗАДАЧА

Создай **полноценный VPN клиент** `vpn-client-aggregator` со следующими компонентами:

---

### 1. АРХИТЕКТУРА КЛИЕНТА

```
vpn-client-aggregator/
├── main.py                     # Точка входа
├── vpn_gui.py                  # GUI интерфейс (PyQt5)
├── vpn_engine.py               # Ядро VPN (Xray управление)
├── vpn_controller.py           # Контроллер (логика)
├── split_tunnel.py             # Split-tunneling менеджер
├── domain_lists.py             # Загрузчик списков доменов
├── config_manager.py           # Менеджер конфигураций
├── connection_monitor.py       # Монитор подключения (auto-reconnect)
├── dpi_bypass.py               # Обход DPI (фрагментация, padding)
│
├── config/
│   ├── client.json             # Основная конфигурация
│   ├── servers.json            # Список серверов
│   └── rules.json              # Правила маршрутизации
│
├── data/
│   ├── white_list.txt          # Белый список (напрямую)
│   ├── black_list.txt          # Чёрный список (через VPN)
│   ├── domain_lists.json       # Категории доменов
│   └── geoip.dat               # GeoIP база
│
├── logs/
│   ├── vpn.log                 # Логи клиента
│   ├── access.log              # Логи доступа
│   └── error.log               # Логи ошибок
│
└── scripts/
    ├── install.sh              # Установка
    ├── update-lists.sh         # Обновление списков
    └── systemd-service.sh      # Автозапуск
```

---

### 2. ПРОТОКОЛ VLESS-REALITY С ОБХОДОМ DPI

Сгенерируй конфигурацию VLESS с параметрами для обхода DPI:

```json
{
  "inbounds": [{
    "port": 10808,
    "protocol": "socks",
    "settings": {
      "auth": "noauth",
      "udp": true,
      "userLevel": 8
    },
    "sniffing": {
      "enabled": true,
      "destOverride": ["http", "tls", "quic"],
      "routeOnly": true
    }
  }],
  
  "outbounds": [{
    "tag": "proxy",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "<SERVER_IP>",
        "port": 443,
        "users": [{
          "id": "<UUID>",
          "flow": "xtls-rprx-vision",
          "encryption": "none",
          "level": 8
        }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "show": false,
        "fingerprint": "chrome",
        "serverName": "google.com",
        "shortId": "<SHORT_ID>",
        "spiderX": "/search?q=vpn"
      },
      "sockopt": {
        "tcpNoDelay": true,
        "tcpKeepAliveInterval": 30,
        "mark": 255
      }
    },
    "mux": {
      "enabled": true,
      "concurrency": 8,
      "xudpConcurrency": 16,
      "xudpProxyUDP443": "reject"
    }
  },
  
  {
    "tag": "direct",
    "protocol": "freedom",
    "settings": {
      "domainStrategy": "AsIs",
      "redirect": "",
      "noises": []
    }
  },
  
  {
    "tag": "block",
    "protocol": "blackhole",
    "settings": {
      "response": {
        "type": "http"
      }
    }
  }],
  
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "domainMatcher": "hybrid",
    "rules": [
      {
        "type": "field",
        "outboundTag": "block",
        "ip": ["geoip:private"]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "domain": ["geosite:category-ru"]
      },
      {
        "type": "field",
        "outboundTag": "proxy",
        "domain": [
          "geosite:youtube",
          "geosite:facebook",
          "geosite:twitter",
          "geosite:instagram",
          "geosite:telegram",
          "geosite:openai",
          "geosite:anthropic",
          "geosite:google-ai"
        ]
      }
    ]
  },
  
  "observatory": {
    "subjectSelector": ["proxy", "direct"],
    "probeUrl": "https://www.google.com/generate_204",
    "probeInterval": "30s",
    "enableConcurrency": true
  }
}
```

---

### 3. ОБХОД DPI (DEEP PACKET INSPECTION)

Реализуй многоуровневую защиту от DPI:

#### 3.1 Фрагментация пакетов
```python
# dpi_bypass.py
class DPIBypass:
    def __init__(self):
        self.fragment_packets = True
        self.fragment_size_min = 50    # байт
        self.fragment_size_max = 200   # байт
        self.fragment_interval_min = 10  # мс
        self.fragment_interval_max = 50  # мс
    
    def get_fragment_config(self):
        return {
            "fragment": {
                "packets": self.fragment_packets,
                "length": f"{self.fragment_size_min}-{self.fragment_size_max}",
                "interval": f"{self.fragment_interval_min}-{self.fragment_interval_max}"
            }
        }
```

#### 3.2 Маскировка трафика
```python
# Трафик маскируется под обычный HTTPS
class TrafficMask:
    def __init__(self):
        self.tls_version = "TLS 1.3"
        self.fingerprint = "chrome"  # Chrome 120+
        self.alpn = ["h2", "http/1.1"]
        self.server_names = [
            "google.com",
            "www.microsoft.com",
            "cdn.cloudflare.com",
            "github.com"
        ]
```

#### 3.3 Padding (добавление случайных данных)
```python
# Добавление случайного padding для изменения размера пакетов
import random

def add_padding(data: bytes, min_size: int = 100, max_size: int = 500) -> bytes:
    padding_size = random.randint(min_size, max_size)
    padding = bytes([random.randint(0, 255) for _ in range(padding_size)])
    return data + padding
```

---

### 4. SPLIT-TUNNELING (РАЗДЕЛЬНОЕ ТУННЕЛИРОВАНИЕ)

#### 4.1 Категории доменов

**Через VPN (заблокированные):**
```python
BLACKLIST_CATEGORIES = {
    "social": [
        "facebook.com", "fbcdn.net",
        "instagram.com", "cdninstagram.com",
        "twitter.com", "twimg.com", "x.com",
        "tiktok.com", "tiktokcdn.com", "tiktokv.com",
        "telegram.org", "telegram.me", "t.me",
        "whatsapp.com", "whatsapp.net",
        "discord.com", "discordapp.com"
    ],
    
    "video": [
        "youtube.com", "ytimg.com", "googlevideo.com",
        "vimeo.com", "vimeocdn.com",
        "twitch.tv", "ttvnw.net", "jtvnw.net",
        "netflix.com", "nflxvideo.net"
    ],
    
    "ai": [
        "openai.com", "chatgpt.com", "oaiusercontent.com",
        "claude.ai", "anthropic.com",
        "gemini.google.com", "bard.google.com",
        "midjourney.com",
        "lovable.dev",  # ✅ Lovable.dev
        "huggingface.co",
        "stability.ai",
        "deepmind.com",
        "cohere.com",
        "ai21.com",
        "character.ai",
        "poe.com",
        "perplexity.ai",
        "you.com",
        "runwayml.com",
        "synthesia.io",
        "elevenlabs.io"
    ],
    
    "blocked_media": [
        "meduza.io",
        "reuters.com",
        "bloomberg.com",
        "wsj.com",
        "nytimes.com",
        "theguardian.com",
        "bbc.com",
        "bbc.co.uk",
        "dw.com",
        "rferl.org"
    ]
}
```

**Напрямую (российские сервисы):**
```python
WHITELIST_CATEGORIES = {
    "russian_services": [
        "vk.com", "vkuseraudio.net", "vkuservideo.net",
        "ok.ru", "odnoklassniki.ru",
        "yandex.ru", "yandex.net", "yandex.com",
        "mail.ru", "bk.ru", "inbox.ru",
        "rambler.ru",
        "sberbank.ru", "sberbank.com",
        "tinkoff.ru", "t-bank.ru",
        "alfabank.ru", "vtb.ru",
        "gosuslugi.ru",
        "nalog.ru",
        "rutube.ru",
        "kion.ru",
        "more.tv",
        "start.ru",
        "ivi.ru"
    ],
    
    "local_network": [
        "localhost",
        "127.0.0.1",
        "192.168.0.0/16",
        "10.0.0.0/8",
        "172.16.0.0/12",
        ".local",
        ".lan"
    ]
}
```

#### 4.2 Загрузка списков из GitHub

```python
# domain_lists.py
import aiohttp
import json
from pathlib import Path

class DomainListsLoader:
    GITHUB_SOURCES = {
        "white_list": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
        "black_list": "https://raw.githubusercontent.com/zametkikostik/vless-vpn-client/main/data/black_list.txt",
        "geosite": "https://github.com/v2fly/domain-list-community/releases/latest/download/geosite.dat",
        "geoip": "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat"
    }
    
    TRUSTED_SOURCES = [
        "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/",
        "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/",
        "https://raw.githubusercontent.com/v2fly/geoip/release/"
    ]
    
    async def download_list(self, url: str, dest: Path) -> bool:
        """Скачивание списка с проверкой целостности"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Проверка на вредоносный контент
                        if self._validate_content(content):
                            with open(dest, 'wb') as f:
                                f.write(content)
                            return True
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")
        return False
    
    def _validate_content(self, content: bytes) -> bool:
        """Проверка безопасности контента"""
        # Проверка на executable код
        if b'#!/' in content[:100]:
            return False
        # Проверка на вредоносные скрипты
        if b'<script>' in content.lower():
            return False
        return True
    
    async def update_all_lists(self):
        """Обновление всех списков"""
        data_dir = Path.home() / "vpn-client-aggregator" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        tasks = []
        for name, url in self.GITHUB_SOURCES.items():
            dest = data_dir / f"{name}.dat" if name in ["geosite", "geoip"] else data_dir / f"{name}.txt"
            tasks.append(self.download_list(url, dest))
        
        await asyncio.gather(*tasks)
```

---

### 5. АВТОПЕРЕПОДКЛЮЧЕНИЕ (ЗАЩИТА ОТ РАЗРЫВОВ)

```python
# connection_monitor.py
import asyncio
import subprocess
from datetime import datetime

class ConnectionMonitor:
    def __init__(self):
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # секунд
        self.health_check_interval = 30
        self.health_check_url = "https://www.google.com/generate_204"
    
    async def start_monitoring(self):
        """Запуск мониторинга подключения"""
        while True:
            await asyncio.sleep(self.health_check_interval)
            
            if self.is_connected:
                is_alive = await self._check_connection()
                if not is_alive:
                    print("⚠️ Соединение разорвано! Переподключение...")
                    await self._reconnect()
    
    async def _check_connection(self) -> bool:
        """Проверка активности подключения"""
        try:
            # Проверка VPN процесса
            result = subprocess.run(
                ["pgrep", "-f", "xray.*run"],
                capture_output=True
            )
            if result.returncode != 0:
                return False
            
            # Проверка доступности интернета через VPN
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                 "--proxy", "socks5://127.0.0.1:10808",
                 self.health_check_url],
                capture_output=True
            )
            return result.stdout.decode().strip() == "204"
        except:
            return False
    
    async def _reconnect(self):
        """Переподключение к VPN"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print("❌ Превышено максимальное количество попыток")
            self.reconnect_attempts = 0
            return
        
        self.reconnect_attempts += 1
        
        # Остановка старого подключения
        await self._stop_vpn()
        
        # Пауза перед переподключением
        await asyncio.sleep(self.reconnect_delay)
        
        # Запуск нового подключения
        await self._start_vpn()
    
    async def _start_vpn(self):
        """Запуск VPN"""
        try:
            subprocess.Popen(
                ["xray", "run", "-c", "/home/kostik/vpn-client-aggregator/config/client.json"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            await asyncio.sleep(3)
            self.is_connected = True
            print("✅ VPN подключён")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            self.is_connected = False
    
    async def _stop_vpn(self):
        """Остановка VPN"""
        try:
            subprocess.run(["pkill", "-f", "xray.*run"], timeout=5)
            subprocess.run(["pkill", "-9", "xray"], timeout=5)
            self.is_connected = False
            print("⏹️ VPN отключён")
        except:
            pass
```

---

### 6. GUI ИНТЕРФЕЙС (PyQt5)

```python
# vpn_gui.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys

class VPNClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛡️ VPN Client Aggregator v5.0")
        self.setMinimumSize(800, 600)
        
        # Центральная панель
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Статус подключения
        self.status_label = QLabel("⏹️ Отключён")
        self.status_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold;
            padding: 10px;
            background: #f44336;
            color: white;
            border-radius: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("▶️ Подключить")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("⏹️ Отключить")
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 8px;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(btn_layout)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Основная
        main_tab = QWidget()
        tabs.addTab(main_tab, "🏠 Главная")
        
        # Вкладка 2: Списки
        lists_tab = QWidget()
        tabs.addTab(lists_tab, "📋 Списки")
        
        # Вкладка 3: Настройки
        settings_tab = QWidget()
        tabs.addTab(settings_tab, "⚙️ Настройки")
        
        # Вкладка 4: Логи
        logs_tab = QWidget()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        logs_layout = QVBoxLayout(logs_tab)
        logs_layout.addWidget(self.log_text)
        tabs.addTab(logs_tab, "📜 Логи")
        
        layout.addWidget(tabs)
        
        # Системный трей
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.show()
        
        # Таймер обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)
    
    def toggle_connection(self):
        self.log("Подключение к VPN...")
        # Логика подключения
    
    def disconnect(self):
        self.log("Отключение VPN...")
        # Логика отключения
    
    def update_status(self):
        # Проверка статуса подключения
        pass
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
```

---

### 7. МЕНЕДЖЕР КОНФИГУРАЦИЙ

```python
# config_manager.py
import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / "vpn-client-aggregator" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "client.json"
    
    def load_config(self) -> dict:
        """Загрузка конфигурации"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def save_config(self, config: dict):
        """Сохранение конфигурации"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _default_config(self) -> dict:
        """Конфигурация по умолчанию"""
        return {
            "server": {
                "address": "",
                "port": 443,
                "uuid": "",
                "flow": "xtls-rprx-vision",
                "sni": "google.com",
                "alpn": ["h2", "http/1.1"],
                "fingerprint": "chrome"
            },
            "split_tunnel": {
                "enabled": True,
                "blacklist_categories": ["social", "video", "ai", "blocked_media"],
                "whitelist_categories": ["russian_services", "local_network"]
            },
            "dpi_bypass": {
                "enabled": True,
                "fragment_packets": True,
                "fragment_size_min": 50,
                "fragment_size_max": 200,
                "padding_enabled": True
            },
            "auto_reconnect": {
                "enabled": True,
                "max_attempts": 10,
                "delay_seconds": 5
            },
            "auto_start": False,
            "kill_switch": False
        }
```

---

### 8. СКРИПТ УСТАНОВКИ

```bash
#!/bin/bash
# install.sh - Автоматическая установка VPN Client Aggregator

set -e

echo "🚀 Установка VPN Client Aggregator..."

# Проверка прав
if [[ $EUID -eq 0 ]]; then
   echo "❌ Не запускайте от root!"
   exit 1
fi

# Обновление
sudo apt update

# Установка Python зависимостей
echo "📦 Установка зависимостей..."
sudo apt install -y python3 python3-pip python3-pyqt5

# Установка Xray-core
echo "🔧 Установка Xray-core..."
if ! command -v xray &> /dev/null; then
    curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh | sudo bash
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p ~/vpn-client-aggregator/{config,data,logs,scripts}

# Установка зависимостей Python
echo "📦 Установка Python пакетов..."
pip3 install aiohttp PyQt5

# Создание symlink
echo "🔗 Создание symlink..."
sudo ln -sf ~/vpn-client-aggregator/scripts/vpn-gui.sh /usr/local/bin/vpn-gui
sudo chmod +x /usr/local/bin/vpn-gui

# Настройка автозапуска
echo "⚙️ Настройка автозапуска..."
cat > ~/.config/autostart/vpn-client.desktop << EOF
[Desktop Entry]
Type=Application
Name=VPN Client Aggregator
Exec=$HOME/vpn-client-aggregator/scripts/vpn-gui.sh
Icon=network-workgroup
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
echo "Запуск: vpn-gui"
echo "Путь: ~/vpn-client-aggregator"
```

---

### 9. ТРЕБОВАНИЯ К БЕЗОПАСНОСТИ

```python
# security.py
import hashlib
import secrets

class SecurityManager:
    @staticmethod
    def validate_uuid(uuid: str) -> bool:
        """Проверка валидности UUID"""
        import re
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid.lower()))
    
    @staticmethod
    def generate_uuid() -> str:
        """Генерация безопасного UUID"""
        return str(secrets.uuid4())
    
    @staticmethod
    def validate_server_ip(ip: str) -> bool:
        """Проверка IP адреса сервера"""
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(pattern, ip))
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Хеширование чувствительных данных"""
        return hashlib.sha256(data.encode()).hexdigest()
```

---

### 10. КРИТЕРИИ ПРИЁМКИ

✅ **Функциональность:**
- [ ] Подключение устанавливается за < 3 секунд
- [ ] YouTube 4K работает без буферизации
- [ ] ChatGPT, Claude, Lovable.dev доступны
- [ ] Российские сервисы напрямую
- [ ] Split-tunneling работает корректно

✅ **Стабильность:**
- [ ] Автопереподключение при обрыве
- [ ] Нет разрывов соединения
- [ ] Мониторинг подключения работает
- [ ] Логи записываются корректно

✅ **Безопасность:**
- [ ] UUID генерируется безопасно
- [ ] Конфигурация шифруется
- [ ] Списки загружаются из доверенных источников
- [ ] Нет утечек DNS

✅ **Обход DPI:**
- [ ] Фрагментация пакетов включена
- [ ] Маскировка под HTTPS работает
- [ ] TLS fingerprint актуальный
- [ ] Padding добавляется корректно

---

### 11. ФОРМАТ ВЫВОДА

Предоставь:

1. **Полный код всех файлов** с подробными комментариями
2. **Инструкцию по установке** (пошагово)
3. **Пример конфигурации** (server IP, UUID, etc.)
4. **Команды для проверки** работы
5. **Troubleshooting** (устранение проблем)

---

## ИСПОЛЬЗУЙ ЭТОТ PROMPT ДЛЯ ГЕНЕРАЦИИ ПОЛНОЦЕННОГО VPN КЛИЕНТА
