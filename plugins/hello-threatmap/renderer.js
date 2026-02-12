(function threatMapPlugin() {
  const mount = document.getElementById("plugin-mount");
  if (!mount) return;

  const card = document.createElement("div");
  card.className = "plugin-card";
  card.innerHTML = "<strong>Threat Map Feed</strong><br/><span id='threat-feed'>Starting...</span>";
  mount.appendChild(card);

  const feed = card.querySelector("#threat-feed");
  const entries = [
    "OSINT pulse: 4 suspicious domains",
    "Port watch: 2 new listeners on localhost",
    "Recon queue: nmap profile updated",
    "Threat intel: IOC cache synced"
  ];

  let idx = 0;
  setInterval(() => {
    feed.textContent = entries[idx % entries.length];
    idx += 1;
  }, 2200);
})();
