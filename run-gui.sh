#!/bin/bash
export DISPLAY=:0
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
cd /home/kostik/vless-vpn-client
/usr/bin/python3 vpn_gui_ultimate.py gui
