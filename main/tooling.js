const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const COMMON_KALI_TOOLS = [
  "nmap",
  "msfconsole",
  "recon-ng",
  "hydra",
  "john",
  "nikto",
  "sqlmap",
  "aircrack-ng",
  "tcpdump",
  "wireshark",
  "netdiscover",
  "enum4linux",
  "whatweb",
  "wfuzz",
  "masscan",
  "burpsuite"
];

function findBinary(cmd) {
  try {
    return execFileSync("which", [cmd], { encoding: "utf8" }).trim();
  } catch {
    return null;
  }
}

function detectInstalledTools(extra = []) {
  const discoveredFromDesktop = detectKaliDesktopTools();
  const targets = [...new Set([...COMMON_KALI_TOOLS, ...extra, ...discoveredFromDesktop])];
  const resolved = targets
    .map((name) => ({ name, path: findBinary(name) }))
    .filter((x) => Boolean(x.path));

  const seen = new Set();
  return resolved.filter((tool) => {
    if (seen.has(tool.name)) return false;
    seen.add(tool.name);
    return true;
  });
}

function detectKaliDesktopTools() {
  const appDir = "/usr/share/applications";
  if (!fs.existsSync(appDir)) return [];

  const out = [];
  for (const file of fs.readdirSync(appDir)) {
    if (!file.startsWith("kali-") || !file.endsWith(".desktop")) continue;
    const fullPath = path.join(appDir, file);
    try {
      const content = fs.readFileSync(fullPath, "utf8");
      const execLine = content
        .split("\n")
        .find((line) => line.startsWith("Exec="));
      if (!execLine) continue;
      const raw = execLine.slice(5).trim();
      if (!raw) continue;
      const first = raw.split(/\s+/)[0].replace(/^["']|["']$/g, "");
      const name = path.basename(first);
      if (name) out.push(name);
    } catch {
      // Ignore unreadable desktop files.
    }
  }
  return out;
}

function discoverThemes(customThemeDirs = []) {
  const builtIn = path.join(__dirname, "..", "themes");
  const themeRoots = [builtIn, ...customThemeDirs];
  const themes = [];

  for (const root of themeRoots) {
    if (!fs.existsSync(root)) continue;
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const manifest = path.join(root, entry.name, "theme.json");
      if (!fs.existsSync(manifest)) continue;
      try {
        const data = JSON.parse(fs.readFileSync(manifest, "utf8"));
        themes.push({
          ...data,
          id: data.id || entry.name,
          sourceDir: path.join(root, entry.name)
        });
      } catch {
        // Ignore invalid theme manifests.
      }
    }
  }

  return themes;
}

module.exports = {
  detectInstalledTools,
  discoverThemes
};
