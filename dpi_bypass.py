#!/usr/bin/env python3
"""
VPN Client Aggregator v5.0
Обход DPI (Deep Packet Inspection) - многоуровневая защита

© 2026 VPN Client Aggregator
"""

import random
import time
import socket
import struct
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DPIBypassMethod(Enum):
    """Методы обхода DPI"""
    FRAGMENTATION = "fragmentation"
    PADDING = "padding"
    TLS_MIMICRY = "tls_mimicry"
    DOMAIN_FRONTING = "domain_fronting"
    OBFUSCATION = "obfuscation"


@dataclass
class FragmentConfig:
    """Конфигурация фрагментации пакетов"""
    enabled: bool = True
    size_min: int = 50      # минимальный размер фрагмента (байт)
    size_max: int = 200     # максимальный размер фрагмента (байт)
    interval_min: int = 10  # минимальный интервал между фрагментами (мс)
    interval_max: int = 50  # максимальный интервал между фрагментами (мс)


@dataclass
class PaddingConfig:
    """Конфигурация padding (добавление случайных данных)"""
    enabled: bool = True
    size_min: int = 100     # минимальный размер padding (байт)
    size_max: int = 500     # максимальный размер padding (байт)
    random_fill: bool = True  # использовать случайные байты


@dataclass
class TLSConfig:
    """Конфигурация TLS маскировки"""
    version: str = "TLS 1.3"
    fingerprint: str = "chrome"  # Chrome 120+
    alpn_protocols: List[str] = None
    server_names: List[str] = None
    
    def __post_init__(self):
        if self.alpn_protocols is None:
            self.alpn_protocols = ["h2", "http/1.1"]
        if self.server_names is None:
            self.server_names = [
                "google.com",
                "www.google.com",
                "www.microsoft.com",
                "cdn.cloudflare.com",
                "github.com",
                "www.amazon.com"
            ]


