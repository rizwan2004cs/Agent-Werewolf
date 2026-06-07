export default function TopBar({ state, mode, onToggleMode, onStart }) {
  const phase = state?.phase ?? "idle";
  const running = phase !== "idle" && phase !== "ended";
  return (
    <header className="topbar">
      <div className="brand">🐺 PACK</div>
      <div className="tagline">AI werewolves · humans bet · Monad referees</div>
      <div className="spacer" />
      {state?.winner && (
        <div className={`winner-badge ${state.winner}`}>🏆 {state.winner} win</div>
      )}
      <button className="btn start" onClick={onStart} disabled={running}>
        ▶ {phase === "ended" ? "New game" : "Start"}
      </button>
      <button className="btn toggle" onClick={onToggleMode}>
        {mode === "god" ? "👁 God mode" : "🎲 Bettor mode"}
      </button>
    </header>
  );
}
