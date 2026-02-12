import { bytesToHuman, fmtPercent } from "./utils.js";

export class ProcessPanel {
  constructor(blackhaven, refreshButton, tableEl) {
    this.blackhaven = blackhaven;
    this.refreshButton = refreshButton;
    this.tableEl = tableEl;
  }

  bind() {
    this.refreshButton.onclick = () => this.refresh();
  }

  async refresh() {
    const list = await this.blackhaven.listProcesses();
    this.tableEl.innerHTML = list
      .map(
        (p) =>
          `<div class="proc-row"><span>${p.pid}</span><span>${p.name}</span><span>${fmtPercent(p.cpu)}</span><span>${bytesToHuman(p.mem)}</span><button class="kill-btn" data-pid="${p.pid}">KILL</button></div>`
      )
      .join("");

    this.tableEl.querySelectorAll(".kill-btn").forEach((btn) => {
      btn.onclick = async () => {
        const pid = Number(btn.dataset.pid);
        await this.blackhaven.killProcess(pid);
        this.refresh();
      };
    });
  }
}
