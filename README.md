<<<<<<< HEAD
# BlackHaven-Frame

BlackHaven-Frame is a futuristic, full-screen, modular terminal cockpit for Kali Linux inspired by eDEX-UI.

## Features

- Full-screen immersive terminal UI with multi-tab and split pane support
- Real shell integration (`/bin/bash`, `zsh`, etc.) via `node-pty`
- Kali tool auto-detection (`nmap`, `msfconsole`, `recon-ng`, `hydra`, `john`, and more)
- System monitoring: CPU, RAM, disks, GPU, temperatures, network connections
- Process viewer with kill action
- Network operations panel: host discovery scan + live port listing
- Tool launcher + command builder with allowlist validation
- Theme system (`~/.blackhaven-frame/themes`) and plugin system (`~/.blackhaven-frame/plugins`)
- Boot animation and optional Matrix effect
- Multi-monitor launch support via `--display=<index>`

## Security Model

- Renderer process runs with Electron sandbox + context isolation
- IPC is explicit and limited through preload bridge
- Tool launcher validates commands against whitelist and sanitizes arguments
- The app never overwrites user shell config files (`~/.bashrc`, `~/.zshrc`)

## Project Structure

```text
BlackHaven-Frame/
  main/
    main.js
    config.js
    security.js
    tooling.js
    terminalManager.js
    systemMonitor.js
    networkTools.js
    pluginManager.js
  renderer/
    index.html
    styles.css
    app.js
    modules/
      effects.js
      monitorPanel.js
      networkPanel.js
      pluginPanel.js
      processPanel.js
      terminalPanel.js
      toolPanel.js
      utils.js
  config/
    default.config.json
  themes/
    default-neon/theme.json
    matrix-green/theme.json
  plugins/
    hello-threatmap/
      plugin.json
      renderer.js
  preload.js
  package.json
  .gitignore
```

## Install (Kali Linux)

```bash
cd /home/hacker/BlackHaven-Frame
sudo apt update
sudo apt install -y build-essential python3 make g++ libx11-dev libxkbfile-dev
npm install
```

## Run

```bash
cd /home/hacker/BlackHaven-Frame
npm start
```

Run on a specific monitor:

```bash
npm start -- --display=1
```

## Config

On first launch, a config is created at:

```text
~/.blackhaven-frame/config.json
```

Example options:

- `shell`: choose `/bin/bash` or `/bin/zsh`
- `theme`: select theme ID (e.g. `default-neon`, `matrix-green`)
- `matrixEffect`: `true` or `false`
- `accent`: custom accent color
- `pluginDirs`: additional plugin folders
- `themeDirs`: additional theme folders

## Full Source File List

- `package.json`
- `.gitignore`
- `preload.js`
- `README.md`
- `config/default.config.json`
- `main/main.js`
- `main/config.js`
- `main/security.js`
- `main/tooling.js`
- `main/terminalManager.js`
- `main/systemMonitor.js`
- `main/networkTools.js`
- `main/pluginManager.js`
- `renderer/index.html`
- `renderer/styles.css`
- `renderer/app.js`
- `renderer/modules/effects.js`
- `renderer/modules/monitorPanel.js`
- `renderer/modules/networkPanel.js`
- `renderer/modules/pluginPanel.js`
- `renderer/modules/processPanel.js`
- `renderer/modules/terminalPanel.js`
- `renderer/modules/toolPanel.js`
- `renderer/modules/utils.js`
- `plugins/hello-threatmap/plugin.json`
- `plugins/hello-threatmap/renderer.js`
- `themes/default-neon/theme.json`
- `themes/matrix-green/theme.json`

## Example Plugin

Included example plugin:

```text
plugins/hello-threatmap/
```

Create custom plugins in:

```text
~/.blackhaven-frame/plugins/<plugin-name>/plugin.json
```

