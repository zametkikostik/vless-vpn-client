#!/bin/bash
# Запуск VPN Web Interface v2.0 с DeVPN
export PATH="$HOME/.local/bin:$PATH"
echo "🌐 Запуск VPN Web Interface v2.0..."
python3 /home/kostik/vpn-client-aggregator/vpn-web-v2.py "$@"
