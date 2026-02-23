#!/usr/bin/env python3
"""
VLESS VPN SaaS - Subscription Manager
Handles subscription URLs, auto-update, and node management.

© 2024 VPN Solutions Inc. All rights reserved.
"""

import base64
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import hashlib


@dataclass
class Subscription:
    """User subscription."""
    user_id: str
    subscription_id: str
    plan: str  # free, basic, pro, enterprise
    status: str  # active, cancelled, expired
    created_at: datetime
    expires_at: datetime
    nodes_limit: int = 1
    data_limit_gb: float = 1.0
    speed_limit_mbps: int = 10
    auto_renew: bool = False
    
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == "active" and datetime.now() < self.expires_at
    
    def get_limits(self) -> Dict[str, Any]:
        """Get subscription limits."""
        limits = {
            "free": {"nodes": 1, "data_gb": 1, "speed_mbps": 10},
            "basic": {"nodes": 5, "data_gb": -1, "speed_mbps": 100},
            "pro": {"nodes": 20, "data_gb": -1, "speed_mbps": 1000},
            "enterprise": {"nodes": -1, "data_gb": -1, "speed_mbps": 10000}
        }
        return limits.get(self.plan, limits["free"])


@dataclass
class VPNNode:
    """VPN node configuration."""
    id: str
    name: str
    country: str
    city: str
    host: str
    port: int
    protocol: str
    transport: str
    uuid: str
    server_name: str
    public_key: str
    short_id: str
    latency: int = 9999
    status: str = "online"
    last_check: Optional[datetime] = None


