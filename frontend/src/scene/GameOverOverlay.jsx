// End-of-game overlay: winner banner + full role reveal + claim winnings.
import { useState } from "react";
import { claimWinnings } from "../wallet";

export default function GameOverOverlay({ state, onNewGame }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  if (!state || state.phase !== "ended") return null;
  const winner = state.winner;
  // Claims pay out on the resolved game_winner market.
  const gw = state.markets?.find((m) => m.type === "game_winner");

  async function onClaim() {
    if (!gw) return;
    setBusy(true);
    setMsg(null);
    try {
      const hash = await claimWinnings(gw.marketId);
      setMsg(`✅ Claimed (${hash.slice(0, 10)}…)`);
    } catch (e) {
      setMsg(`⚠️ ${e.shortMessage || e.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="overlay">
      <div className="overlay-card">
        <div className={`winner-banner ${winner}`}>
          {winner === "village" ? "🏡 Village Wins!" : "🐺 Wolves Win!"}
        </div>
        <div className="reveal-grid">
          {state.players.map((p) => (
            <div key={p.idx} className="reveal-row">
              <span className="reveal-name">{p.name}</span>
              <span className={`role-tag revealed ${p.revealedRole || p.role}`}>
                {p.revealedRole || p.role}
              </span>
            </div>
          ))}
        </div>
        <div className="overlay-pot">Prize pot: {state.pot} MON</div>
        <div className="overlay-actions">
          <button
            className="claim-btn"
            onClick={onClaim}
            disabled={busy || !gw?.resolved}
            title={gw?.resolved ? "Claim if you bet on the winning side" : "Market not resolved yet"}
          >
            {busy ? "Claiming…" : "💸 Claim winnings"}
          </button>
          <button className="newgame-btn" onClick={onNewGame}>
            🔄 New Game
          </button>
        </div>
        {msg && <div className="bet-msg">{msg}</div>}
      </div>
    </div>
  );
}
