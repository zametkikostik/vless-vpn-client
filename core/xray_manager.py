#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xray Manager - Управление Xray-core
"""

import subprocess
import json
import os
import signal
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from core.config_manager import ConfigManager
from core.config_parser import ConfigParser


class XrayManager:
    """Менеджер для управления Xray-core"""
    
    # Пути по умолчанию
    DEFAULT_XRAY_PATHS = [
        "/usr/bin/xray",
        "/usr/local/bin/xray",
        "/usr/bin/xray-core",
        "xray",  # В PATH
    ]
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.parser = ConfigParser()
        self.xray_path: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None
        self.config_file: Optional[Path] = None
        self.is_running = False
    
    def find_xray(self) -> Optional[str]:
        """Найти исполняемый файл xray"""
        for path in self.DEFAULT_XRAY_PATHS:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                self.xray_path = path
                return path
        
        # Пробуем найти через which
        try:
            result = subprocess.run(
                ['which', 'xray'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                self.xray_path = result.stdout.strip()
                return self.xray_path
        except:
            pass
        
        return None
    
    def generate_config(
        self,
        server: Dict[str, Any],
        routing_config: Optional[Dict] = None,
        anti_dpi: bool = True
    ) -> Dict:
        """
        Генерация полной конфигурации Xray
        
        Args:
            server: Конфигурация сервера
            routing_config: Настройки маршрутизации
            anti_dpi: Включить Anti-DPI
        
        Returns:
            Полная конфигурация Xray
        """
        # Outbound (прокси)
        outbound = self.parser.to_xray_config(server, "proxy")
        
        # Добавляем Anti-DPI настройки
        if anti_dpi:
            self._apply_anti_dpi(outbound)
        
        # Direct outbound (для прямых соединений)
        direct_outbound = {
            "tag": "direct",
            "protocol": "freedom",
            "settings": {
                "domainStrategy": "AsIs"
            }
        }
        
        # Block outbound
        block_outbound = {
            "tag": "block",
            "protocol": "blackhole",
            "settings": {
                "response": {
                    "type": "http"
                }
            }
        }
        
        # Inbound (локальный прокси)
        socks_port = self.config.get('socks_port', 10809)
        http_port = self.config.get('proxy_port', 10808)
        
        inbounds = [
            {
                "tag": "socks",
                "port": socks_port,
                "protocol": "socks",
                "settings": {
                    "auth": "noauth",
                    "udp": True
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls", "quic"]
                }
            },
            {
                "tag": "http",
                "port": http_port,
                "protocol": "http",
                "settings": {
                    "allowTransparent": False
                }
            }
        ]
        
        # Маршрутизация
        routing = self._generate_routing(routing_config)
        
        # DNS
        dns = {
            "servers": [
                {
                    "address": "https://dns.google/dns-query",
                    "domains": ["geosite:google"],
                    "expectIPs": ["geoip:us", "geoip:ca"]
                },
                {
                    "address": "https://dns.cloudflare.com/dns-query",
                    "domains": ["geosite:cloudflare"]
                },
                "1.1.1.1",
                "8.8.8.8"
            ],
            "tag": "dns"
        }
        
        # Логирование
        log_config = {
            "loglevel": "warning",
            "access": "/dev/null",
            "error": "/dev/null"
        }
        
        # API для статистики
        api = {
            "tag": "api",
            "services": ["StatsService"],
            "tag": "api"
        }
        
        # Статистика
        stats = {}
        
        config = {
            "log": log_config,
            "inbounds": inbounds,
            "outbounds": [outbound, direct_outbound, block_outbound],
            "routing": routing,
            "dns": dns,
            "stats": stats,
            "api": api
        }
        
        return config
    
    def _apply_anti_dpi(self, outbound: Dict) -> None:
        """Применить Anti-DPI настройки"""
        stream = outbound.get('streamSettings', {})
        
        # uTLS fingerprint
        tls_settings = stream.get('tlsSettings', {}) or stream.get('realitySettings', {})
        tls_settings['fingerprint'] = 'chrome'
        
        # Добавляем padding для WS
        if stream.get('network') == 'ws':
            ws_settings = stream.get('wsSettings', {})
            # Можно добавить кастомные заголовки
            headers = ws_settings.get('headers', {})
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ws_settings['headers'] = headers
        
        # Mux (multiplexing)
        outbound['mux'] = {
            "enabled": True,
            "concurrency": 8,
            "xudpConcurrency": 16,
            "xudpProxyUDP443": "reject"
        }
    
    def _generate_routing(self, routing_config: Optional[Dict] = None) -> Dict:
        """Генерация правил маршрутизации"""
        rules = []
        
        # DNS правила
        rules.append({
            "type": "field",
            "inboundTag": ["dns"],
            "outboundTag": "dns"
        })
        
        if routing_config and routing_config.get('smart_routing', True):
            # Российские домены и IP - напрямую
            rules.append({
                "type": "field",
                "domain": [
                    "geosite:category-ru",
                    "domain:.ru",
                    "domain:.рф",
                    "domain:.su"
                ],
                "outboundTag": "direct"
            })
            
            rules.append({
                "type": "field",
                "ip": [
                    "geoip:ru",
                    "geoip:private"
                ],
                "outboundTag": "direct"
            })
            
            # Заблокированные сервисы - через прокси
            blocked = routing_config.get('blocked_services', [])
            if blocked:
                rules.append({
                    "type": "field",
                    "domain": blocked,
                    "outboundTag": "proxy"
                })
            
            # YouTube, Instagram, Facebook и т.д.
            rules.append({
                "type": "field",
                "domain": [
                    "geosite:youtube",
                    "geosite:instagram",
                    "geosite:facebook",
                    "geosite:twitter",
                    "geosite:openai",
                    "geosite:tiktok"
                ],
                "outboundTag": "proxy"
            })
        
        # Всё остальное - через прокси
        rules.append({
            "type": "field",
            "network": "tcp,udp",
            "outboundTag": "proxy"
        })
        
        return {
            "domainStrategy": "IPIfNonMatch",
            "rules": rules
        }
    
    def save_config(self, config: Dict, filepath: Optional[str] = None) -> Path:
        """Сохранить конфигурацию в файл"""
        if filepath:
            config_path = Path(filepath)
        else:
            config_dir = Path.home() / ".anticensor"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.json"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.config_file = config_path
        return config_path
    
    def start(self, config: Optional[Dict] = None) -> bool:
        """
        Запустить Xray
        
        Args:
            config: Конфигурация (если None, используется сохранённая)
        
        Returns:
            True если успешно
        """
        if not self.xray_path:
            if not self.find_xray():
                print("Xray not found!")
                return False
        
        # Сохраняем конфигурацию если предоставлена
        if config:
            self.save_config(config)
        
        if not self.config_file or not self.config_file.exists():
            print("Config file not found!")
            return False
        
        try:
            # Запускаем Xray
            self.process = subprocess.Popen(
                [self.xray_path, '-config', str(self.config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Ждём немного и проверяем процесс
            time.sleep(1)
            
            if self.process.poll() is None:
                self.is_running = True
                return True
            else:
                # Процесс завершился - читаем ошибку
                stderr = self.process.stderr.read().decode('utf-8')
                print(f"Xray failed to start: {stderr}")
                return False
                
        except Exception as e:
            print(f"Error starting Xray: {e}")
            return False
    
    def stop(self) -> bool:
        """Остановить Xray"""
        if not self.process:
            return True
        
        try:
            # Используем os.killpg для завершения всей группы процессов
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait(timeout=5)
            self.is_running = False
            self.process = None
            return True
        except Exception as e:
            print(f"Error stopping Xray: {e}")
            # Принудительное завершение
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except:
                pass
            return False
    
    def restart(self, config: Optional[Dict] = None) -> bool:
        """Перезапустить Xray"""
        self.stop()
        time.sleep(1)
        return self.start(config)
    
    def get_status(self) -> Dict:
        """Получить статус Xray"""
        if not self.is_running or not self.process:
            return {"status": "stopped", "pid": None}
        
        try:
            # Проверяем существует ли процесс
            self.process.poll()
            if self.process.returncode is not None:
                self.is_running = False
                return {"status": "crashed", "pid": self.process.pid, "code": self.process.returncode}
            
            return {
                "status": "running",
                "pid": self.process.pid,
                "config": str(self.config_file) if self.config_file else None
            }
        except:
            return {"status": "unknown", "pid": None}
