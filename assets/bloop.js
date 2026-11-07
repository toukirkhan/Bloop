const el = (id) => document.getElementById(id);
const ctx = el("matrix").getContext("2d");
const blank = "00".repeat(13);
const input = el("text");
const send = el("send");
let selected = null;
let online = false;
let sending = false;
let previewVersion = 0;
let previewTimer;
let animationTimer;

async function api(path, body) {
  const response = await fetch(path, {
    cache: "no-store",
    ...(body ? {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    } : {}),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed.");
  return data;
}

function paint(frame) {
  ctx.clearRect(0, 0, 286, 176);
  for (let x = 0; x < 13; x++) {
    const column = parseInt(frame.slice(x * 2, x * 2 + 2), 16);
    for (let y = 0; y < 8; y++) {
      ctx.fillStyle = (column & (1 << y)) ? "#83d3ff" : "#233150";
      ctx.beginPath();
      ctx.arc(11 + x * 22, 11 + y * 22, 6, 0, 2 * Math.PI);
      ctx.fill();
    }
  }
}

function selection() {
  if (selected) return {kind: "emoji", value: selected};
  return input.value.trim() ? {kind: "text", value: input.value} : null;
}

function updateSend() {
  send.disabled = !online || sending || !selection();
}

function refreshPreview() {
  const version = ++previewVersion;
  clearTimeout(previewTimer);
  clearInterval(animationTimer);
  el("feedback").textContent = "";
  const body = selection();
  updateSend();
  paint(blank);
  if (!body) return;
  previewTimer = setTimeout(async () => {
    try {
      const {frames, interval} = await api("/api/preview", body);
      if (version !== previewVersion) return;
      let frame = 0;
      paint(frames[frame]);
      if (frames.length > 1) {
        animationTimer = setInterval(() => {
          frame = (frame + 1) % frames.length;
          paint(frames[frame]);
        }, interval);
      }
    } catch (error) {
      if (version === previewVersion) el("feedback").textContent = error.message;
    }
  }, 160);
}

function selectIcon(key) {
  selected = key;
  for (const button of el("icons").children) {
    button.setAttribute("aria-pressed", String(button.dataset.icon === key));
  }
  refreshPreview();
}

input.addEventListener("input", () => selectIcon(null));
document.querySelector("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = selection();
  if (!body || !online || sending) return;
  sending = true;
  updateSend();
  try {
    await api("/api/messages", body);
    el("feedback").textContent = "Bloop queued!";
  } catch (error) {
    el("feedback").textContent = error.message;
  } finally {
    sending = false;
    updateSend();
  }
});

async function poll() {
  try {
    const state = await api("/api/status");
    online = state.online;
    el("connection").textContent = online ? "● Matrix ready" : "○ Waiting for the matrix";
    el("waiting").textContent = state.waiting + " waiting";
    const active = state.messages.filter((item) => item.state === "Starting" || item.state === "Displaying");
    const queued = state.messages.filter((item) => item.position !== null);
    const recent = state.messages.filter((item) => ["Done", "Interrupted"].includes(item.state)).slice(-4).reverse();
    const rows = [...active, ...queued, ...recent].map((item) => {
      const row = document.createElement("li");
      row.textContent = item.label + " · " + item.state + (item.position ? " #" + item.position : "");
      return row;
    });
    if (!rows.length) {
      const empty = document.createElement("li");
      empty.textContent = "No Bloops yet.";
      rows.push(empty);
    }
    el("messages").replaceChildren(...rows);
  } catch {
    online = false;
    el("connection").textContent = "○ Connection lost";
  } finally {
    updateSend();
    setTimeout(poll, 1000);
  }
}

paint(blank);
poll();
api("/api/icons").then((icons) => {
  for (const [key, emoji] of Object.entries(icons)) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.icon = key;
    button.textContent = emoji;
    button.setAttribute("aria-label", key);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      input.value = "";
      selectIcon(key);
    });
    el("icons").append(button);
  }
}).catch(() => { el("feedback").textContent = "Reload the page to load the emoji picker."; });
