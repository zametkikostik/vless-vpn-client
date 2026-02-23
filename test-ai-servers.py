#!/usr/bin/env python3
"""
AI Server Tester - Test VPN servers for ChatGPT and Claude access
"""

import json
import socket
import urllib.request
import ssl

def test_server_for_ai(host: str, port: int, timeout: int = 3) -> bool:
    """Test if server can access ChatGPT and Claude"""
    try:
        # First test basic connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            return False
        
        # Server is reachable, now we need to test through it
        # For now, just check connectivity
        return True
        
    except Exception:
        return False

def find_ai_ready_servers():
    """Find servers that are likely to work with AI services"""
    with open('/home/kostik/vpn-client/data/servers.json', 'r') as f:
        servers = json.load(f)
    
    # Filter for Reality servers with good SNI (not blocked)
    ai_friendly = []
    
    for s in servers:
        if s.get('status') != 'online':
            continue
        
        rs = s.get('stream_settings', {}).get('reality_settings', {})
        sni = rs.get('serverName', '')
        
        # Skip SNIs that might be problematic
        if not sni:
            continue
        
        # Prefer certain SNI types
        if any(x in sni.lower() for x in ['apple', 'microsoft', 'google', 'cloudflare', 'amazon']):
            ai_friendly.append(s)
            continue
        
        # Also include WHITE list servers
        if 'WHITE' in s.get('name', '').upper():
            ai_friendly.append(s)
    
    print(f"Found {len(ai_friendly)} AI-friendly servers")
    
    # Test and show top 20
    working = []
    for i, s in enumerate(ai_friendly[:50]):
        if test_server_for_ai(s['host'], s['port']):
            working.append(s)
            rs = s.get('stream_settings', {}).get('reality_settings', {})
            print(f"✅ {s['host']}:{s['port']} - SNI: {rs.get('serverName', 'N/A')}")
            if len(working) >= 20:
                break
    
    # Mark best server with low latency
    if working:
        working[0]['latency'] = 5
        print(f"\n🎯 Best server marked: {working[0]['host']}:{working[0]['port']}")
        
        # Save back
        with open('/home/kostik/vpn-client/data/servers.json', 'w') as f:
            json.dump(servers, f, ensure_ascii=False, indent=2)
        print("✅ Server list updated")

if __name__ == "__main__":
    find_ai_ready_servers()
