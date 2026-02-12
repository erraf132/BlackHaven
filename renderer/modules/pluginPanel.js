export class PluginPanel {
  constructor(blackhaven, mountEl) {
    this.blackhaven = blackhaven;
    this.mountEl = mountEl;
  }

  async init() {
    const plugins = await this.blackhaven.listPlugins();
    this.mountEl.innerHTML = "";

    for (const plugin of plugins) {
      const card = document.createElement("div");
      card.className = "plugin-card";
      card.innerHTML = `<strong>${plugin.name || plugin.id}</strong><br/>${plugin.description || "No description"}`;
      this.mountEl.appendChild(card);

      if (plugin.rendererEntry) {
        const script = document.createElement("script");
        script.src = `file://${plugin.rendererEntry}`;
        script.dataset.pluginId = plugin.id;
        document.body.appendChild(script);
      }
    }
  }
}
