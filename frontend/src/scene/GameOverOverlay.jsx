const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

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
        <button className="btn start big" onClick={onNewGame}>▶ New game</button>
      </div>
    </div>
  );
}
