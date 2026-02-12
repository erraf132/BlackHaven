export class TerminalPanel {
  constructor(blackhaven, paneA, paneB, tabStrip, paneWrap) {
    this.blackhaven = blackhaven;
    this.paneA = paneA;
    this.paneB = paneB;
    this.tabStrip = tabStrip;
    this.paneWrap = paneWrap;

    this.tabs = [];
    this.terminals = new Map();
    this.activeTabId = null;
    this.split = false;
    this.paneATabId = null;
    this.paneBTabId = null;
  }

  attachEventBridge() {
    this.blackhaven.onTerminalData(({ id, data }) => {
      const item = this.terminals.get(id);
      if (item) item.term.write(data);
    });
  }

  async createTab(label) {
    const created = await this.blackhaven.createTerminal();
    const term = new Terminal({
      fontFamily: "JetBrains Mono, Fira Code, monospace",
      fontSize: 13,
      cursorBlink: true,
      allowTransparency: true,
      theme: {
        background: "#00000000",
        foreground: getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#cdf9ff",
        cursor: getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#00f5d4"
      },
      scrollback: 5000
    });

    this.terminals.set(created.id, { term });
    term.onData((data) => {
      this.blackhaven.writeTerminal(created.id, data);
    });

    const tab = { id: created.id, label: label || `TAB-${created.id}` };
    this.tabs.push(tab);
    this.activeTabId = created.id;

    if (!this.paneATabId) this.paneATabId = created.id;
    if (this.split && !this.paneBTabId) this.paneBTabId = created.id;

    this.renderTabs();
    this.mountTerminals();
  }

  setSplit(enabled) {
    this.split = enabled;
    this.paneWrap.className = `pane-wrap ${this.split ? "split" : "single"}`;

    if (this.split && !this.paneBTabId) {
      const alt = this.tabs.find((t) => t.id !== this.paneATabId);
      this.paneBTabId = alt ? alt.id : this.paneATabId;
    }

    this.mountTerminals();
  }

  async ensureSplitTab() {
    if (!this.split) return;
    if (this.paneBTabId) return;
    await this.createTab("AUX");
    this.paneBTabId = this.activeTabId;
    this.paneATabId = this.tabs[0]?.id || this.activeTabId;
  }

  mountSingle(container, tabId, activePaneClass) {
    container.classList.toggle("active-pane", activePaneClass);
    container.innerHTML = "";
    if (!tabId) return;

    const t = this.terminals.get(tabId);
    if (!t) return;

    t.term.open(container);
    this.resizeTerminalToContainer(tabId, container);
  }

  mountTerminals() {
    this.mountSingle(this.paneA, this.paneATabId, true);

    if (this.split) {
      this.paneB.classList.remove("hidden");
      this.mountSingle(this.paneB, this.paneBTabId, false);
    } else {
      this.paneB.classList.add("hidden");
    }
  }

  renderTabs() {
    this.tabStrip.innerHTML = "";
    for (const tab of this.tabs) {
      const btn = document.createElement("button");
      btn.className = `tab ${this.activeTabId === tab.id ? "active" : ""}`;
      btn.textContent = tab.label;
      btn.onclick = () => {
        this.activeTabId = tab.id;
        this.paneATabId = tab.id;
        if (this.split && !this.paneBTabId) {
          const alt = this.tabs.find((t) => t.id !== tab.id);
          this.paneBTabId = alt ? alt.id : tab.id;
        }
        this.renderTabs();
        this.mountTerminals();
      };
      this.tabStrip.appendChild(btn);
    }
  }

  handleResize() {
    for (const [id] of this.terminals) {
      const isA = this.paneATabId === id;
      const isB = this.split && this.paneBTabId === id;
      if (!isA && !isB) continue;
      const container = isA ? this.paneA : this.paneB;
      this.resizeTerminalToContainer(id, container);
    }
  }

  resizeTerminalToContainer(tabId, container) {
    const item = this.terminals.get(tabId);
    if (!item) return;

    const rect = container.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const cols = Math.max(20, Math.floor(rect.width / 9));
    const rows = Math.max(5, Math.floor(rect.height / 18));
    item.term.resize(cols, rows);
    this.blackhaven.resizeTerminal(tabId, cols, rows);
  }

  closeAll() {
    for (const [id] of this.terminals) {
      this.blackhaven.closeTerminal(id);
    }
  }
}
