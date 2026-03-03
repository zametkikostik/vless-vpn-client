#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Manager - Загрузка и проверка серверов
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Callable
from core.config_parser import ConfigParser
from core.config_manager import ConfigManager


class ServerManager:
    """Менеджер серверов - загрузка, проверка, сортировка"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.parser = ConfigParser()
        self.servers: List[Dict] = []
        self.is_loading = False
    
    async def load_from_sources(self) -> List[Dict]:
        """
        Загрузка серверов из всех источников
        
        Returns:
            Список серверов
        """
        self.is_loading = True
        all_servers = []
        
        sources = self.config.get_sources()
        
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_source(session, source) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_servers.extend(result)
        
        # Убираем дубликаты
        seen = set()
        unique_servers = []
        for server in all_servers:
            key = f"{server['host']}:{server['port']}"
            if key not in seen:
                seen.add(key)
                unique_servers.append(server)
        
        self.servers = unique_servers
        self.is_loading = False
        
        return unique_servers
    
    async def _fetch_source(self, session: aiohttp.ClientSession, source: Dict) -> List[Dict]:
        """Загрузка из одного источника"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(source['url'], timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    servers = self.parser.parse_subscription(content)
                    print(f"Loaded {len(servers)} servers from {source['name']}")
                    return servers
                else:
                    print(f"Error fetching {source['name']}: HTTP {response.status}")
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")

        return []
    
    async def check_servers(
        self, 
        servers: Optional[List[Dict]] = None,
        max_concurrent: int = 20,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Проверка доступности серверов
        
        Args:
            servers: Список серверов для проверки
            max_concurrent: Максимальное количество одновременных проверок
            progress_callback: Callback для обновления прогресса
        
        Returns:
            Список серверов с ping
        """
        if servers is None:
            servers = self.servers
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_single(server: Dict) -> Dict:
            async with semaphore:
                ping = await self._check_ping(server)
                server['ping'] = ping
                server['last_check'] = time.time()
                
                if progress_callback:
                    progress_callback(len([s for s in servers if s.get('ping') is not None]), len(servers))
                
                return server
        
        tasks = [check_single(server) for server in servers]
        results = await asyncio.gather(*tasks)
        
        # Сортируем по ping (рабочие сначала)
        working = [s for s in results if s.get('ping') is not None]
        not_working = [s for s in results if s.get('ping') is None]
        
        working.sort(key=lambda x: x['ping'])
        
        return working + not_working
    
    async def _check_ping(self, server: Dict) -> Optional[float]:
        """
        Проверка пинга сервера
        
        Args:
            server: Конфигурация сервера
        
        Returns:
            Ping в мс или None если недоступен
        """
        # Простая проверка через HTTP запрос к серверу
        # В реальности нужно проверять через Xray
        
        timeout = aiohttp.ClientTimeout(total=5)
        
        try:
            # Для Reality/TLS серверов пробуем HTTPS
            if server.get('security') in ['tls', 'reality']:
                url = f"https://{server['host']}:{server['port']}"
            else:
                url = f"http://{server['host']}:{server['port']}"
            
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(url, timeout=timeout, ssl=False) as response:
                    elapsed = (time.time() - start) * 1000
                    # Даже если 404 - сервер доступен
                    return round(elapsed, 2)
        except:
            pass
        
        # Альтернативная проверка - просто TCP соединение
        try:
            start = time.time()
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(server['host'], server['port']),
                timeout=5.0
            )
            elapsed = (time.time() - start) * 1000
            writer.close()
            await writer.wait_closed()
            return round(elapsed, 2)
        except:
            return None
    
    def get_best_server(self, min_ping: float = 1000) -> Optional[Dict]:
        """
        Получить лучший сервер
        
        Args:
            min_ping: Максимально допустимый ping
        
        Returns:
            Конфигурация лучшего сервера или None
        """
        working = [s for s in self.servers if s.get('ping') is not None and s['ping'] < min_ping]
        
        if not working:
            return None
        
        # Сортируем по ping
        working.sort(key=lambda x: x['ping'])
        
        return working[0]
    
    def get_servers_by_country(self, country: str) -> List[Dict]:
        """Получить серверы по стране"""
        return [s for s in self.servers if s.get('country', '').lower() == country.lower()]
    
    def get_servers_by_protocol(self, protocol: str) -> List[Dict]:
        """Получить серверы по протоколу"""
        return [s for s in self.servers if s.get('protocol', '').lower() == protocol.lower()]
    
    def save_servers(self, filepath: str) -> bool:
        """Сохранить серверы в файл"""
        import json
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving servers: {e}")
            return False
    
    def load_servers(self, filepath: str) -> bool:
        """Загрузить серверы из файла"""
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.servers = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading servers: {e}")
            return False
