const { spawn, execFile } = require("child_process");
const { validateArgs } = require("./security");

function runNmapPing(target) {
  validateArgs([target]);
  return new Promise((resolve, reject) => {
    const child = spawn("nmap", ["-sn", target]);
    let output = "";
    let errOut = "";

    child.stdout.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      errOut += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) return reject(new Error(errOut || `nmap exited with ${code}`));
      resolve(output);
    });
  });
}

function listListeningPorts() {
  return new Promise((resolve, reject) => {
    execFile("ss", ["-tulpen"], { maxBuffer: 1024 * 1024 }, (err, stdout) => {
      if (err) return reject(err);
      resolve(stdout);
    });
  });
}

module.exports = {
  runNmapPing,
  listListeningPorts
};
