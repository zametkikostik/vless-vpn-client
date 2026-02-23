#!/usr/bin/env python3
"""
VLESS VPN SaaS - Enhanced CLI Client
Production CLI with full API integration.

© 2024 VPN Solutions Inc. All rights reserved.
"""

__version__ = "3.0.0-saas-cli"

import click
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import requests

# Configuration
API_BASE = os.getenv("VLESS_API_URL", "http://localhost:8000")
CONFIG_DIR = Path.home() / ".vpn-saas"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load stored configuration."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save configuration."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_token() -> str:
    """Get stored access token."""
    config = load_config()
    return config.get("access_token", "")


def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make API request with authentication."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_token()}"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ API Error: {e}", err=True)
        sys.exit(1)


@click.group()
@click.version_option(version=__version__)
def cli():
    """VLESS VPN SaaS - Production CLI Client"""
    pass


# =============================================================================
# Authentication Commands
# =============================================================================

@cli.command()
@click.option('--email', prompt=True, help='User email')
@click.option('--password', prompt=True, hide_input=True, help='User password')
def login(email, password):
    """Login to VPN service."""
    click.echo("🔐 Logging in...")
    
    response = api_request("POST", "/api/v1/auth/login", {
        "email": email,
        "password": password
    })
    
    config = load_config()
    config["access_token"] = response["access_token"]
    config["refresh_token"] = response["refresh_token"]
    config["email"] = email
    save_config(config)
    
    click.echo("✅ Login successful!")
    click.echo(f"   Token expires in: {response.get('expires_in', 'N/A')} seconds")


@cli.command()
@click.option('--email', prompt=True, help='User email')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.option('--username', prompt=True, help='Username')
def register(email, password, username):
    """Register new account."""
    click.echo("📝 Registering new account...")
    
    response = api_request("POST", "/api/v1/auth/register", {
        "email": email,
        "password": password,
        "username": username
    })
    
    click.echo("✅ Registration successful!")
    click.echo(f"   User ID: {response.get('id', 'N/A')}")
    click.echo(f"   Plan: {response.get('plan', 'free')}")


@cli.command()
def logout():
    """Logout and clear credentials."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    click.echo("✅ Logged out successfully")


# =============================================================================
# User Commands
# =============================================================================

@cli.command()
def me():
    """Show current user information."""
    token = get_token()
    if not token:
        click.echo("❌ Not logged in. Use 'login' command first.")
        sys.exit(1)
    
    user = api_request("GET", "/api/v1/users/me")
    
    click.echo("\n👤 User Information")
    click.echo("=" * 40)
    click.echo(f"Email: {user.get('email')}")
    click.echo(f"Username: {user.get('username')}")
    click.echo(f"Plan: {user.get('plan', 'free').upper()}")
    click.echo(f"Active: {'Yes' if user.get('is_active') else 'No'}")
    click.echo("")


@cli.command()
def usage():
    """Show usage statistics."""
    stats = api_request("GET", "/api/v1/users/me/usage")
    
    click.echo("\n📊 Usage Statistics")
    click.echo("=" * 40)
    click.echo(f"Uploaded: {stats.get('bytes_uploaded', 0) / (1024*1024):.2f} MB")
    click.echo(f"Downloaded: {stats.get('bytes_downloaded', 0) / (1024*1024):.2f} MB")
    click.echo(f"Connections: {stats.get('connections_count', 0)}")
    click.echo("")


# =============================================================================
# Subscription Commands
# =============================================================================

@cli.command()
def subscription():
    """Show current subscription."""
    try:
        sub = api_request("GET", "/api/v1/subscriptions/me")
        
        click.echo("\n💳 Subscription")
        click.echo("=" * 40)
        click.echo(f"Plan: {sub.get('plan', 'N/A').upper()}")
        click.echo(f"Status: {sub.get('status', 'N/A')}")
        click.echo(f"Starts: {sub.get('current_period_start', 'N/A')}")
        click.echo(f"Ends: {sub.get('current_period_end', 'N/A')}")
        click.echo("")
    except Exception as e:
        click.echo(f"❌ No subscription found: {e}")


@cli.command()
@click.option('--plan', type=click.Choice(['free', 'basic', 'pro', 'enterprise']), required=True)
@click.option('--payment', type=click.Choice(['stripe', 'crypto']), default='stripe')
@click.option('--months', type=int, default=1)
def subscribe(plan, payment, months):
    """Create new subscription."""
    click.echo(f"💳 Creating {plan.upper()} subscription...")
    
    data = {
        "plan": plan,
        "payment_method": payment,
        "months": months
    }
    
    if payment == 'crypto':
        data["crypto_currency"] = "USDT"
    
    sub = api_request("POST", "/api/v1/subscriptions", data)
    
    click.echo("✅ Subscription created!")
    click.echo(f"   Plan: {sub.get('plan')}")
    click.echo(f"   Ends: {sub.get('current_period_end')}")
    click.echo("")


# =============================================================================
# VPN Node Commands
# =============================================================================

@cli.command('nodes')
def list_nodes():
    """List available VPN nodes."""
    nodes = api_request("GET", "/api/v1/nodes")
    
    if not nodes:
        click.echo("❌ No nodes available")
        return
    
    click.echo("\n🌍 Available VPN Nodes")
    click.echo("=" * 60)
    click.echo(f"{'Name':<25} {'Country':<15} {'Latency':<10} {'Status':<10}")
    click.echo("-" * 60)
    
    for node in nodes:
        status_icon = "🟢" if node.get('status') == 'online' else "🔴"
        click.echo(
            f"{node.get('name', 'N/A'):<25} "
            f"{node.get('country', 'N/A'):<15} "
            f"{node.get('latency', 'N/A')}ms {' ' * 6:<6} "
            f"{status_icon} {node.get('status', 'N/A')}"
        )
    
    click.echo("")


# =============================================================================
# VPN Config Commands
# =============================================================================

@cli.command()
@click.option('--node', '-n', help='Specific node ID')
@click.option('--protocol', default='vless', help='VPN protocol')
@click.option('--transport', default='reality', help='Transport type')
def connect(node, protocol, transport):
    """Generate VPN configuration and connect."""
    click.echo("🔌 Connecting to VPN...")
    
    data = {
        "protocol": protocol,
        "transport": transport
    }
    
    if node:
        data["node_id"] = node
    
    config = api_request("POST", "/api/v1/configs/generate", data)
    
    click.echo("✅ VPN Configuration Generated!")
    click.echo("=" * 60)
    click.echo(f"VLESS URL:")
    click.echo(config.get('vless_url'))
    click.echo("")
    click.echo(f"Subscription URL:")
    click.echo(config.get('subscription_url'))
    click.echo("")
    click.echo("ℹ️  Import this URL into your VPN client")
    click.echo("")


@cli.command('configs')
def list_configs():
    """List user VPN configurations."""
    configs = api_request("GET", "/api/v1/configs")
    
    if not configs:
        click.echo("❌ No configurations found")
        return
    
    click.echo("\n📋 Your VPN Configurations")
    click.echo("=" * 60)
    
    for config in configs:
        click.echo(f"ID: {config.get('id')}")
        click.echo(f"Protocol: {config.get('protocol')}")
        click.echo(f"Transport: {config.get('transport')}")
        click.echo(f"Expires: {config.get('expires_at')}")
        click.echo("-" * 60)
    
    click.echo("")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    cli()
