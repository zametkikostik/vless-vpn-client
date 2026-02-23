#!/bin/bash
# Скрипт запуска VPN при старте системы

# Ждем подключения сети
sleep 10

# Экспортируем PATH
export PATH="$HOME/.local/bin:$PATH"

# Запускаем VPN в фоне
nohup vless-vpn start --auto > /home/kostik/vpn-client/logs/vpn.log 2>&1 &

# Настраиваем прокси в среде (опционально)
# export all_proxy=socks5://127.0.0.1:10808
# export https_proxy=http://127.0.0.1:10809

echo "VPN запущен" >> /home/kostik/vpn-client/logs/autostart.log
date >> /home/kostik/vpn-client/logs/autostart.log
