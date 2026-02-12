const os = require("os");
const pty = require("node-pty");

class TerminalManager {
  constructor(config) {
    this.config = config;
    this.sessions = new Map();
    this.nextId = 1;
  }

  createSession() {
    const id = this.nextId++;
    const shell = this.config.shell || (os.platform() === "win32" ? "powershell.exe" : "/bin/bash");

    const term = pty.spawn(shell, [], {
      name: "xterm-256color",
      cols: 120,
      rows: 30,
      cwd: os.homedir(),
      env: {
        ...process.env,
        TERM: "xterm-256color"
      }
    });

    this.sessions.set(id, term);
    return { id, shell };
  }

  onData(id, cb) {
    const term = this.sessions.get(id);
    if (!term) throw new Error(`Terminal session missing: ${id}`);
    term.onData(cb);
  }

  write(id, data) {
    const term = this.sessions.get(id);
    if (!term) return;
    term.write(data);
  }

  resize(id, cols, rows) {
    const term = this.sessions.get(id);
    if (!term) return;
    term.resize(Math.max(cols, 20), Math.max(rows, 5));
  }

  close(id) {
    const term = this.sessions.get(id);
    if (!term) return;
    term.kill();
    this.sessions.delete(id);
  }

  closeAll() {
    for (const [id, term] of this.sessions.entries()) {
      term.kill();
      this.sessions.delete(id);
    }
  }
}

module.exports = TerminalManager;
