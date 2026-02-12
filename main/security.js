const SAFE_ARG = /^[a-zA-Z0-9_./:=,@+-]+$/;

function validateArgs(args) {
  for (const arg of args) {
    if (!SAFE_ARG.test(arg)) {
      throw new Error(`Unsafe argument rejected: ${arg}`);
    }
  }
}

function validateToolLaunch(tool, args, whitelist) {
  const allowed = whitelist instanceof Set ? whitelist : new Set(whitelist || []);
  if (!allowed.has(tool)) {
    throw new Error(`Tool not allowed: ${tool}`);
  }
  validateArgs(args);
}

module.exports = {
  validateArgs,
  validateToolLaunch
};