class DPIBypass:
    """
    Многоуровневая система обхода DPI (Deep Packet Inspection).
    
    Реализует следующие методы:
    1. Фрагментация пакетов - разделение на мелкие части
    2. Padding - добавление случайных данных для изменения размера
    3. TLS маскировка - имитация обычного HTTPS трафика
    4. Domain fronting - использование доверенных доменов
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация системы обхода DPI.
        
        Args:
            config: Конфигурация обхода DPI
        """
        self.config = config or self._default_config()
        
        # Инициализация компонентов
        self.fragment_config = FragmentConfig(
            enabled=self.config.get('fragment_packets', True),
            size_min=self.config.get('fragment_size_min', 50),
            size_max=self.config.get('fragment_size_max', 200),
            interval_min=self.config.get('fragment_interval_min', 10),
            interval_max=self.config.get('fragment_interval_max', 50)
        )
        
        self.padding_config = PaddingConfig(
            enabled=self.config.get('padding_enabled', True),
            size_min=self.config.get('padding_min', 100),
            size_max=self.config.get('padding_max', 500),
            random_fill=self.config.get('padding_random', True)
        )
        
        self.tls_config = TLSConfig(
            fingerprint=self.config.get('fingerprint', 'chrome'),
            alpn_protocols=self.config.get('alpn', ["h2", "http/1.1"]),
            server_names=self.config.get('server_names')
        )
        
        # Статистика
        self.stats = {
            'packets_fragmented': 0,
            'bytes_padded': 0,
            'tls_handshakes': 0,
            'detections_avoided': 0
        }
        
        # Внутренние состояния
        self._last_fragment_time = 0
        self._sequence_number = 0
    
    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def fragment_packet(self, data: bytes) -> List[bytes]:
        """
        Фрагментация пакета на мелкие части.
        
        Args:
            data: Исходные данные пакета
        
        Returns:
            Список фрагментов
        """
        if not self.fragment_config.enabled:
            return [data]
        
        fragments = []
        remaining = data
        
        while remaining:
            # Определение размера текущего фрагмента
            fragment_size = random.randint(
                self.fragment_config.size_min,
                min(self.fragment_config.size_max, len(remaining))
            )
            
            # Извлечение фрагмента
            fragment = remaining[:fragment_size]
            fragments.append(fragment)
            remaining = remaining[fragment_size:]
            
            # Обновление статистики
            self.stats['packets_fragmented'] += 1
        
        # Добавление интервалов между фрагментами
        if len(fragments) > 1 and self.fragment_config.interval_max > 0:
            self._apply_fragment_intervals()
        
        return fragments
    
    def add_padding(self, data: bytes) -> bytes:
        """
        Добавление padding (случайных данных) к пакету.
        
        Args:
            data: Исходные данные
        
        Returns:
            Данные с padding
        """
        if not self.padding_config.enabled:
            return data
        
        # Определение размера padding
        padding_size = random.randint(
            self.padding_config.size_min,
            self.padding_config.size_max
        )
        
        # Генерация padding
        if self.padding_config.random_fill:
            padding = bytes([random.randint(0, 255) for _ in range(padding_size)])
        else:
            padding = bytes([0x00] * padding_size)
        
        # Добавление padding
        padded_data = data + padding
        
        # Обновление статистики
        self.stats['bytes_padded'] += padding_size
        
        return padded_data
    
    def generate_tls_client_hello(self, server_name: Optional[str] = None) -> bytes:
        """
        Генерация TLS Client Hello для маскировки.
        
        Args:
            server_name: Доменное имя для SNI
        
        Returns:
            TLS Client Hello пакет
        """
        if server_name is None:
            server_name = random.choice(self.tls_config.server_names)
        
        # Обновление статистики
        self.stats['tls_handshakes'] += 1
        
        # Генерация TLS 1.3 Client Hello
        # Версия TLS 1.3 (0x0304)
        tls_version = b'\x03\x04'
        
        # Random (32 байта)
        random_bytes = self._generate_tls_random()
        
        # Session ID (0 байт для TLS 1.3)
        session_id = b'\x00'
        
        # Cipher Suites
        cipher_suites = self._get_tls13_cipher_suites()
        
        # Compression Methods
        compression_methods = b'\x01\x00'
        
        # Extensions
        extensions = self._generate_tls_extensions(server_name)
        
        # Сборка Client Hello
        client_hello = (
            tls_version +
            random_bytes +
            session_id +
            cipher_suites +
            compression_methods +
            extensions
        )
        
        # TLS Record Header
        record_type = b'\x16'  # Handshake
        record_version = b'\x03\x01'  # TLS 1.0 для совместимости
        length = struct.pack('>H', len(client_hello))
        
        return record_type + record_version + length + client_hello
    
    def apply_domain_fronting(self, target_domain: str) -> Tuple[str, str]:
        """
        Применение domain fronting.
        
        Args:
            target_domain: Целевой домен
        
        Returns:
            Кортеж (front_domain, target_domain)
        """
        front_domain = random.choice(self.tls_config.server_names)
        
        # Проверка что front_domain не совпадает с target
        while front_domain == target_domain:
            front_domain = random.choice(self.tls_config.server_names)
        
        return front_domain, target_domain
    
    def obfuscate_payload(self, data: bytes, method: str = 'xor') -> bytes:
        """
        Обфускация полезной нагрузки.
        
        Args:
            data: Исходные данные
            method: Метод обфускации ('xor', 'rotate', 'substitute')
        
        Returns:
            Обфусцированные данные
        """
        if method == 'xor':
            return self._xor_obfuscate(data)
        elif method == 'rotate':
            return self._rotate_obfuscate(data)
        elif method == 'substitute':
            return self._substitute_obfuscate(data)
        else:
            return data
    
    def get_xray_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации для Xray-core.
        
        Returns:
            Конфигурация обхода DPI для Xray
        """
        config = {
            "streamSettings": {
                "sockopt": {
                    "tcpNoDelay": True,
                    "tcpKeepAliveInterval": self.fragment_config.interval_min,
                    "tcpKeepAliveIdle": 300,
                    "mark": 255
                }
            }
        }
        
        # Fragment настройки (для версий Xray с поддержкой)
        if self.fragment_config.enabled:
            config["fragment"] = {
                "packets": True,
                "length": f"{self.fragment_config.size_min}-{self.fragment_config.size_max}",
                "interval": f"{self.fragment_config.interval_min}-{self.fragment_config.interval_max}"
            }
        
        return config
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики работы.
        
        Returns:
            Статистика
        """
        return {
            **self.stats,
            'fragment_enabled': self.fragment_config.enabled,
            'padding_enabled': self.padding_config.enabled,
            'tls_fingerprint': self.tls_config.fingerprint,
            'available_server_names': len(self.tls_config.server_names)
        }
    
    # ==========================================================================
    ПРИВАТНЫЕ МЕТОДЫ
    # ==========================================================================
    
    def _default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'fragment_packets': True,
            'fragment_size_min': 50,
            'fragment_size_max': 200,
            'fragment_interval_min': 10,
            'fragment_interval_max': 50,
            'padding_enabled': True,
            'padding_min': 100,
            'padding_max': 500,
            'padding_random': True,
            'fingerprint': 'chrome',
            'alpn': ['h2', 'http/1.1'],
            'server_names': None
        }
    
    def _generate_tls_random(self) -> bytes:
        """Генерация случайных байтов для TLS"""
        # GMT Unix time (4 байта)
        gmt_time = struct.pack('>I', int(time.time()))
        
        # Random bytes (28 байт)
        random_bytes = bytes([random.randint(0, 255) for _ in range(28)])
        
        return gmt_time + random_bytes
    
    def _get_tls13_cipher_suites(self) -> bytes:
        """Получение списка шифров TLS 1.3"""
        # TLS 1.3 cipher suites
        ciphers = [
            b'\x13\x01',  # TLS_AES_128_GCM_SHA256
            b'\x13\x02',  # TLS_AES_256_GCM_SHA384
            b'\x13\x03',  # TLS_CHACHA20_POLY1305_SHA256
        ]
        
        length = struct.pack('>H', len(ciphers) * 2)
        return length + b''.join(ciphers)
    
    def _generate_tls_extensions(self, server_name: str) -> bytes:
        """Генерация TLS расширений"""
        extensions = []
        
        # SNI (Server Name Indication)
        sni_extension = self._create_sni_extension(server_name)
        extensions.append(sni_extension)
        
        # Supported Versions (TLS 1.3)
        versions_extension = self._create_supported_versions_extension()
        extensions.append(versions_extension)
        
        # Key Share
        key_share = self._create_key_share_extension()
        extensions.append(key_share)
        
        # Signature Algorithms
        sig_algs = self._create_signature_algorithms_extension()
        extensions.append(sig_algs)
        
        # PSK Key Exchange Modes
        psk_modes = self._create_psk_modes_extension()
        extensions.append(psk_modes)
        
        # Сборка всех расширений
        extensions_data = b''.join(extensions)
        extensions_length = struct.pack('>H', len(extensions_data))
        
        return extensions_length + extensions_data
    
    def _create_sni_extension(self, server_name: str) -> bytes:
        """Создание SNI расширения"""
        # Extension type: server_name (0x0000)
        ext_type = b'\x00\x00'
        
        # Server name list
        name_bytes = server_name.encode('utf-8')
        name_length = struct.pack('>H', len(name_bytes))
        
        # Host name (type 0x00)
        hostname = b'\x00' + name_length + name_bytes
        hostname_list_length = struct.pack('>H', len(hostname))
        
        # Extension length
        ext_length = struct.pack('>H', len(hostname_list_length) + len(hostname))
        
        return ext_type + ext_length + hostname_list_length + hostname
    
    def _create_supported_versions_extension(self) -> bytes:
        """Создание расширения поддерживаемых версий"""
        # Extension type: supported_versions (0x002b)
        ext_type = b'\x00\x2b'
        
        # TLS 1.2 и TLS 1.3
        versions = b'\x04\x03\x04\x03\x03'  # length + TLS 1.3 + TLS 1.2
        
        # Extension length
        ext_length = struct.pack('>H', len(versions))
        
        return ext_type + ext_length + versions
    
    def _create_key_share_extension(self) -> bytes:
        """Создание расширения Key Share"""
        # Extension type: key_share (0x0033)
        ext_type = b'\x00\x33'
        
        # X25519 key share (32 байта публичный ключ + 2 байта тип)
        key_type = b'\x00\x1d'  # X25519
        public_key = bytes([random.randint(0, 255) for _ in range(32)])
        key_exchange = key_type + struct.pack('>H', len(public_key)) + public_key
        
        # Client share
        client_share_length = struct.pack('>H', len(key_exchange))
        client_share = client_share_length + key_exchange
        
        # Extension length
        ext_length = struct.pack('>H', len(client_share))
        
        return ext_type + ext_length + client_share
    
    def _create_signature_algorithms_extension(self) -> bytes:
        """Создание расширения алгоритмов подписи"""
        # Extension type: signature_algorithms (0x000d)
        ext_type = b'\x00\x0d'
        
        # Signature algorithms
        algorithms = [
            b'\x04\x03',  # ecdsa_secp256r1_sha256
            b'\x05\x03',  # ecdsa_secp384r1_sha384
            b'\x06\x03',  # ecdsa_secp521r1_sha512
            b'\x04\x01',  # rsa_pss_rsae_sha256
            b'\x05\x01',  # rsa_pss_rsae_sha384
            b'\x06\x01',  # rsa_pss_rsae_sha512
            b'\x02\x01',  # rsa_pkcs1_sha1
            b'\x02\x03',  # ecdsa_sha1
        ]
        
        algorithms_data = b''.join(algorithms)
        algorithms_length = struct.pack('>H', len(algorithms_data))
        
        # Extension length
        ext_length = struct.pack('>H', len(algorithms_length) + len(algorithms_data))
        
        return ext_type + ext_length + algorithms_length + algorithms_data
    
    def _create_psk_modes_extension(self) -> bytes:
        """Создание расширения PSK modes"""
        # Extension type: psk_key_exchange_modes (0x002d)
        ext_type = b'\x00\x2d'
        
        # PSK modes: PSK with (EC)DHE key establishment
        modes = b'\x01\x01'  # length + psk_dhe_ke
        
        # Extension length
        ext_length = struct.pack('>H', len(modes))
        
        return ext_type + ext_length + modes
    
    def _xor_obfuscate(self, data: bytes) -> bytes:
        """XOR обфускация"""
        key = random.randint(1, 255)
        return bytes([b ^ key for b in data])
    
    def _rotate_obfuscate(self, data: bytes) -> bytes:
        """ROT обфускация"""
        rotation = random.randint(1, 25)
        return bytes([(b + rotation) % 256 for b in data])
    
    def _substitute_obfuscate(self, data: bytes) -> bytes:
        """Substitution обфускация"""
        # Простая замена байтов
        substitution_table = bytes([random.randint(0, 255) for _ in range(256)])
        return bytes([substitution_table[b] for b in data])
    
    def _apply_fragment_intervals(self):
        """Применение интервалов между фрагментами"""
        current_time = time.time()
        elapsed = (current_time - self._last_fragment_time) * 1000  # мс
        
        min_interval = self.fragment_config.interval_min
        
        if elapsed < min_interval:
            sleep_time = (min_interval - elapsed) / 1000
            time.sleep(sleep_time)
        
        self._last_fragment_time = time.time()
    
    def _increment_sequence(self) -> int:
        """Инкремент номера последовательности"""
        self._sequence_number = (self._sequence_number + 1) % 65536
        return self._sequence_number


