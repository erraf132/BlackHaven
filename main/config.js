const fs = require("fs");
const os = require("os");
const path = require("path");

const APP_DIR = path.join(os.homedir(), ".blackhaven-frame");
const CONFIG_PATH = path.join(APP_DIR, "config.json");
const DEFAULT_CONFIG_PATH = path.join(__dirname, "..", "config", "default.config.json");

function ensureDir(p) {
  if (!fs.existsSync(p)) {
    fs.mkdirSync(p, { recursive: true });
  }
}

function expandHome(p) {
  if (!p) return p;
  if (p === "~") return os.homedir();
  if (p.startsWith("~/")) return path.join(os.homedir(), p.slice(2));
  return p;
}

function loadDefaultConfig() {
  return JSON.parse(fs.readFileSync(DEFAULT_CONFIG_PATH, "utf8"));
}

function ensureUserConfig() {
  const defaults = loadDefaultConfig();
  ensureDir(APP_DIR);
  ensureDir(path.join(APP_DIR, "themes"));
  ensureDir(path.join(APP_DIR, "plugins"));

  if (!fs.existsSync(CONFIG_PATH)) {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(defaults, null, 2));
  }
}

function loadConfig() {
  ensureUserConfig();
  const defaults = loadDefaultConfig();
  const user = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));

  const merged = {
    ...defaults,
    ...user,
    pluginDirs: [...(defaults.pluginDirs || []), ...(user.pluginDirs || [])],
    themeDirs: [...(defaults.themeDirs || []), ...(user.themeDirs || [])]
  };

  merged.pluginDirs = [...new Set(merged.pluginDirs.map(expandHome))];
  merged.themeDirs = [...new Set(merged.themeDirs.map(expandHome))];
  return merged;
}

module.exports = {
  APP_DIR,
  CONFIG_PATH,
  ensureUserConfig,
  loadConfig,
  expandHome
};
