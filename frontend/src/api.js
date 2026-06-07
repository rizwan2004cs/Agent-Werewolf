const BASE = import.meta.env.VITE_ORCHESTRATOR_URL || "http://localhost:8000";
export const EXPLORER = import.meta.env.VITE_EXPLORER_URL || "https://testnet.monadvision.com";

export async function fetchState(mode) {
  const r = await fetch(`${BASE}/state?mode=${mode}`);
  if (!r.ok) throw new Error(`state ${r.status}`);
  return r.json();
}

export async function startGame() {
  return fetch(`${BASE}/control/start`, { method: "POST" });
}