# =============================================================================
# ТОЧКА ВХОДА ДЛЯ ТЕСТИРОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("🔧 Тестирование DPIBypass...")
    
    # Создание экземпляра
    dpi_bypass = DPIBypass({
        'fragment_packets': True,
        'fragment_size_min': 50,
        'fragment_size_max': 150,
        'padding_enabled': True,
        'padding_min': 50,
        'padding_max': 200,
        'fingerprint': 'chrome'
    })
    
    # Тест фрагментации
    test_data = b"Hello, World! This is a test packet for DPI bypass testing." * 10
    print(f"\n📦 Исходные данные: {len(test_data)} байт")
    
    fragments = dpi_bypass.fragment_packet(test_data)
    print(f"✅ Фрагментация: {len(fragments)} фрагментов")
    for i, frag in enumerate(fragments[:3]):
        print(f"   Фрагмент {i+1}: {len(frag)} байт")
    if len(fragments) > 3:
        print(f"   ... и ещё {len(fragments) - 3} фрагментов")
    
    # Тест padding
    padded = dpi_bypass.add_padding(test_data)
    print(f"\n📦 Padding: {len(test_data)} → {len(padded)} байт")
    print(f"   Добавлено: {len(padded) - len(test_data)} байт")
    
    # Тест TLS Client Hello
    tls_hello = dpi_bypass.generate_tls_client_hello("google.com")
    print(f"\n🔐 TLS Client Hello: {len(tls_hello)} байт")
    print(f"   Версия: TLS 1.3")
    print(f"   Fingerprint: Chrome")
    
    # Тест Domain Fronting
    front, target = dpi_bypass.apply_domain_fronting("blocked-site.com")
    print(f"\n🎭 Domain Fronting:")
    print(f"   Front domain: {front}")
    print(f"   Target: {target}")
    
    # Статистика
    stats = dpi_bypass.get_stats()
    print(f"\n📊 Статистика:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Xray конфигурация
    xray_config = dpi_bypass.get_xray_config()
    print(f"\n⚙️ Xray конфигурация:")
    print(f"   {json.dumps(xray_config, indent=2)}")
    
    print("\n✅ DPIBypass готов к работе!")
