#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Parser - Парсинг VLESS/VMess/Trojan конфигураций
"""

import re
import json
import base64
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs, unquote


class ConfigParser:
    """Парсер конфигураций VPN"""
    
    # Паттерны для различных протоколов
    PROTOCOL_PATTERNS = {
        'vless': r'^vless://',
        'vmess': r'^vmess://',
        'trojan': r'^trojan://',
        'ss': r'^ss://',
        'ssr': r'^ssr://'
    }
    
    def __init__(self):
        self.servers: List[Dict[str, Any]] = []
    
    def parse_subscription(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсинг подписки (base64 или список ссылок)

        Args:
            content: Содержимое подписки

        Returns:
            Список серверов
        """
        servers = []
        
        # Проверяем пустой контент
        if not content or len(content.strip()) < 10:
            return servers

        # Пробуем декодировать как base64
        try:
            # Проверяем, похож ли контент на base64
            content_clean = content.strip()
            if len(content_clean) > 100 and not '\n' in content_clean[:50]:
                # Возможно это base64
                try:
                    decoded = base64.b64decode(content_clean).decode('utf-8')
                    lines = decoded.strip().split('\n')
                except:
                    lines = content_clean.split('\n')
            else:
                lines = content_clean.split('\n')
        except:
            lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            server = self.parse_link(line)
            if server:
                servers.append(server)

        return servers
    
    def parse_link(self, link: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг отдельной ссылки
        
        Args:
            link: Ссылка вида protocol://...
        
        Returns:
            Конфигурация сервера или None
        """
        link = link.strip()
        
        if not link:
            return None
        
        # Определяем протокол
        protocol = None
        for proto, pattern in self.PROTOCOL_PATTERNS.items():
            if re.match(pattern, link, re.IGNORECASE):
                protocol = proto
                break
        
        if not protocol:
            return None
        
        # Парсим в зависимости от протокола
        parsers = {
            'vless': self._parse_vless,
            'vmess': self._parse_vmess,
            'trojan': self._parse_trojan,
            'ss': self._parse_shadowsocks,
            'ssr': self._parse_shadowsocksr
        }
        
        parser = parsers.get(protocol)
        if parser:
            return parser(link)
        
        return None
    
    def _parse_vless(self, link: str) -> Optional[Dict[str, Any]]:
        """Парсинг VLESS ссылки"""
        try:
            # vless://uuid@host:port?params#name
            parsed = urlparse(link)
            
            uuid = parsed.username or ''
            host = parsed.hostname or ''
            port = parsed.port or 443
            
            params = parse_qs(parsed.query)
            
            # Извлекаем параметры
            security = params.get('security', ['none'])[0]
            flow = params.get('flow', [''])[0]
            pbk = params.get('pbk', [''])[0]
            fp = params.get('fp', ['chrome'])[0]
            sni = params.get('sni', [host])[0]
            alpn = params.get('alpn', ['h2,http/1.1'])[0]
            path = params.get('path', ['/'])[0]
            host_header = params.get('host', [host])[0]
            type_ = params.get('type', ['tcp'])[0]
            
            name = unquote(parsed.fragment) if parsed.fragment else f"{host}:{port}"
            
            return {
                'protocol': 'vless',
                'name': name,
                'host': host,
                'port': port,
                'uuid': uuid,
                'security': security,
                'flow': flow,
                'pbk': pbk,
                'fp': fp,
                'sni': sni,
                'alpn': alpn,
                'path': path,
                'host_header': host_header,
                'type': type_,
                'raw_link': link
            }
        except Exception as e:
            print(f"Error parsing VLESS: {e}")
            return None
    
    def _parse_vmess(self, link: str) -> Optional[Dict[str, Any]]:
        """Парсинг VMess ссылки"""
        try:
            # vmess://base64(json)
            encoded = link[8:]  # Убираем 'vmess://'
            
            # Добавляем паддинг если нужно
            padding = 4 - (len(encoded) % 4)
            if padding != 4:
                encoded += '=' * padding
            
            decoded = base64.b64decode(encoded).decode('utf-8')
            config = json.loads(decoded)
            
            return {
                'protocol': 'vmess',
                'name': config.get('ps', f"{config.get('add', 'unknown')}:{config.get('port', '443')}"),
                'host': config.get('add', ''),
                'port': int(config.get('port', 443)),
                'uuid': config.get('id', ''),
                'alter_id': int(config.get('aid', 0)),
                'security': config.get('scy', 'auto'),
                'type': config.get('net', 'tcp'),
                'path': config.get('path', '/'),
                'host_header': config.get('host', ''),
                'tls': config.get('tls', ''),
                'sni': config.get('sni', ''),
                'alpn': config.get('alpn', ''),
                'fp': config.get('fp', 'chrome'),
                'raw_link': link
            }
        except Exception as e:
            print(f"Error parsing VMess: {e}")
            return None
    
    def _parse_trojan(self, link: str) -> Optional[Dict[str, Any]]:
        """Парсинг Trojan ссылки"""
        try:
            # trojan://password@host:port?params#name
            parsed = urlparse(link)
            
            password = parsed.username or ''
            host = parsed.hostname or ''
            port = parsed.port or 443
            
            params = parse_qs(parsed.query)
            
            security = params.get('security', ['tls'])[0]
            sni = params.get('sni', [host])[0]
            alpn = params.get('alpn', ['h2,http/1.1'])[0]
            type_ = params.get('type', ['tcp'])[0]
            path = params.get('path', ['/'])[0]
            
            name = unquote(parsed.fragment) if parsed.fragment else f"{host}:{port}"
            
            return {
                'protocol': 'trojan',
                'name': name,
                'host': host,
                'port': port,
                'password': password,
                'security': security,
                'sni': sni,
                'alpn': alpn,
                'type': type_,
                'path': path,
                'raw_link': link
            }
        except Exception as e:
            print(f"Error parsing Trojan: {e}")
            return None
    
    def _parse_shadowsocks(self, link: str) -> Optional[Dict[str, Any]]:
        """Парсинг Shadowsocks ссылки"""
        try:
            # ss://base64(method:password@host:port)#name
            # или ss://method:password@host:port#name
            parsed = urlparse(link)
            
            host = parsed.hostname or ''
            port = parsed.port or 443
            
            # Пробуем разные форматы
            try:
                # Формат с base64
                decoded = base64.b64decode(parsed.netloc.split('@')[0]).decode('utf-8')
                method, rest = decoded.split(':', 1)
                password = rest.split('@')[0]
            except:
                # Прямой формат
                method = parsed.username or ''
                password = parsed.password or ''
            
            name = unquote(parsed.fragment) if parsed.fragment else f"{host}:{port}"
            
            return {
                'protocol': 'ss',
                'name': name,
                'host': host,
                'port': port,
                'method': method,
                'password': password,
                'raw_link': link
            }
        except Exception as e:
            print(f"Error parsing Shadowsocks: {e}")
            return None
    
    def _parse_shadowsocksr(self, link: str) -> Optional[Dict[str, Any]]:
        """Парсинг ShadowsocksR ссылки"""
        # Упрощённая реализация
        try:
            encoded = link[6:]  # Убираем 'ssr://'
            decoded = base64.b64decode(encoded).decode('utf-8')
            
            parts = decoded.split('/?')
            main_part = parts[0]
            params = parse_qs(parts[1]) if len(parts) > 1 else {}
            
            main_parts = main_part.split(':')
            if len(main_parts) >= 5:
                host = main_parts[0]
                port = main_parts[1]
                protocol = main_parts[2]
                method = main_parts[3]
                obfs = main_parts[4]
                password = base64.b64decode(main_parts[5]).decode('utf-8') if len(main_parts) > 5 else ''
                
                return {
                    'protocol': 'ssr',
                    'name': f"{host}:{port}",
                    'host': host,
                    'port': int(port),
                    'protocol': protocol,
                    'method': method,
                    'obfs': obfs,
                    'password': password,
                    'raw_link': link
                }
        except Exception as e:
            print(f"Error parsing SSR: {e}")
        
        return None
    
    def validate_server(self, server: Dict[str, Any]) -> bool:
        """Проверка валидности сервера"""
        required_fields = ['protocol', 'host', 'port']
        return all(field in server for field in required_fields)
    
    def to_xray_config(self, server: Dict[str, Any], outbound_tag: str = "proxy") -> Dict:
        """
        Конвертация сервера в формат конфигурации Xray
        
        Args:
            server: Конфигурация сервера
            outbound_tag: Тег для outbound
        
        Returns:
            Конфигурация outbound для Xray
        """
        protocol = server.get('protocol', 'vless')
        
        if protocol == 'vless':
            return self._vless_to_xray(server, outbound_tag)
        elif protocol == 'vmess':
            return self._vmess_to_xray(server, outbound_tag)
        elif protocol == 'trojan':
            return self._trojan_to_xray(server, outbound_tag)
        elif protocol in ['ss', 'ssr']:
            return self._ss_to_xray(server, outbound_tag)
        
        return {}
    
    def _vless_to_xray(self, server: Dict, tag: str) -> Dict:
        """VLESS -> Xray config"""
        settings = {
            "vnext": [{
                "address": server['host'],
                "port": server['port'],
                "users": [{
                    "id": server['uuid'],
                    "encryption": "none",
                    "flow": server.get('flow', '')
                }]
            }]
        }
        
        stream_settings = self._build_stream_settings(server)
        
        return {
            "tag": tag,
            "protocol": "vless",
            "settings": settings,
            "streamSettings": stream_settings
        }
    
    def _vmess_to_xray(self, server: Dict, tag: str) -> Dict:
        """VMess -> Xray config"""
        settings = {
            "vnext": [{
                "address": server['host'],
                "port": server['port'],
                "users": [{
                    "id": server['uuid'],
                    "alterId": server.get('alter_id', 0),
                    "security": server.get('security', 'auto')
                }]
            }]
        }
        
        stream_settings = self._build_stream_settings(server)
        
        return {
            "tag": tag,
            "protocol": "vmess",
            "settings": settings,
            "streamSettings": stream_settings
        }
    
    def _trojan_to_xray(self, server: Dict, tag: str) -> Dict:
        """Trojan -> Xray config"""
        settings = {
            "servers": [{
                "address": server['host'],
                "port": server['port'],
                "password": server['password'],
                "level": 0
            }]
        }
        
        stream_settings = self._build_stream_settings(server)
        
        return {
            "tag": tag,
            "protocol": "trojan",
            "settings": settings,
            "streamSettings": stream_settings
        }
    
    def _ss_to_xray(self, server: Dict, tag: str) -> Dict:
        """Shadowsocks -> Xray config"""
        settings = {
            "servers": [{
                "address": server['host'],
                "port": server['port'],
                "method": server['method'],
                "password": server['password'],
                "level": 0
            }]
        }
        
        return {
            "tag": tag,
            "protocol": "shadowsocks",
            "settings": settings
        }
    
    def _build_stream_settings(self, server: Dict) -> Dict:
        """Построение stream settings"""
        stream = {
            "network": server.get('type', 'tcp'),
            "security": server.get('security', 'none')
        }
        
        # TLS/Reality settings
        if server.get('security') in ['tls', 'reality']:
            tls_settings = {
                "serverName": server.get('sni', server.get('host', '')),
                "alpn": server.get('alpn', 'h2,http/1.1').split(','),
                "fingerprint": server.get('fp', 'chrome')
            }
            
            if server.get('security') == 'reality' and server.get('pbk'):
                tls_settings["realitySettings"] = {
                    "publicKey": server['pbk'],
                    "serverName": server.get('sni', server.get('host', ''))
                }
            
            stream["tlsSettings"] = tls_settings
        
        # Transport settings
        network = server.get('type', 'tcp')
        if network == 'ws':
            stream["wsSettings"] = {
                "path": server.get('path', '/'),
                "headers": {
                    "Host": server.get('host_header', server.get('host', ''))
                }
            }
        elif network == 'grpc':
            stream["grpcSettings"] = {
                "serviceName": server.get('path', '')
            }
        elif network == 'h2':
            stream["httpSettings"] = {
                "path": server.get('path', '/'),
                "host": [server.get('host_header', server.get('host', ''))]
            }
        
        return stream
