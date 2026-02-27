#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/kostik/vless-vpn-client')

from vpn_controller import VPNController
from pathlib import Path
import json

controller = VPNController()
controller.initialize()

# Генерируем конфиг через engine
engine = controller.engine
xray_config = engine._generate_xray_config()

# Сохраняем
config_file = Path.home() / 'vpn-client' / 'config' / 'config.json'
with open(config_file, 'w') as f:
    json.dump(xray_config, f, indent=2, ensure_ascii=False)

print(f'✅ Конфиг сохранён')

# Проверяем
for outbound in xray_config['outbounds']:
    if outbound.get('tag') == 'proxy':
        rs = outbound.get('streamSettings', {}).get('realitySettings', {})
        print(f'publicKey: {rs.get("publicKey", "")[:20]}...')
        print(f'shortId: {rs.get("shortId", "")}')
        break
