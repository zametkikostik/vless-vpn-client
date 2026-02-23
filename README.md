# VLESS VPN Client - Production Version

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/igareck/vpn-client-aggregator)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

Enterprise-grade VPN client for VLESS protocol with Reality obfuscation.

## Features

- **Production-ready code** - Type hints, proper error handling, comprehensive logging
- **Reality protocol support** - Advanced obfuscation for bypassing restrictions
- **Automatic server selection** - Priority-based algorithm (Low-ping → WHITE → BLACK)
- **Health checking** - TCP connectivity tests before connection
- **XRay core integration** - Full support for VLESS protocol
- **GitHub auto-update** - Automatic server list updates from remote repository

## Installation

```bash
# Clone repository
git clone https://github.com/igareck/vpn-client-aggregator.git
cd vpn-client-aggregator

# Install dependencies (optional, for GUI)
pip3 install PyQt5

# Setup symlink
ln -sf $(pwd)/vless_client.py ~/.local/bin/vless-vpn
chmod +x ~/.local/bin/vless-vpn
```

## Usage

### Command Line

```bash
# Connect to VPN (auto-select best server)
vless-vpn start --auto

# Check connection status
vless-vpn status

# Update server list from GitHub
vless-vpn update

# Disconnect from VPN
vless-vpn stop
```

### GUI Interface

```bash
# Launch GUI
vpn-gui
```

## Configuration

The client uses the following directory structure:

```
~/vpn-client/
├── data/
│   └── servers.json      # Server list cache
├── config/
│   └── config.json       # XRay configuration
├── logs/
│   └── client.log        # Application logs
└── bin/
    └── xray              # XRay binary
```

## Server Selection Algorithm

1. **Priority 1**: Low latency servers (<100ms) with Reality protocol
2. **Priority 2**: WHITE list servers with Reality protocol  
3. **Priority 3**: Any Reality protocol servers with UUID

The client tests top 5 servers for TCP connectivity and selects the first available.

## API Reference

### VLESSClient Class

```python
from vless_client import VLESSClient, VPNConfig

# Create client with default configuration
client = VLESSClient()

# Or custom configuration
config = VPNConfig(
    home_dir=Path.home(),
    # ... other options
)
client = VLESSClient(config)

# Connect to VPN
success = client.connect()

# Get status
status = client.status()
print(f"Connected: {status['connected']}")

# Disconnect
client.disconnect()

# Update servers
client.update_servers()
```

## Logging

The client uses Python's standard logging module with the following format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] Message
```

Log levels:
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages

## Requirements

- Python 3.8+
- XRay binary
- PyQt5 (optional, for GUI)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues and feature requests, please use GitHub Issues.
