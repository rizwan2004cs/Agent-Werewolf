import { useEffect, useState } from "react";
import { bettorId, fetchBalance } from "../api";

const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };
const TITLES = { game_winner: "Game winner", who_voted_out: "Voted out" };

// Play-money winnings: the backend already credited these to this browser's
// bettor id when the markets resolved. This just shows what landed.
function Winnings({ payouts }) {
  const [balance, setBalance] = useState(null);
  const me = bettorId();
  const mine = (payouts || []).filter(
    (p) => p.address && p.address === me
  );
  useEffect(() => {
    let on = true;
    fetchBalance().then((b) => { if (on) setBalance(b); }).catch(() => {});
    return () => { on = false; };
  }, []);

  const total = mine.reduce((a, p) => a + parseFloat(p.amount || 0), 0);

  return (
    <div className="claims">
      <h4>🪙 Your winnings</h4>
      {balance != null && (
        <div className="claim-row">
          <span>Balance</span>
          <span className="payout">{balance.toFixed(2)} pts</span>
        </div>
      )}
      {mine.length === 0 ? (
        <div className="muted">No winning bets this game.</div>
      ) : (
        mine.map((p, i) => (
          <div key={i} className="claim-row">
            <span>{TITLES[p.type] || p.type}: <b>{p.option}</b></span>
            <span className="payout">+{p.amount} pts</span>
          </div>
        ))
      )}
      {mine.length > 0 && (
        <div className="claim-row">
          <span>Total won</span>
          <span className="payout">+{total.toFixed(2)} pts</span>
        </div>
      )}
    </div>
  );
}

export default function GameOverOverlay({ state, onNewGame, onHome }) {
  if (!state || state.phase !== "ended") return null;
  const winner = state.winner;
  const betting = state.kind !== "human";
  // In play-yourself games, tell the human how THEY did.
  const you = state.you;
  let youResult = null;
  if (you) {
    const wonTeam = (you.role === "wolf") === (winner === "wolves");
    youResult = { won: wonTeam, alive: you.alive };
  }
  return (
    <div className="overlay">
      <div className="overlay-card">
        <div className={`overlay-winner ${winner}`}>
          {winner === "wolves" ? "🐺 Wolves win" : "🧑‍🌾 Village wins"}
        </div>
        {youResult && (
          <div className={`you-result ${youResult.won ? "win" : "lose"}`}>
            {youResult.won ? "🎉 You win!" : "💀 You lose."}{" "}
            ({you.role}, {youResult.alive ? "survived" : "eliminated"})
          </div>
        )}
        <div className="overlay-roles">
          {state.players.map((p) => (
            <div key={p.idx} className={`reveal-row ${p.role}`}>
              <span>{ROLE_EMOJI[p.role]}</span>
              <span className="rv-name">{p.name}{p.isHuman ? " (you)" : ""}</span>
              <span className="rv-role">{p.role}</span>
              <span className="rv-state">{p.alive ? "survived" : "eliminated"}</span>
            </div>
          ))}
        </div>
        {betting && <Winnings payouts={state.payouts} />}
        <div className="overlay-actions">
          <button className="btn start big" onClick={onNewGame}>▶ New game</button>
          <button className="btn big" onClick={onHome}>🏠 Home</button>
        </div>
      </div>
    </div>
  );
}
