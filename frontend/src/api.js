const BASE =
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_ORCHESTRATOR_URL ||
  "http://localhost:8000";

// A stable, per-browser bettor id (play money is tracked against it server-side).
// No wallet/chain — just a random handle persisted in localStorage.
export function bettorId() {
  const KEY = "pack_bettor_id";
  let id = null;
  try {
    id = localStorage.getItem(KEY);
    if (!id) {
      id = "p_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(KEY, id);
    }
  } catch {
    id = id || "p_anon";
  }
  return id;
}

// fetch with an abort timeout so a sleeping (cold-starting) backend doesn't
// leave requests hanging forever / piling up.
async function timedFetch(url, opts = {}, timeoutMs = 8000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

// Liveness probe used to warm the backend (Render free dynos sleep when idle).
// Returns true once the server answers. Never throws.
export async function pingHealth(timeoutMs = 5000) {
  try {
    const r = await timedFetch(`${BASE}/health`, {}, timeoutMs);
    return r.ok;
  } catch {
    return false;
  }
}

export async function fetchState(mode) {
  const r = await timedFetch(`${BASE}/state?mode=${mode}`, {}, 8000);
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

// Off-chain play-money bet: the backend pools it and pays winners pro-rata.
// Returns { message, balance } (updated play-money balance).
export async function postBet(marketId, option, amount) {
  const r = await fetch(`${BASE}/bet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marketId, option, address: bettorId(), amount: parseFloat(amount) }),
  });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || "bet failed");
  return j;
}

// Current play-money balance for this browser's bettor id.
export async function fetchBalance() {
  const r = await fetch(`${BASE}/wallet?address=${encodeURIComponent(bettorId())}`);
  if (!r.ok) throw new Error(`wallet ${r.status}`);
  const j = await r.json();
  return j.balance;
}
