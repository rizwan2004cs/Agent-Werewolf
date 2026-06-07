// HTTP client for the backend. The only place that knows the backend URL.
const BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function fetchState(mode) {
  const res = await fetch(`${BASE}/state?mode=${mode}`);
  if (!res.ok) throw new Error(`/state ${res.status}`);
  return res.json();
}

export async function startGame() {
  const res = await fetch(`${BASE}/control/start`, { method: "POST" });
  return res.json();
}

export async function fetchHistory() {
  const res = await fetch(`${BASE}/history`);
  if (!res.ok) throw new Error(`/history ${res.status}`);
  return res.json();
}
