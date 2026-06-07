import { placeBet } from "../wallet";

function odds(pools, opt) {
  const total = Object.values(pools || {}).reduce((a, b) => a + parseFloat(b || 0), 0);
  const o = parseFloat((pools || {})[opt] || 0);
  return o > 0 ? (total / o).toFixed(2) + "×" : "—";
}

const TITLES = { game_winner: "Who wins the game?", who_voted_out: "Who gets voted out?" };

function Market({ m, frozen }) {
  const win = m.resolved ? m.winningOption : null;
  return (
    <div className={`market ${m.resolved ? "resolved" : ""}`}>
      <div className="market-title">{TITLES[m.type] || m.type}</div>
      <div className="options">
        {m.options.map((opt, i) => (
          <button
            key={opt}
            className={`bet-btn ${win === opt ? "won" : ""}`}
            disabled={frozen || m.resolved}
            onClick={() => placeBet(m.marketId, i).catch((e) => alert(e.message))}
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
  if (!state || !state.markets?.length) return null;
  const frozen = !state.bettingOpen;
  const active = state.markets.filter((m) => !m.resolved);
  const settled = state.markets.filter((m) => m.resolved);
  return (
    <div className="betting-bar">
      <div className="bet-head">
        {frozen ? (
          <span className="bet-locked">🔒 Betting closed — watch the discussion</span>
        ) : (
          <span className="bet-cta">💰 Place your bet!</span>
        )}
      </div>
      <div className="markets-row">
        {active.map((m) => <Market key={m.marketId} m={m} frozen={frozen} />)}
        {settled.map((m) => <Market key={m.marketId} m={m} frozen />)}
      </div>
    </div>
  );
}
