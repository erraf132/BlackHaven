export function bytesToHuman(v) {
  if (!v) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let n = v;
  let i = 0;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toFixed(1)} ${units[i]}`;
}

export function fmtPercent(v) {
  return `${Number(v || 0).toFixed(1)}%`;
}

export function splitArgs(value) {
  if (!value.trim()) return [];
  return value.trim().split(/\s+/);
}
