(() => {
  const entityWrap = document.getElementById("entityWrap");
  const skull = document.getElementById("skull");
  const snake = document.getElementById("snake");
  const status = document.getElementById("status");
  const logoBar = document.getElementById("logoBar");

  const typeStatus = (text, speed = 22) => {
    status.textContent = "";
    let idx = 0;
    const step = () => {
      status.textContent += text[idx] ?? "";
      idx += 1;
      if (idx < text.length) {
        setTimeout(step, speed);
      }
    };
    step();
  };

  const speakOnce = (() => {
    let spoken = false;
    return () => {
      if (spoken) return;
      spoken = true;
      const text = "What can I do for you";
      if (!("speechSynthesis" in window)) {
        showSkull();
        return;
      }
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 0.9;
      utter.pitch = 0.9;
      utter.volume = 1.0;
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(v => /en/i.test(v.lang) && /male|alex|daniel|fred|ryan|microsoft/i.test(v.name.toLowerCase()));
      if (preferred) utter.voice = preferred;
      utter.onend = () => showSkull();
      utter.onerror = () => showSkull();
      window.speechSynthesis.speak(utter);
      setTimeout(() => {
        if (!entityWrap.classList.contains("show-skull")) showSkull();
      }, 3500);
    };
  })();

  const showSkull = () => {
    typeStatus("System presence online.");
    entityWrap.classList.add("show-skull");
  };

  const snakeState = {
    active: false,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    t: 0,
    orbitRadius: 120,
    speed: 2.0,
    targetX: 0,
    targetY: 0,
  };

  const getLogoAnchor = () => {
    const rect = logoBar.getBoundingClientRect();
    return {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
      radius: Math.max(rect.width, rect.height) * 0.6,
    };
  };

  const updateSnakeTarget = (mouse) => {
    const anchor = getLogoAnchor();
    const angle = snakeState.t * 0.6;
    const orbitX = anchor.x + Math.cos(angle) * snakeState.orbitRadius;
    const orbitY = anchor.y + Math.sin(angle) * (snakeState.orbitRadius * 0.6);

    if (mouse && mouse.active) {
      const dx = mouse.x - anchor.x;
      const dy = mouse.y - anchor.y;
      const dist = Math.hypot(dx, dy);
      if (dist < anchor.radius * 1.2) {
        snakeState.targetX = mouse.x;
        snakeState.targetY = mouse.y;
        return;
      }
    }

    snakeState.targetX = orbitX;
    snakeState.targetY = orbitY;
  };

  const updateSnake = (mouse) => {
    if (!snakeState.active) return;
    snakeState.t += 0.016;

    updateSnakeTarget(mouse);
    const dx = snakeState.targetX - snakeState.x;
    const dy = snakeState.targetY - snakeState.y;
    const dist = Math.hypot(dx, dy) || 1;
    const ux = dx / dist;
    const uy = dy / dist;

    const speed = snakeState.speed + Math.min(2, dist / 120);
    snakeState.vx = ux * speed;
    snakeState.vy = uy * speed;

    snakeState.x += snakeState.vx;
    snakeState.y += snakeState.vy;

    const wiggle = Math.sin(snakeState.t * 6) * 4;
    const rot = Math.atan2(snakeState.vy, snakeState.vx);
    snake.style.transform = `translate(${snakeState.x}px, ${snakeState.y}px) rotate(${rot}rad) translateY(${wiggle}px)`;
  };

  const animateSnake = (mouse) => {
    updateSnake(mouse);
    requestAnimationFrame(() => animateSnake(mouse));
  };

  let transformed = false;
  const transformToSnake = () => {
    if (transformed) return;
    transformed = true;
    typeStatus("Guardian protocol engaged.");
    entityWrap.classList.add("show-snake");
    const anchor = getLogoAnchor();
    snakeState.x = anchor.x - 120;
    snakeState.y = anchor.y + 140;
    snakeState.active = true;
  };

  const mouse = { x: 0, y: 0, active: false };
  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.active = true;
  });

  const init = () => {
    speakOnce();
    animateSnake(mouse);
  };

  skull.addEventListener("click", transformToSnake);
  snake.addEventListener("click", () => {
    typeStatus("Awaiting command.");
  });

  window.addEventListener("DOMContentLoaded", init);
})();
