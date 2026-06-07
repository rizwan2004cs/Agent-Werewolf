import { useState } from "react";
import { connect, currentAccount, placeBet } from "../wallet";

function odds(pools, opt) {
  const total = Object.values(pools || {}).reduce((a, b) => a + parseFloat(b || 0), 0);
  const o = parseFloat((pools || {})[opt] || 0);
  return o > 0 ? (total / o).toFixed(2) + "×" : "—";
}

const TITLES = { game_winner: "Who wins the game?", who_voted_out: "Who gets voted out?" };

function short(a) {
  return a ? a.slice(0, 6) + "…" + a.slice(-4) : "";
}

function Market({ m, frozen, amount, onBet, busy }) {
  const win = m.resolved ? m.winningOption : null;
  const offchain = m.marketId < 0; // openMarket failed (chain not configured)
  return (
    <div className={`market ${m.resolved ? "resolved" : ""}`}>
      <div className="market-title">{TITLES[m.type] || m.type}</div>
      <div className="options">
        {m.options.map((opt, i) => (
          <button
            key={opt}
            className={`bet-btn ${win === opt ? "won" : ""}`}
            disabled={frozen || m.resolved || busy || offchain}
            onClick={() => onBet(m.marketId, i, opt)}
          >
            <span className="opt-name">{opt}</span>
            <span className="odds">{odds(m.pools, opt)}</span>
          </button>
        ))}
      </div>
      {m.resolved && <div className="market-result">✓ {m.winningOption}</div>}
      {offchain && <div className="market-result">⚠ off-chain — betting unavailable</div>}
    </div>
  );
}

export default function BettingPanel({ state }) {
  const [account, setAccount] = useState(currentAccount());
  const [amount, setAmount] = useState("0.05");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  if (!state || !state.markets?.length) return null;
  const frozen = !state.bettingOpen;
  const active = state.markets.filter((m) => !m.resolved);
  const settled = state.markets.filter((m) => m.resolved);

  const onConnect = async () => {
    try { setAccount(await connect()); setMsg(null); }
    catch (e) { setMsg(e.message); }
  };

  // Direct on-chain bet: the bettor stakes MON from their own wallet via
  // MetaMask; the contract pays winners on claim (see GameOverOverlay).
  const onBet = async (marketId, optionIdx, opt) => {
    setMsg(null);
    if (marketId < 0) {
      setMsg("⚠ This market isn't on-chain (server chain config missing) — betting unavailable.");
      return;
    }
    try {
      if (!account) setAccount(await connect());
      setBusy(true);
      const hash = await placeBet(marketId, optionIdx, amount);
      setMsg(`✅ Bet ${amount} MON on ${opt} — tx ${short(hash)}`);
    } catch (e) {
      setMsg("⚠ " + (e.shortMessage || e.message));
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
          <span className="bet-cta">💰 Place your bet! (staked from your wallet)</span>
        )}
        <span className="bet-controls">
          <label className="amount">
            Stake
            <input
              type="number" min="0.01" step="0.01" value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            MON
          </label>
          {account ? (
            <span className="wallet-chip">🦊 {short(account)}</span>
          ) : (
            <button className="btn connect" onClick={onConnect}>🦊 Connect MetaMask</button>
          )}
        </span>
      </div>
      {msg && <div className="bet-msg">{msg}</div>}
      <div className="markets-row">
        {active.map((m) => <Market key={m.marketId} m={m} frozen={frozen} amount={amount} onBet={onBet} busy={busy} />)}
        {settled.map((m) => <Market key={m.marketId} m={m} frozen amount={amount} onBet={onBet} busy={busy} />)}
      </div>
    </div>
  );
}
