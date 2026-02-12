const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("blackhaven", {
  getConfig: () => ipcRenderer.invoke("config:get"),
  detectTools: () => ipcRenderer.invoke("tools:detect"),
  listThemes: () => ipcRenderer.invoke("themes:list"),
  listPlugins: () => ipcRenderer.invoke("plugins:list"),

  createTerminal: () => ipcRenderer.invoke("terminal:create"),
  writeTerminal: (id, data) => ipcRenderer.invoke("terminal:write", { id, data }),
  resizeTerminal: (id, cols, rows) => ipcRenderer.invoke("terminal:resize", { id, cols, rows }),
  closeTerminal: (id) => ipcRenderer.invoke("terminal:close", id),
  onTerminalData: (cb) => {
    const listener = (_, payload) => cb(payload);
    ipcRenderer.on("terminal:data", listener);
    return () => ipcRenderer.removeListener("terminal:data", listener);
  },

  launchTool: (tool, args) => ipcRenderer.invoke("tools:launch", { tool, args }),
  getSnapshot: () => ipcRenderer.invoke("monitor:snapshot"),
  listProcesses: () => ipcRenderer.invoke("process:list"),
  killProcess: (pid) => ipcRenderer.invoke("process:kill", pid),

  runNetworkScan: (target) => ipcRenderer.invoke("network:scan", target),
  listPorts: () => ipcRenderer.invoke("network:ports")
});
