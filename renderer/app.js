import { bootAnimation, applyTheme, runMatrixEffect } from "./modules/effects.js";
import { TerminalPanel } from "./modules/terminalPanel.js";
import { MonitorPanel } from "./modules/monitorPanel.js";
import { ToolPanel } from "./modules/toolPanel.js";
import { NetworkPanel } from "./modules/networkPanel.js";
import { ProcessPanel } from "./modules/processPanel.js";
import { PluginPanel } from "./modules/pluginPanel.js";

const els = {
  bootScreen: document.getElementById("boot-screen"),
  bootProgress: document.getElementById("boot-progress"),
  sysline: document.getElementById("sysline"),
  tabStrip: document.getElementById("tab-strip"),
  paneWrap: document.getElementById("pane-wrap"),
  paneA: document.getElementById("pane-a"),
  paneB: document.getElementById("pane-b"),
  newTabBtn: document.getElementById("new-tab-btn"),
  splitBtn: document.getElementById("split-btn"),
  monitorGrid: document.getElementById("monitor-grid"),
  toolList: document.getElementById("tool-list"),
  builderTool: document.getElementById("builder-tool"),
  builderArgs: document.getElementById("builder-args"),
  launchToolBtn: document.getElementById("launch-tool-btn"),
  scanTarget: document.getElementById("scan-target"),
  scanBtn: document.getElementById("scan-btn"),
  scanOutput: document.getElementById("scan-output"),
  refreshPortsBtn: document.getElementById("refresh-ports-btn"),
  portsOutput: document.getElementById("ports-output"),
  refreshProcBtn: document.getElementById("refresh-proc-btn"),
  procTable: document.getElementById("proc-table"),
  pluginMount: document.getElementById("plugin-mount"),
  matrixCanvas: document.getElementById("matrix-canvas")
};

let monitorTimer;
let terminalPanel;

async function init() {
  const config = await window.blackhaven.getConfig();
  const themes = await window.blackhaven.listThemes();
  const selectedTheme = themes.find((t) => t.id === config.theme) || themes[0];

  applyTheme(selectedTheme);
  runMatrixEffect(els.matrixCanvas, Boolean(config.matrixEffect));

  terminalPanel = new TerminalPanel(window.blackhaven, els.paneA, els.paneB, els.tabStrip, els.paneWrap);
  terminalPanel.attachEventBridge();
  await terminalPanel.createTab("MAIN");

  const monitorPanel = new MonitorPanel(window.blackhaven, els.monitorGrid, els.sysline);
  const toolPanel = new ToolPanel(window.blackhaven, els.toolList, els.builderTool, els.builderArgs, els.launchToolBtn);
  const networkPanel = new NetworkPanel(window.blackhaven, els.scanTarget, els.scanBtn, els.scanOutput, els.refreshPortsBtn, els.portsOutput);
  const processPanel = new ProcessPanel(window.blackhaven, els.refreshProcBtn, els.procTable);
  const pluginPanel = new PluginPanel(window.blackhaven, els.pluginMount);

  await Promise.all([toolPanel.init(), processPanel.refresh(), networkPanel.refreshPorts(), pluginPanel.init(), monitorPanel.poll()]);

  processPanel.bind();
  networkPanel.bind();

  els.newTabBtn.onclick = () => terminalPanel.createTab();
  els.splitBtn.onclick = async () => {
    terminalPanel.setSplit(!terminalPanel.split);
    await terminalPanel.ensureSplitTab();
    terminalPanel.mountTerminals();
  };

  monitorTimer = setInterval(() => monitorPanel.poll(), config.monitoringIntervalMs || 1200);
  await bootAnimation(els.bootScreen, els.bootProgress);
}

window.addEventListener("resize", () => {
  if (terminalPanel) terminalPanel.handleResize();
});

window.addEventListener("beforeunload", () => {
  clearInterval(monitorTimer);
  if (terminalPanel) terminalPanel.closeAll();
});

init().catch((err) => {
  els.sysline.textContent = `Initialization error: ${err.message}`;
});