`plugin.json` example:

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "description": "Custom BlackHaven panel",
  "renderer": "renderer.js"
}
```

## Example Theme

Included themes:

- `themes/default-neon/theme.json`
- `themes/matrix-green/theme.json`

Custom themes can be added to:

```text
~/.blackhaven-frame/themes/<theme-id>/theme.json
```
=======
# BlackHaven Framework v3.0 OMEGA

**BlackHaven** is an advanced OSINT and security auditing framework designed for authorized cybersecurity research, education, and defensive security analysis.

Developed by **erraf132 and Vyrn.exe Official**

---

## Overview

BlackHaven provides a modular and secure environment for:

* OSINT investigations
* Username intelligence gathering
* Email analysis
* Network and domain reconnaissance
* System and security auditing
* Controlled and authorized security testing

BlackHaven uses a secure authentication system with a globally unique owner account and controlled access levels.

---

## Features

* Secure authentication system
* Global unique Owner account
* Modular architecture
* Automatic results logging to file
* Professional terminal interface
* Secure password hashing (Argon2 / bcrypt)
* OSINT and reconnaissance modules
* Fully local execution (no forced external servers)
* Expandable module system

---

## Installation

### Recommended method (Linux / Kali Linux)

Clone the repository:

```
git clone https://github.com/erraf132/BlackHaven.git
cd BlackHaven
```

Create virtual environment:

```
python3 -m venv venv
```

Activate virtual environment:

```
source venv/bin/activate
```

Install BlackHaven:

```
pip install -e .
```

Run BlackHaven:

```
blackhaven
```

---

## First launch

On first launch, BlackHaven will:

* Show the legal disclaimer
* Ask to create the global results file
* Require creation of the Owner account (first install only)
* Secure all future access

---

## Project Structure

```
blackhaven/
│
├── auth_pkg/          Authentication system
├── core/              Core engines
├── modules/           OSINT and security modules
├── security/          Security configuration
├── ui/                Interface and banner
├── utils/             Utilities and results logging
├── data/              Logs and activity files
│
├── main.py            Main entry point
└── __main__.py        CLI launcher
```

---

## Security Model

BlackHaven uses a secure access model:

* Owner (global root access)
* Admin (optional)
* User (standard access)

Only one Owner exists globally.

Owner privileges include:

* Full system access
* Access to all result files
* System configuration control

---

## Results Logging

All results are automatically saved to the configured results file.

This ensures:

* Audit trail
* Traceability
* Persistent intelligence storage

---

## Updating

To update BlackHaven:

```
git pull
source venv/bin/activate
pip install -e .
```

---

## Legal Disclaimer

BlackHaven is intended for:

* Educational purposes
* Authorized cybersecurity research
* Defensive security testing

Unauthorized use against systems without explicit permission is strictly prohibited.

The authors assume no responsibility for misuse.

You are responsible for complying with applicable laws.

---

## Author

Developed by:

**erraf132**
**Vyrn.exe Official**

BlackHaven Framework © 2026

---

## License

All rights reserved.

This software may not be redistributed, modified, or used without permission from the authors.
>>>>>>> adaa425ea95cdb85faa27662f9a3b79e01a1fd9e



# 🖤 BlackHaven-Frame

**BlackHaven-Frame** est un **terminal cockpit futuriste pour Kali Linux**, inspiré de **EDEX-UI**, combinant **BlackHaven main**, **framework** et outils **DeadNS / DNS Reaper** pour une expérience “hacker style”.

---

## ⚡ Features

- Interface terminal stylée, futuriste et modulable  
- Basculer entre le **BlackHaven main** et le **framework**  
- Intégration de tous les outils BlackHaven  
- Visualisation en temps réel du système et du réseau  
- Support de plugins et extensions  
- Modules OSINT intégrés (Email Intelligence, Network Scanner, etc.)

---

## 🛠 Installation

```bash
# Mettre à jour Kali et installer les dépendances
sudo apt-get update
sudo apt-get install -y build-essential python3 nodejs npm

# Aller dans le dossier du cockpit
cd ~/BlackHaven-Frame/blackhaven-frame-cockpit

# Installer les packages Node.js
npm install

# Lancer l'interface
npm run start

