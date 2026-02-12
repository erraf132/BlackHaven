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
