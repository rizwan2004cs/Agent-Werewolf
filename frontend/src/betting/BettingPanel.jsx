// The "bid space" (bettor mode, right column). Every wallet's bets aggregate
// into the on-chain pools shown here (read back via /state). Winners split the
// pool on claim (parimutuel). Shows per-option pool (MON), live odds, your
// session stake, and the total pool. Bets go on-chain via MetaMask.
import { useState } from "react";
import { connectWallet, placeBet } from "../wallet";

const AMOUNTS = ["0.05", "0.1", "0.5", "1"];
const TITLE = { game_winner: "Who wins the game?", who_voted_out: "Who gets voted out?" };

function poolTotal(pools) {
  return Object.values(pools || {}).reduce((a, b) => a + parseFloat(b || 0), 0);
}
function oddsFor(pools, opt) {
  const t = poolTotal(pools);
  const o = parseFloat((pools || {})[opt] || 0);
  return o > 0 ? (t / o).toFixed(2) + "×" : "—";
}

export default function BettingPanel({ state }) {
  const [account, setAccount] = useState(null);
  const [amount, setAmount] = useState("0.05");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [stakes, setStakes] = useState({}); // "marketId:optionIdx" -> MON (this session)

  const frozen = !state?.bettingOpen;
  const active = (state?.markets || []).filter((m) => !m.resolved);
  const short = account ? `${account.slice(0, 6)}…${account.slice(-4)}` : null;

  async function onConnect() {
    try {
      setAccount(await connectWallet());
    } catch (e) {
      setMsg(e.message);
    }
  }

  async function onBet(m, i, opt) {
    setBusy(true);
    setMsg(null);
    try {
      if (!account) setAccount(await connectWallet());
      await placeBet(m.marketId, i, amount);
      const key = `${m.marketId}:${i}`;
      setStakes((s) => ({ ...s, [key]: (s[key] || 0) + parseFloat(amount) }));
      setMsg(`✅ Bet ${amount} MON on ${opt}`);
    } catch (e) {
      setMsg(`⚠️ ${e.shortMessage || e.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="betting-panel">
      <div className="bet-head">
        <h3>🎲 Place your bids</h3>
        <button className="connect-btn" onClick={onConnect}>
          {short ? `🟢 ${short}` : "Connect wallet"}
        </button>
      </div>

      <div className={`bet-state ${frozen ? "locked" : "open"}`}>
        {frozen ? "🔒 Betting closed — discussion in progress" : "💰 Betting open"}
      </div>

      <div className="amount-row">
        <span>Stake per bet</span>
        <select
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          disabled={frozen || busy}
        >
          {AMOUNTS.map((a) => (
            <option key={a} value={a}>
              {a} MON
            </option>
          ))}
        </select>
      </div>

      {!active.length && <div className="bet-empty">No open markets yet — start a game.</div>}

      {active.map((m) => {
        const total = poolTotal(m.pools);
        return (
          <div className="bid-market" key={m.marketId}>
            <div className="bid-market-head">
              <span className="bid-title">{TITLE[m.type] ?? m.type}</span>
              <span className="bid-total">{total.toFixed(3)} MON pool</span>
            </div>
            <div className="bid-options">
              {m.options.map((opt, i) => {
                const pool = parseFloat((m.pools || {})[opt] || 0);
                const mine = stakes[`${m.marketId}:${i}`] || 0;
                const pct = total > 0 ? (pool / total) * 100 : 0;
                return (
                  <button
                    className="bid-option"
                    key={opt}
                    disabled={frozen || busy}
                    onClick={() => onBet(m, i, opt)}
                  >
                    <div className="bid-opt-top">
                      <span className="bid-opt-name">{opt}</span>
                      <span className="bid-opt-odds">{oddsFor(m.pools, opt)}</span>
                    </div>
                    <div className="bid-bar">
                      <span className="bid-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <div className="bid-opt-bot">
                      <span>{pool.toFixed(3)} MON</span>
                      {mine > 0 && <span className="bid-mine">you: {mine.toFixed(2)}</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}

      {msg && <div className="bet-msg">{msg}</div>}
    </section>
  );
}
