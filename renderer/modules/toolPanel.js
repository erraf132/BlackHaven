import { splitArgs } from "./utils.js";

export class ToolPanel {
  constructor(blackhaven, toolList, builderTool, builderArgs, launchButton) {
    this.blackhaven = blackhaven;
    this.toolList = toolList;
    this.builderTool = builderTool;
    this.builderArgs = builderArgs;
    this.launchButton = launchButton;
    this.tools = [];
  }

  render() {
    this.toolList.innerHTML = "";
    this.builderTool.innerHTML = "";

    this.tools.forEach((t) => {
      const chip = document.createElement("div");
      chip.className = "tool-chip";
      chip.textContent = t.name;
      chip.title = t.path;
      this.toolList.appendChild(chip);

      const opt = document.createElement("option");
      opt.value = t.name;
      opt.textContent = t.name;
      this.builderTool.appendChild(opt);
    });
  }

  bind() {
    this.launchButton.onclick = async () => {
      const tool = this.builderTool.value;
      const args = splitArgs(this.builderArgs.value);
      try {
        await this.blackhaven.launchTool(tool, args);
        this.builderArgs.value = "";
      } catch (err) {
        alert(`Tool launch rejected: ${err.message}`);
      }
    };
  }

  async init() {
    this.tools = await this.blackhaven.detectTools();
    this.render();
    this.bind();
  }
}
