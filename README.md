# BlackHaven

**BlackHaven** is a professional OSINT and security auditing toolkit with a hardened, red-team style terminal interface. It is designed for authorized security testing, training, and defensive research workflows.

```
██████████████████████████████████
        BLACKHAVEN v1.0
   Advanced Security Framework
██████████████████████████████████
```

## Features
- Animated, persistent banner and professional CLI layout
- Modular OSINT and security tooling
- Multithreaded username search and port scanning
- Domain intelligence (WHOIS + DNS)
- Email lookup and password strength checks
- System info collection
- Export results to TXT, JSON, and CSV
- Plugin system for custom modules

## Requirements
- Python 3.9 or newer
- Linux (Kali, Ubuntu) or Windows 10/11
- Terminal with ANSI color support

## Installation

### Kali Linux
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd BlackHaven
./install.sh
```

### Ubuntu
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd BlackHaven
./install.sh
```

### Windows (PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install .
```

### Alternative Install
```bash
pip install .
```

## Usage
```bash
blackhaven
```

```bash
python3 -m blackhaven.main
```

## Security
Owner-only access enabled.

## Screenshot
- Add screenshots to `docs/screenshots/` and update this section.

## Folder Structure
```text
BlackHaven/
├─ blackhaven/              Core package
│  ├─ main.py               Entry point
│  ├─ ui.py                 UI rendering and layouts
│  └─ modules/              Built-in modules
├─ plugins/                 Example plugins
├─ install.sh               Linux installer
├─ uninstall.sh             Linux uninstaller
├─ README.md                Documentation
└─ requirements.txt         Dependencies
```

## Plugin System
BlackHaven loads plugins from the user plugin directory.

Default user plugin path:
```
~/.blackhaven/plugins
```

Each plugin must expose `get_module()` and return a dict with:
```python
{
  "name": "Module Name",
  "description": "What it does",
  "run": callable,
}
```

## Troubleshooting
- **No modules found**: Verify `blackhaven/modules/` exists and Python can import the package.
- **Permission errors**: Run in a user-writable directory and avoid restricted paths.
- **Colors not showing**: Use a terminal that supports ANSI colors.
- **Unexpected error occurred**: Check the log at `~/.blackhaven/results/blackhaven.log`.

## Legal Disclaimer
BlackHaven is provided for educational purposes and authorized security testing only. You must have explicit permission to test or access any systems, networks, or data. Unauthorized use may be illegal and could result in civil or criminal penalties. By using this tool, you accept full responsibility for your actions and agree to comply with all applicable laws and regulations.
