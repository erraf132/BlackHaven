export class NetworkPanel {
  constructor(blackhaven, scanTarget, scanButton, scanOutput, portsButton, portsOutput) {
    this.blackhaven = blackhaven;
    this.scanTarget = scanTarget;
    this.scanButton = scanButton;
    this.scanOutput = scanOutput;
    this.portsButton = portsButton;
    this.portsOutput = portsOutput;
  }

  bind() {
    this.scanButton.onclick = () => this.runScan();
    this.portsButton.onclick = () => this.refreshPorts();
  }

  async runScan() {
    this.scanOutput.textContent = "Running nmap host discovery...";
    try {
      const target = this.scanTarget.value.trim();
      const out = await this.blackhaven.runNetworkScan(target);
      this.scanOutput.textContent = out.slice(0, 4000);
    } catch (err) {
      this.scanOutput.textContent = `Scan failed: ${err.message}`;
    }
  }

  async refreshPorts() {
    try {
      const out = await this.blackhaven.listPorts();
      this.portsOutput.textContent = out.slice(0, 4000);
    } catch (err) {
      this.portsOutput.textContent = `Port monitor error: ${err.message}`;
    }
  }
}
