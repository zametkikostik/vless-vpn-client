#!/bin/bash
# Запуск VLESS VPN Client - ALL IN ONE
export PATH="$HOME/.local/bin:$PATH"
echo "🚀 Запуск VLESS VPN Client - ALL IN ONE..."
python3 /home/kostik/vpn-client-aggregator/vpn-client-all-in-one.py "$@"
