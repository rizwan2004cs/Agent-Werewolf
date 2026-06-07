import { useEffect, useState } from "react";
import { connect, currentAccount, previewClaim, claimWinnings } from "../wallet";

const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };
const TITLES = { game_winner: "Game winner", who_voted_out: "Voted out" };

function short(h) {
  return h ? h.slice(0, 6) + "…" + h.slice(-4) : "";
}

// Sponsored payouts: the backend already SENT these to the winner's wallet —
// this just shows the connected user what landed (with tx hash when live).
function SponsoredPayouts({ payouts }) {
  const account = currentAccount();
  const mine = (payouts || []).filter(
    (p) => account && p.address?.toLowerCase() === account.toLowerCase()
  );
  if (!mine.length) return null;
  return (
    <div className="claims">
      <h4>💸 Sent to your wallet</h4>
      {mine.map((p, i) => (
        <div key={i} className="claim-row">
          <span>market #{p.marketId}</span>
          <span className="payout">{p.amount} MON</span>
          <span className="none">{p.txHash ? `tx ${short(p.txHash)}` : "auto-paid"}</span>
        </div>
      ))}
    </div>
  );
}

// Claim panel: preflights stakeOf/claimed on each resolved market so the user
// only sees a Claim button when there's actually MON to collect.
function Claims({ markets }) {
  const [account, setAccount] = useState(currentAccount());
  const [rows, setRows] = useState(null);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  // marketId < 0 means the on-chain openMarket failed (chain not configured),
  // so there's nothing to claim — skip them or getMarket(-1) throws.
  const resolved = (markets || []).filter((m) => m.resolved && m.marketId >= 0);

  useEffect(() => {
    if (!account || !resolved.length || !window.ethereum) return;
    let on = true;
    (async () => {
      try {
        const out = [];
        for (const m of resolved) out.push({ m, ...(await previewClaim(m.marketId)) });
        if (on) setRows(out);
      } catch (e) {
        if (on) setMsg(e.message);
      }
    })();
    return () => { on = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account, resolved.length]);

  if (!resolved.length) return null;

  const onConnect = async () => {
    try { setAccount(await connect()); setMsg(null); }
    catch (e) { setMsg(e.message); }
  };

  const onClaim = async (marketId) => {
    setMsg(null); setBusy(true);
    try {
      const hash = await claimWinnings(marketId);
      setMsg(`✅ Claimed! tx ${short(hash)}`);
      setRows((rs) => rs?.map((r) => (r.m.marketId === marketId ? { ...r, payout: "0", done: true } : r)));
    } catch (e) {
      setMsg("⚠ " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="claims">
      <h4>💰 Your winnings</h4>
      {!account && <button className="btn connect" onClick={onConnect}>🦊 Connect to check winnings</button>}
      {account && !rows && !msg && <div className="muted">Checking the chain…</div>}
      {rows?.map(({ m, payout, done }) => (
        <div key={m.marketId} className="claim-row">
          <span>{TITLES[m.type] || m.type}: <b>{m.winningOption}</b></span>
          {parseFloat(payout) > 0 ? (
            <>
              <span className="payout">{payout} MON</span>
              <button className="btn claim" disabled={busy} onClick={() => onClaim(m.marketId)}>Claim</button>
            </>
          ) : (
            <span className="none">{done ? "claimed ✓" : "no winnings"}</span>
          )}
        </div>
      ))}
      {msg && <div className="claim-msg">{msg}</div>}
    </div>
  );
}

export default function GameOverOverlay({ state, onNewGame }) {
  if (!state || state.phase !== "ended") return null;
  const winner = state.winner;
  return (
    <div className="overlay">
      <div className="overlay-card">
        <div className={`overlay-winner ${winner}`}>
          {winner === "wolves" ? "🐺 Wolves win" : "🧑‍🌾 Village wins"}
        </div>
        <div className="overlay-roles">
          {state.players.map((p) => (
            <div key={p.idx} className={`reveal-row ${p.role}`}>
              <span>{ROLE_EMOJI[p.role]}</span>
              <span className="rv-name">{p.name}</span>
              <span className="rv-role">{p.role}</span>
              <span className="rv-state">{p.alive ? "survived" : "eliminated"}</span>
            </div>
          ))}
        </div>
        <SponsoredPayouts payouts={state.payouts} />
        <Claims markets={state.markets} />
        <button className="btn start big" onClick={onNewGame}>▶ New game</button>
      </div>
    </div>
  );
}
