import { useEffect, useState } from "react";
import { postBet, fetchBalance } from "../api";

function odds(pools, opt) {
  const total = Object.values(pools || {}).reduce((a, b) => a + parseFloat(b || 0), 0);
  const o = parseFloat((pools || {})[opt] || 0);
  return o > 0 ? (total / o).toFixed(2) + "×" : "—";
}

const TITLES = { game_winner: "Who wins the game?", who_voted_out: "Who gets voted out?" };

function Market({ m, frozen, onBet, busy }) {
  const win = m.resolved ? m.winningOption : null;
  return (
    <div className={`market ${m.resolved ? "resolved" : ""}`}>
      <div className="market-title">{TITLES[m.type] || m.type}</div>
      <div className="options">
        {m.options.map((opt, i) => (
          <button
            key={opt}
            className={`bet-btn ${win === opt ? "won" : ""}`}
            disabled={frozen || m.resolved || busy}
            onClick={() => onBet(m.marketId, i, opt)}
          >
            <span className="opt-name">{opt}</span>
            <span className="odds">{odds(m.pools, opt)}</span>
          </button>
        ))}
      </div>
      {m.resolved && <div className="market-result">✓ {m.winningOption}</div>}
    </div>
  );
}

export default function BettingPanel({ state }) {
  const [amount, setAmount] = useState("5");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [balance, setBalance] = useState(null);

  // Load the play-money balance once, then refresh as the game progresses
  // (winnings get credited server-side when markets resolve).
  const refreshBalance = async () => {
    try { setBalance(await fetchBalance()); } catch { /* ignore */ }
  };
  useEffect(() => { refreshBalance(); }, []);
  useEffect(() => { refreshBalance(); }, [state?.phase, state?.payouts?.length]);

  if (!state || !state.markets?.length) return null;
  const frozen = !state.bettingOpen;
  const active = state.markets.filter((m) => !m.resolved);
  const settled = state.markets.filter((m) => m.resolved);

  const onBet = async (marketId, optionIdx, opt) => {
    setMsg(null);
    setBusy(true);
    try {
      const { message, balance: bal } = await postBet(marketId, opt, amount);
      if (typeof bal === "number") setBalance(bal);
      setMsg(`✅ ${message}`);
    } catch (e) {
      setMsg("⚠ " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="betting-bar">
      <div className="bet-head">
        {frozen ? (
          <span className="bet-locked">🔒 Betting closed — watch the discussion</span>
        ) : (
          <span className="bet-cta">💰 Place your bet! (play money — no wallet needed)</span>
        )}
        <span className="bet-controls">
          <label className="amount">
            Stake
            <input
              type="number" min="1" step="1" value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            pts
          </label>
          <span className="wallet-chip">
            🪙 {balance == null ? "…" : balance.toFixed(2)} pts
          </span>
        </span>
      </div>
      {msg && <div className="bet-msg">{msg}</div>}
      <div className="markets-row">
        {active.map((m) => <Market key={m.marketId} m={m} frozen={frozen} onBet={onBet} busy={busy} />)}
        {settled.map((m) => <Market key={m.marketId} m={m} frozen onBet={onBet} busy={busy} />)}
      </div>
    </div>
  );
}
