export async function bootAnimation(bootScreen, bootProgress) {
  for (let i = 0; i <= 100; i += 4) {
    bootProgress.style.width = `${i}%`;
    // eslint-disable-next-line no-await-in-loop
    await new Promise((r) => setTimeout(r, 25));
  }
  bootScreen.classList.add("hidden");
}

export function applyTheme(theme) {
  if (!theme || !theme.colors) return;
  const map = {
    "--bg": theme.colors.bg,
    "--panel": theme.colors.panel,
    "--line": theme.colors.line,
    "--text": theme.colors.text,
    "--muted": theme.colors.muted,
    "--accent": theme.colors.accent
  };

  for (const [k, v] of Object.entries(map)) {
    if (v) document.documentElement.style.setProperty(k, v);
  }
}

export function runMatrixEffect(canvas, enabled) {
  const ctx = canvas.getContext("2d", { alpha: true });
  if (!enabled || !ctx) {
    canvas.style.opacity = "0";
    return;
  }

  canvas.style.opacity = "0.16";
  const chars = "01BLACKHAVENFRAME";
  const fontSize = 14;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  resize();
  window.addEventListener("resize", resize);

  const columns = Math.floor(canvas.width / fontSize);
  const drops = Array(columns).fill(1);

  function draw() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00ff99";
    ctx.font = `${fontSize}px monospace`;

    for (let i = 0; i < drops.length; i += 1) {
      const txt = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(txt, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i] += 1;
    }

    requestAnimationFrame(draw);
  }

  draw();
}
