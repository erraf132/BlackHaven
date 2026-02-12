const fs = require("fs");
const path = require("path");

function discoverPlugins(customPluginDirs = []) {
  const builtIn = path.join(__dirname, "..", "plugins");
  const roots = [builtIn, ...customPluginDirs];
  const plugins = [];

  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const pluginDir = path.join(root, entry.name);
      const manifestPath = path.join(pluginDir, "plugin.json");
      if (!fs.existsSync(manifestPath)) continue;

      try {
        const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
        plugins.push({
          ...manifest,
          id: manifest.id || entry.name,
          pluginDir,
          rendererEntry: manifest.renderer ? path.join(pluginDir, manifest.renderer) : null
        });
      } catch {
        // Ignore invalid plugin manifests.
      }
    }
  }

  return plugins;
}

module.exports = {
  discoverPlugins
};
