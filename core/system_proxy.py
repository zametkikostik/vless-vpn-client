#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Proxy Manager - Управление системным прокси
"""

import subprocess
import os
from typing import Optional


class SystemProxyManager:
    """Управление системными настройками прокси"""
    
    def __init__(self, socks_port: int = 10809, http_port: int = 10808):
        self.socks_port = socks_port
        self.http_port = http_port
        self.original_proxy: Optional[str] = None
    
    def enable_system_proxy(self) -> bool:
        """
        Включить системный прокси
        
        Returns:
            True если успешно
        """
        # Для GNOME
        try:
            # SOCKS прокси
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'manual'
            ], check=True)
            
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.socks', 'host', '127.0.0.1'
            ], check=True)
            
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.socks', 'port', str(self.socks_port)
            ], check=True)
            
            # HTTP прокси (для совместимости)
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'host', '127.0.0.1'
            ], check=True)
            
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'port', str(self.http_port)
            ], check=True)
            
            # HTTPS прокси
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.https', 'host', '127.0.0.1'
            ], check=True)
            
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.https', 'port', str(self.http_port)
            ], check=True)
            
            # Игнорировать локальные адреса
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'ignore-hosts',
                "['localhost', '127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']"
            ], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting GNOME proxy: {e}")
            return False
        except FileNotFoundError:
            print("gsettings not found - not a GNOME environment")
            return False
    
    def disable_system_proxy(self) -> bool:
        """
        Отключить системный прокси
        
        Returns:
            True если успешно
        """
        try:
            subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'none'
            ], check=True)
            return True
        except:
            return False
    
    def set_environment_proxy(self) -> None:
        """Установить переменные окружения прокси"""
        os.environ['http_proxy'] = f'http://127.0.0.1:{self.http_port}'
        os.environ['https_proxy'] = f'http://127.0.0.1:{self.http_port}'
        os.environ['socks_proxy'] = f'socks5://127.0.0.1:{self.socks_port}'
        os.environ['all_proxy'] = f'socks5://127.0.0.1:{self.socks_port}'
    
    def unset_environment_proxy(self) -> None:
        """Убрать переменные окружения прокси"""
        for var in ['http_proxy', 'https_proxy', 'socks_proxy', 'all_proxy']:
            os.environ.pop(var, None)
            os.environ.pop(var.upper(), None)
    
    def enable_firefox_proxy(self) -> bool:
        """
        Настроить прокси для Firefox
        
        Returns:
            True если успешно
        """
        # Firefox хранит настройки в prefs.js
        # Это требует перезапуска Firefox
        firefox_profiles = [
            os.path.expanduser('~/.mozilla/firefox'),
            os.path.expanduser('~/.var/app/org.mozilla.firefox/.mozilla/firefox')
        ]
        
        for profile_dir in firefox_profiles:
            if not os.path.exists(profile_dir):
                continue
            
            try:
                for entry in os.listdir(profile_dir):
                    if entry.endswith('.default-release') or entry.endswith('.default'):
                        prefs_file = os.path.join(profile_dir, entry, 'prefs.js')
                        if os.path.exists(prefs_file):
                            self._modify_firefox_prefs(prefs_file)
                            return True
            except Exception as e:
                print(f"Error configuring Firefox: {e}")
        
        return False
    
    def _modify_firefox_prefs(self, prefs_file: str) -> None:
        """Изменить файл prefs.js Firefox"""
        proxy_settings = f"""
user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "127.0.0.1");
user_pref("network.proxy.socks_port", {self.socks_port});
user_pref("network.proxy.socks_version", 5);
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.proxy.no_proxies_on", "localhost, 127.0.0.1");
"""
        
        try:
            # Читаем существующие настройки
            with open(prefs_file, 'r') as f:
                content = f.read()
            
            # Удаляем старые настройки прокси
            lines = content.split('\n')
            new_lines = [
                line for line in lines 
                if not line.startswith('user_pref("network.proxy')
            ]
            
            # Добавляем новые
            new_content = '\n'.join(new_lines) + proxy_settings
            
            with open(prefs_file, 'w') as f:
                f.write(new_content)
                
        except Exception as e:
            print(f"Error modifying Firefox prefs: {e}")
