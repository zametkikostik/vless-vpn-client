#!/bin/bash
# Запуск VPN GUI
export PATH="$HOME/.local/bin:$PATH"
python3 /home/kostik/vpn-client-aggregator/vpn_gui.py "$@"
