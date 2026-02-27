#!/bin/bash
cd /home/kostik/vless-vpn-client
echo "=== Запуск VPN GUI ===" 
echo "Дата: $(date)"
python3 vpn_gui.py 2>&1 | tee /tmp/vpn-gui-full.log
