# bt - Modern BLE CLI Tool

A beautiful, interactive command-line tool for scanning, connecting to, and communicating with Bluetooth Low Energy (BLE) devices. Built with **Typer**, **Rich**, and **Bleak**. Includes **security auditing** and a **real-time web dashboard**.

## Features

✨ **Interactive Device Selection** — Scan for BLE devices and navigate with arrow keys  
📊 **Device Introspection** — View all services and characteristics with their properties  
📖 **Read Characteristics** — Read data from BLE device characteristics  
✍️ **Write to Devices** — Send data to writable characteristics  
🔔 **Listen for Notifications** — Receive real-time notifications from device characteristics  
🎨 **Colorful UI** — Modern, user-friendly terminal interface with Rich formatting  
🔐 **Security Audit** — Automated BLE security assessment and vulnerability detection  
📈 **Web Dashboard** — Real-time web UI with live device monitoring, RSSI tracking, and audit results  
📡 **Packet Logging** — Capture and analyze BLE advertisement packets  
📶 **RSSI Monitoring** — Track signal strength over time  

## Installation

### Prerequisites
- Python 3.9+
- `uv` package manager ([install here](https://docs.astral.sh/uv/getting-started/))

### Setup

```bash
git clone https://github.com/qainsights/bt.git
cd bt

# Install dependencies
uv pip install -e .
```

Or with the full dev setup:
```bash
uv pip install -e . && uv pip install pytest
```

## Quick Start

### 1. Scan for Devices (CLI)

```bash
bt scan
```

This will:
- 🔍 Scan for BLE devices for 5 seconds
- 📋 Display all found devices with names and MAC addresses
- 🎯 Let you select a device using arrow keys to automatically connect

### 2. Connect Directly (if you know the MAC)

```bash
bt connect 20:6E:F1:88:11:7D
```

### 3. Interactive Commands (After Connecting)

Once connected, you'll see an interactive menu:

```
Choose an action:
  ▸ Read Characteristic
    Write Characteristic
    Listen to Characteristic
    Disconnect
```

**Read a value:**
```
? Choose an action: Read Characteristic
? Select characteristic: 26d4d7fa-58a5-4672-b363-d73c680a9f86
✅ Read: b'42'
```

**Write a message:**
```
? Choose an action: Write Characteristic
? Select characteristic: 16d4d7fa-58a5-4672-b363-d73c680a9f85
? Enter message to write: Hello World
✅ Write successful
```

**Listen for notifications:**
```
? Choose an action: Listen to Characteristic
? Select characteristic: 36d4d7fa-58a5-4672-b363-d73c680a9f87
Listening on 36d4d7fa-58a5-4672-b363-d73c680a9f87... Press Enter to stop
→ 48656c6c6f
→ 576f726c64
```

### 4. Security Audit (CLI)

Automatically scan a device for security vulnerabilities:

```bash
python -c "
import asyncio
from security_audit import BLESecurityAuditor

auditor = BLESecurityAuditor()
report = asyncio.run(auditor.audit('20:6E:F1:88:11:7D'))
print(report.to_text())
"
```

Detects:
- 🔴 Unencrypted characteristics
- 🔴 Missing authentication/authorization
- 🟠 Insecure UUIDs
- 🟠 Lack of GATT write protection
- 🟡 Missing security descriptors

### 5. Web Dashboard

Launch the real-time web dashboard:

```bash
python dashboard.py
```

Then open **http://localhost:8080** in your browser.

**Dashboard features:**
- 📊 Live device scanning with RSSI visualization
- 🔍 Real-time packet log stream
- 🔐 Run security audits from the UI
- 📈 Signal strength charts
- 🎯 One-click device details

## Command Reference

### `bt scan [--timeout 5.0]`
Scan for available BLE devices with interactive selection.

- `--timeout`: Scan duration in seconds (default: 5.0)

### `bt connect <address>`
Connect directly to a device by MAC address.

- `address`: Device MAC address (e.g., `20:6E:F1:88:11:7D`)

### `bt write <address> <char> "message"`
Write data to a specific characteristic (one-off operation).

- `address`: Device MAC address
- `char`: Characteristic UUID
- `message`: Data to write

### `bt listen <address> <char>`
Listen for notifications on a characteristic (one-off operation).

- `address`: Device MAC address
- `char`: Characteristic UUID (must support notify/indicate)

## Tools & Modules

### `security_audit.py`
Automated security assessment tool. Checks for:
- Unencrypted data exposure
- Missing authentication
- Weak GATT descriptors
- Insecure UUIDs
- Replay attack vulnerabilities

**Usage:**
```python
from security_audit import BLESecurityAuditor
auditor = BLESecurityAuditor()
report = await auditor.audit("AA:BB:CC:DD:EE:FF")
print(report.to_text())
print(report.to_json())
```

### `dashboard.py`
Real-time web dashboard with WebSocket support. Features:
- Live device scanner
- RSSI tracking
- Packet logger
- Security audit integration
- Signal strength visualization

**Usage:**
```bash
python dashboard.py --port 8080
```

### `packet_logger.py`
Captures and logs BLE advertisement packets for analysis.

### `rssi_monitor.py`
Monitors signal strength (RSSI) of BLE devices over time.

### `gatt_uuids.py`
GATT UUID resolver with 600+ standard UUIDs. Automatically resolves:
- Service UUIDs to human-readable names
- Characteristic UUIDs to descriptions
- Vendor-specific UUIDs

## Testing with ESP32

Included: `ble.ino` — an Arduino sketch for testing with ESP32/XIAO.

### Setup

1. **Install Arduino IDE** and add ESP32 board support
2. **Open `ble.ino`** in Arduino IDE
3. **Select board**: Tools → Board → ESP32 Dev Module (or XIAO ESP32C3)
4. **Upload** to your ESP32

The device will:
- Advertise as `test-ble`
- Expose 3 characteristics:
  - **Write**: `16d4d7fa-58a5-4672-b363-d73c680a9f85` (write only)
  - **Read**: `26d4d7fa-58a5-4672-b363-d73c680a9f86` (read-only, returns counter)
  - **Notify**: `36d4d7fa-58a5-4672-b363-d73c680a9f87` (notifications)
- Display written messages on connected OLED

## Project Structure

```
bt/
├── bt.py                  # Main CLI application
├── ble.py                 # BleManager class (async BLE operations)
├── security_audit.py      # BLE security auditor
├── dashboard.py           # Web dashboard (aiohttp + WebSocket)
├── packet_logger.py       # BLE packet capture & logging
├── rssi_monitor.py        # Signal strength monitoring
├── gatt_uuids.py          # GATT UUID resolver (600+ UUIDs)
├── ble.ino                # ESP32 test device firmware
├── pyproject.toml         # Python package config
├── uv.toml                # uv configuration
├── test_cli.py            # Unit tests
├── static/                # Web dashboard assets
├── logs/                  # Packet logs directory
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## Understanding BLE

### Services & Characteristics

- **Service**: A logical grouping of functionality (UUID)
  - Example: Battery Service (`180F`), Device Information (`180A`)
- **Characteristic**: A data point within a service (UUID)
  - Example: Battery Level (`2A19`), Manufacturer Name (`2A29`)
  - Properties: `read`, `write`, `notify`, `indicate`, `write_without_response`

### UUID Types

- **Standard UUIDs**: 16-bit, assigned by Bluetooth SIG (e.g., `180F`)
- **Custom UUIDs**: 128-bit, unique per vendor (e.g., `89c52e89-c665-4378-a274-e08065ee12e3`)

Generate custom UUIDs at [uuidgenerator.net](https://www.uuidgenerator.net/)

### Security Considerations

BLE security depends on:
- **Encryption**: All data should be encrypted over the air
- **Authentication**: Devices must verify identity
- **Authorization**: Access control on sensitive characteristics
- **GATT Protection**: Write/read permissions properly configured

Use the `security_audit.py` tool to identify vulnerabilities.

## Development

### Run Tests

```bash
pytest test_cli.py -v
```

### Code Style

- Python 3.9+ with type hints
- Minimal comments (code should be self-documenting)
- Use Rich for terminal output
- Use Typer for CLI structure
- Async/await for BLE operations

## Troubleshooting

**"Device not found"**
- Ensure device is powered on and advertising
- Try increasing scan timeout: `bt scan --timeout 10.0`
- Check device is not already connected to another application

**"Write/Read failed"**
- Verify characteristic UUID is correct
- Check characteristic properties (e.g., only write to writable characteristics)
- Device may have disconnected; reconnect with `bt scan`

**Permissions issues (Linux/Mac)**
- May need `sudo` for Bluetooth access
- Or add user to `bluetooth` group: `sudo usermod -a -G bluetooth $USER`

**Dashboard not loading**
- Ensure port 8080 is not in use: `python dashboard.py --port 8081`
- Check firewall allows localhost connections

## Dependencies

- **typer** - CLI framework
- **rich** - Terminal formatting & colors
- **bleak** - Cross-platform BLE library
- **questionary** - Interactive prompts with arrow key support
- **aiohttp** - Web server for dashboard
- **pytest** - Testing framework

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Author

Created with ❤️ using GitHub Copilot CLI

---

**Have questions?** Open an issue on GitHub!
