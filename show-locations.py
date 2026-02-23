#!/usr/bin/env python3
"""Показать доступные локации"""
import json
from pathlib import Path

SERVERS_FILE = Path.home() / "vpn-client" / "data" / "servers.json"

with open(SERVERS_FILE) as f:
    servers = json.load(f)

countries = {}
country_map = {
    "🇩🇪": "Germany", "Germany": "Germany",
    "🇳🇱": "Netherlands", "Netherlands": "Netherlands",
    "🇺🇸": "USA", "USA": "USA",
    "🇬🇧": "UK", "UK": "UK",
    "🇫🇷": "France", "France": "France",
    "🇪🇪": "Estonia", "Estonia": "Estonia",
    "🇧🇾": "Belarus", "Belarus": "Belarus",
    "🇵🇱": "Poland", "Poland": "Poland",
    "🇺🇦": "Ukraine", "Ukraine": "Ukraine",
    "🇰🇿": "Kazakhstan", "Kazakhstan": "Kazakhstan",
    "🇫🇮": "Finland", "Finland": "Finland",
    "🇸🇪": "Sweden", "Sweden": "Sweden",
    "🇳🇴": "Norway", "Norway": "Norway",
    "🇱🇻": "Latvia", "Latvia": "Latvia",
    "🇱🇹": "Lithuania", "Lithuania": "Lithuania",
    "🤖": "AI Services", "chatgpt.com": "AI Services", "claude.com": "AI Services",
}

for server in servers:
    if server.get("status") != "online":
        continue
    name = server.get("name", "")
    host = server.get("host", "")
    country = "🌍 Other"
    
    # Проверка на AI сервисы (claude.com, chatgpt.com, lovable.dev)
    if "claude" in name.lower() or "claude" in host.lower() or "claude.ai" in host.lower():
        country = "🤖 AI Services"
    elif "chatgpt" in name.lower() or "chatgpt" in host.lower():
        country = "🤖 AI Services"
    elif "lovable" in name.lower() or "lovable" in host.lower():
        country = "🤖 AI Services"
    else:
        for flag, cname in country_map.items():
            if flag in name or cname in name:
                country = f"{flag} {cname}"
                break
    if country not in countries:
        countries[country] = []
    countries[country].append({
        "host": server["host"],
        "port": server["port"],
        "latency": server.get("latency", 9999)
    })

countries = dict(sorted(countries.items(), key=lambda x: len(x[1]), reverse=True))

print("\n" + "=" * 60)
print("🌍 ДОСТУПНЫЕ ЛОКАЦИИ")
print("=" * 60)

for i, (country, servers_list) in enumerate(countries.items(), 1):
    servers_list.sort(key=lambda x: x["latency"])
    print(f"\n{i}. {country} ({len(servers_list)} серверов)")
    print(f"   Лучший: {servers_list[0]['host']}:{servers_list[0]['port']} - {servers_list[0]['latency']} мс")

print("\n" + "=" * 60)
print(f"\nВсего локаций: {len(countries)}")
print(f"Всего серверов онлайн: {sum(len(s) for s in countries.values())}")
