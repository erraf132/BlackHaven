const si = require("systeminformation");
const os = require("os");
const { execFile } = require("child_process");

function tryNvidiaSmi() {
  return new Promise((resolve) => {
    execFile("nvidia-smi", ["--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], (err, stdout) => {
      if (err || !stdout) return resolve(null);
      const line = stdout.split("\n")[0]?.trim();
      if (!line) return resolve(null);
      const [util, temp, memUsed, memTotal] = line.split(",").map((x) => Number(x.trim()));
      resolve({ util, temp, memUsed, memTotal, source: "nvidia-smi" });
    });
  });
}

async function getSnapshot() {
  const [load, mem, fsSize, temp, netStats, netConn, graphics, time, cpu] = await Promise.all([
    si.currentLoad(),
    si.mem(),
    si.fsSize(),
    si.cpuTemperature(),
    si.networkStats(),
    si.networkConnections(),
    si.graphics(),
    si.time(),
    si.cpu()
  ]);

  const gpuFallback = graphics.controllers?.[0]
    ? {
        util: graphics.controllers[0].utilizationGpu || 0,
        temp: graphics.controllers[0].temperatureGpu || 0,
        memUsed: graphics.controllers[0].memoryUsed || 0,
        memTotal: graphics.controllers[0].memoryTotal || 0,
        source: "systeminformation"
      }
    : null;

  const gpu = (await tryNvidiaSmi()) || gpuFallback;

  return {
    cpu: {
      model: cpu.brand,
      load: load.currentLoad,
      cores: cpu.cores
    },
    memory: {
      used: mem.used,
      total: mem.total,
      active: mem.active
    },
    disks: fsSize.map((d) => ({
      fs: d.fs,
      used: d.used,
      size: d.size,
      use: d.use
    })),
    gpu,
    temperature: {
      main: temp.main,
      cores: temp.cores || []
    },
    network: {
      stats: netStats,
      connections: netConn.length
    },
    system: {
      hostname: os.hostname(),
      platform: `${os.type()} ${os.release()}`,
      kernel: os.release(),
      uptime: time.uptime
    }
  };
}

async function listProcesses() {
  const list = await si.processes();
  return list.list
    .sort((a, b) => b.cpu - a.cpu)
    .slice(0, 60)
    .map((p) => ({
      pid: p.pid,
      name: p.name,
      cpu: p.cpu,
      mem: p.memRss,
      user: p.user,
      state: p.state
    }));
}

module.exports = {
  getSnapshot,
  listProcesses
};