class SubscriptionManager:
    """
    Manage user subscriptions and auto-updating node lists.
    
    Features:
    - Subscription URL generation
    - Auto-update nodes from URL
    - Node health checking
    - Plan-based node filtering
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, Subscription] = {}
        self.nodes: Dict[str, VPNNode] = {}
        self.user_nodes: Dict[str, List[str]] = {}  # user_id -> node_ids
    
    def generate_subscription_url(self, user_id: str, token: str) -> str:
        """Generate subscription URL for user."""
        base_url = "https://api.vpn-saas.io/api/v1/subscribe"
        params = {
            "user": user_id,
            "token": token,
            "format": "vless"
        }
        
        query = urllib.parse.urlencode(params)
        return f"{base_url}?{query}"
    
    def parse_subscription_url(self, url: str) -> List[VPNNode]:
        """Parse subscription URL and extract nodes."""
        nodes = []
        
        try:
            # Fetch subscription data
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "VLESS-VPN-SaaS/3.0.0")
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8')
            
            # Try base64 decode (common format)
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                lines = decoded.strip().split('\n')
            except Exception:
                lines = content.strip().split('\n')
            
            # Parse VLESS URLs
            for line in lines:
                line = line.strip()
                if line.startswith('vless://'):
                    node = self._parse_vless_url(line)
                    if node:
                        nodes.append(node)
            
        except Exception as e:
            print(f"Failed to parse subscription URL: {e}")
        
        return nodes
    
    def _parse_vless_url(self, url: str) -> Optional[VPNNode]:
        """Parse VLESS URL into VPNNode."""
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            
            parsed = urlparse(url)
            
            # Extract fragment (node name)
            name = unquote(parsed.fragment) if parsed.fragment else "Unknown"
            
            # Extract UUID
            uuid = parsed.username or ""
            
            # Extract host and port
            host = parsed.hostname or ""
            port = parsed.port or 443
            
            if not uuid or not host:
                return None
            
            # Parse query parameters
            qs = parse_qs(parsed.query)
            params = {k: unquote(v[0]) if v else "" for k, v in qs.items()}
            
            # Extract Reality settings
            security = params.get('security', 'none')
            server_name = params.get('sni', host)
            public_key = params.get('pbk', '')
            short_id = params.get('sid', '')
            
            # Determine transport
            transport = params.get('type', 'tcp')
            if transport == 'ws':
                transport = 'websocket'
            
            # Generate node ID
            node_id = hashlib.md5(f"{host}:{port}".encode()).hexdigest()[:12]
            
            return VPNNode(
                id=node_id,
                name=name,
                country=self._detect_country(name),
                city="",
                host=host,
                port=port,
                protocol="vless",
                transport=transport if security == 'reality' else 'tcp',
                uuid=uuid,
                server_name=server_name,
                public_key=public_key,
                short_id=short_id
            )
            
        except Exception:
            return None
    
    def _detect_country(self, name: str) -> str:
        """Detect country from node name."""
        name_upper = name.upper()
        
        country_map = {
            "DE": "Germany", "DEU": "Germany", "GER": "Germany",
            "NL": "Netherlands", "NLD": "Netherlands", "AMS": "Netherlands",
            "US": "USA", "USA": "USA", "NY": "USA", "LA": "USA",
            "GB": "UK", "GBR": "UK", "LON": "UK",
            "FR": "France", "FRA": "France", "PAR": "France",
            "SG": "Singapore", "SGP": "Singapore",
            "JP": "Japan", "JPN": "Japan", "TYO": "Japan",
            "RU": "Russia", "RUS": "Russia", "MOW": "Russia",
        }
        
        for code, country in country_map.items():
            if code in name_upper:
                return country
        
        return "Unknown"
    
    def update_nodes(self, user_id: str, subscription_url: str) -> int:
        """Update nodes from subscription URL."""
        nodes = self.parse_subscription_url(subscription_url)
        
        if not nodes:
            return 0
        
        # Store nodes
        for node in nodes:
            self.nodes[node.id] = node
        
        # Associate with user
        if user_id not in self.user_nodes:
            self.user_nodes[user_id] = []
        
        self.user_nodes[user_id] = [node.id for node in nodes]
        
        return len(nodes)
    
    def get_nodes_for_user(self, user_id: str, subscription: Subscription) -> List[VPNNode]:
        """Get available nodes for user based on subscription plan."""
        if user_id not in self.user_nodes:
            return []
        
        limits = subscription.get_limits()
        node_ids = self.user_nodes[user_id]
        
        # Filter online nodes
        available_nodes = [
            self.nodes[nid] for nid in node_ids
            if nid in self.nodes and self.nodes[nid].status == "online"
        ]
        
        # Sort by latency
        available_nodes.sort(key=lambda n: n.latency)
        
        # Apply node limit
        if limits["nodes"] > 0:
            available_nodes = available_nodes[:limits["nodes"]]
        
        return available_nodes
    
    def check_node_health(self, node: VPNNode, timeout: int = 2) -> bool:
        """Check node health."""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((node.host, node.port))
            sock.close()
            
            is_healthy = result == 0
            node.status = "online" if is_healthy else "offline"
            node.last_check = datetime.now()
            
            return is_healthy
            
        except Exception:
            node.status = "offline"
            node.last_check = datetime.now()
            return False
    
    def health_check_all(self, user_id: str) -> Dict[str, bool]:
        """Health check all nodes for user."""
        results = {}
        
        if user_id not in self.user_nodes:
            return results
        
        for node_id in self.user_nodes[user_id]:
            if node_id in self.nodes:
                is_healthy = self.check_node_health(self.nodes[node_id])
                results[node_id] = is_healthy
        
        return results
    
    def create_subscription(self, user_id: str, plan: str, months: int = 1) -> Subscription:
        """Create new subscription."""
        now = datetime.now()
        expires = now + timedelta(days=30 * months)
        
        subscription = Subscription(
            user_id=user_id,
            subscription_id=f"sub_{hashlib.md5(f'{user_id}{now}'.encode()).hexdigest()[:12]}",
            plan=plan,
            status="active",
            created_at=now,
            expires_at=expires,
            auto_renew=True
        )
        
        self.subscriptions[user_id] = subscription
        return subscription
    
    def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription."""
        if user_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[user_id]
        subscription.status = "cancelled"
        subscription.auto_renew = False
        
        return True


# =============================================================================
# CLI for testing
# =============================================================================

def main():
    """Test subscription manager."""
    manager = SubscriptionManager()
    
    # Example subscription URL (replace with real one)
    test_url = "https://api.vpn-saas.io/api/v1/subscribe?user=test&token=xxx"
    
    print("Subscription Manager Test")
    print("=" * 50)
    
    # Create test subscription
    sub = manager.create_subscription("user123", "pro")
    print(f"Created subscription: {sub.subscription_id}")
    print(f"Plan: {sub.plan}")
    print(f"Limits: {sub.get_limits()}")
    
    # Update nodes (would use real URL in production)
    # count = manager.update_nodes("user123", test_url)
    # print(f"Updated {count} nodes")
    
    # Get nodes for user
    # nodes = manager.get_nodes_for_user("user123", sub)
    # for node in nodes:
    #     print(f"  - {node.name} ({node.country}) - {node.host}:{node.port}")


if __name__ == "__main__":
    main()
