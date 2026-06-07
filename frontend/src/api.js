const BASE =
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_ORCHESTRATOR_URL ||
  "http://localhost:8000";

export const EXPLORER = import.meta.env.VITE_EXPLORER_URL || "";

export async function fetchState(mode) {
  const r = await fetch(`${BASE}/state?mode=${mode}`);
  if (!r.ok) throw new Error(`state ${r.status}`);
  return r.json();
}

export async function startGame(kind = "betting") {
  return fetch(`${BASE}/control/start?kind=${kind}`, { method: "POST" });
}

// "Play yourself" — submit the human player's discussion line.
export async function sendSpeech(text) {
  return fetch(`${BASE}/control/say`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

// "Play yourself" — submit the human player's vote.
export async function sendVote(target) {
  return fetch(`${BASE}/control/vote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target }),
  });
}

// House-sponsored bet: gas-free, no MON needed — just your address.
// The operator stakes on-chain for you; winnings arrive in your wallet.
export async function postBet(marketId, option, address, amount) {
  const r = await fetch(`${BASE}/bet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marketId, option, address, amount: parseFloat(amount) }),
  });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || "bet failed");
  return j.message;
}
