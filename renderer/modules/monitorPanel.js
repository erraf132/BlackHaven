import { bytesToHuman, fmtPercent } from "./utils.js";

export class MonitorPanel {
  constructor(blackhaven, monitorGrid, sysline) {
    this.blackhaven = blackhaven;
    this.monitorGrid = monitorGrid;
    this.sysline = sysline;
  }

  render(snapshot) {
    const rows = [
      ["CPU", `${fmtPercent(snapshot.cpu.load)} (${snapshot.cpu.cores} cores)`],
      ["RAM", `${bytesToHuman(snapshot.memory.used)} / ${bytesToHuman(snapshot.memory.total)}`],
      ["Disk", `${snapshot.disks[0] ? fmtPercent(snapshot.disks[0].use) : "n/a"}`],
      ["GPU", snapshot.gpu ? `${fmtPercent(snapshot.gpu.util)} | ${snapshot.gpu.temp || 0}C` : "n/a"],
      ["Temp", `${snapshot.temperature.main || 0}C`],
      ["Connections", String(snapshot.network.connections)],
      ["Hostname", snapshot.system.hostname],
      ["Kernel", snapshot.system.kernel]
    ];

    this.monitorGrid.innerHTML = rows
      .map(([k, v]) => `<div class="metric"><strong>${k}</strong><br />${v}</div>`)
      .join("");

    this.sysline.textContent = `${snapshot.system.platform} | uptime ${Math.floor(snapshot.system.uptime / 3600)}h | cpu ${fmtPercent(snapshot.cpu.load)} | mem ${fmtPercent((snapshot.memory.used / snapshot.memory.total) * 100)}`;
  }

  async poll() {
    const snap = await this.blackhaven.getSnapshot();
    this.render(snap);
  }
}
