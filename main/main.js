const path = require("path");
const { app, BrowserWindow, ipcMain, shell, screen } = require("electron");
const { spawn } = require("child_process");

const { ensureUserConfig, loadConfig, CONFIG_PATH } = require("./config");
const { detectInstalledTools, discoverThemes } = require("./tooling");
const { discoverPlugins } = require("./pluginManager");
const { validateToolLaunch } = require("./security");
const TerminalManager = require("./terminalManager");
const systemMonitor = require("./systemMonitor");
const networkTools = require("./networkTools");

let mainWindow;
let terminalManager;
let appConfig;
let cachedDetectedTools = [];

function parseDisplayArg() {
  const arg = process.argv.find((a) => a.startsWith("--display="));
  if (!arg) return null;
  const idx = Number(arg.split("=")[1]);
  return Number.isInteger(idx) ? idx : null;
}

function createWindow() {
  const displays = screen.getAllDisplays();
  const displayIndex = parseDisplayArg();
  const targetDisplay = displayIndex !== null && displays[displayIndex] ? displays[displayIndex] : screen.getPrimaryDisplay();

  mainWindow = new BrowserWindow({
    x: targetDisplay.bounds.x,
    y: targetDisplay.bounds.y,
    width: targetDisplay.bounds.width,
    height: targetDisplay.bounds.height,
    fullscreen: true,
    backgroundColor: "#05070d",
    title: "BlackHaven-Frame",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, "..", "renderer", "index.html"));

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

function registerIpc() {
  ipcMain.handle("config:get", () => ({ ...appConfig, configPath: CONFIG_PATH }));
  ipcMain.handle("tools:detect", () => {
    cachedDetectedTools = detectInstalledTools(appConfig.toolWhitelist);
    return cachedDetectedTools;
  });
  ipcMain.handle("themes:list", () => discoverThemes(appConfig.themeDirs));
  ipcMain.handle("plugins:list", () => discoverPlugins(appConfig.pluginDirs));

  ipcMain.handle("terminal:create", () => {
    const created = terminalManager.createSession();
    terminalManager.onData(created.id, (data) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send("terminal:data", { id: created.id, data });
      }
    });
    return created;
  });

  ipcMain.handle("terminal:write", (_, payload) => {
    terminalManager.write(payload.id, payload.data);
    return true;
  });

  ipcMain.handle("terminal:resize", (_, payload) => {
    terminalManager.resize(payload.id, payload.cols, payload.rows);
    return true;
  });

  ipcMain.handle("terminal:close", (_, id) => {
    terminalManager.close(id);
    return true;
  });

  ipcMain.handle("monitor:snapshot", async () => systemMonitor.getSnapshot());
  ipcMain.handle("process:list", async () => systemMonitor.listProcesses());

  ipcMain.handle("process:kill", async (_, pid) => {
    process.kill(Number(pid), "SIGTERM");
    return true;
  });

  ipcMain.handle("network:scan", async (_, target) => networkTools.runNmapPing(target));
  ipcMain.handle("network:ports", async () => networkTools.listListeningPorts());

  ipcMain.handle("tools:launch", async (_, { tool, args }) => {
    const allowed = new Set(cachedDetectedTools.map((t) => t.name));
    validateToolLaunch(tool, args, allowed);

    const proc = spawn(tool, args, {
      detached: true,
      stdio: "ignore"
    });
    proc.unref();
    return { ok: true };
  });
}

app.commandLine.appendSwitch("enable-gpu-rasterization");
app.commandLine.appendSwitch("ignore-gpu-blocklist");

app.whenReady().then(() => {
  ensureUserConfig();
  appConfig = loadConfig();
  terminalManager = new TerminalManager(appConfig);
  registerIpc();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (terminalManager) terminalManager.closeAll();
  if (process.platform !== "darwin") app.quit();
});
