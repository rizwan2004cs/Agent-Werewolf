function impliedOdds(pools, option) {
  const total = Object.values(pools).reduce((a, b) => a + parseFloat(b || 0), 0);
  const opt = parseFloat(pools[option] || 0);
  return opt > 0 ? (total / opt).toFixed(2) + "x" : "—";
}

const PRETTY = {
  game_winner: "Who wins the game?",
  who_voted_out: "Who gets voted out?",
  catches_wolf_this_round: "Village catches a wolf this round?",
  seer_survives: "Does the seer survive?",
};

function Market({ m }) {
  const total = Object.values(m.pools).reduce((a, b) => a + parseFloat(b || 0), 0);
  return (
    <div className={`market ${m.resolved ? "resolved" : ""}`}>
      <h4>
        {PRETTY[m.type] || m.type}
        <span className="pot-sm">{total.toFixed(2)} MON</span>
      </h4>
      <div className="options">
        {m.options.map((opt) => {
          const win = m.resolved && m.winningOption === opt;
          return (
            <button
              key={opt}
              className={`opt ${win ? "win" : ""}`}
              disabled={m.frozen || m.resolved}
              onClick={() => alert(`Demo: connect a wallet to bet on "${opt}".`)}
            >
              <span>{opt}</span>
              <span className="odds">{impliedOdds(m.pools, opt)}</span>
            </button>
          );
        })}
      </div>
      {m.resolved && <div className="resolved-tag">✓ resolved: {m.winningOption}</div>}
    </div>
  );
}

export function BettingPanel({ state }) {
  const frozen = !state.bettingOpen;
  const markets = (state.markets || []).filter((m) => !m.resolved);
  const settled = (state.markets || []).filter((m) => m.resolved);
  return (
    <div className="betting">
      <h3>🎲 Markets</h3>
      {frozen && <div className="frozen-banner">🔒 Betting closed — discussion in progress</div>}
      {markets.length === 0 && settled.length === 0 && <div className="muted">No open markets yet.</div>}
      {markets.map((m) => <Market key={m.marketId} m={m} />)}
      {settled.length > 0 && <div className="settled-head">Settled</div>}
      {settled.map((m) => <Market key={m.marketId} m={m} />)}
    </div>
  );
}
