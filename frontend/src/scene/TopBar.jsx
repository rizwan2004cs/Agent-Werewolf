export default function TopBar({ state, mode, screen, onToggleMode, onStart, onHome }) {
  const phase = state?.phase ?? "idle";
  const running = phase !== "idle" && phase !== "ended";
  const isPlay = screen === "play";
  return (
    <header className="topbar">
      <div className="brand">🐺 PACK</div>
      <div className="tagline">{isPlay ? "Play yourself · 1 human + 6 agents" : "AI werewolves · humans bet · Monad referees"}</div>
      {state?.agentProvider && (
        <div className={`llm-badge ${state.agentProvider === "mock" ? "mock" : "live"}`}>
          {state.agentProvider === "mock" ? "⚠ MOCK AGENTS" : `🤖 ${state.agentProvider}`}
        </div>
      )}
      <div className="spacer" />
      {state?.winner && (
        <div className={`winner-badge ${state.winner}`}>🏆 {state.winner} win</div>
      )}
      <button className="btn" onClick={onHome}>🏠 Home</button>
      <button className="btn start" onClick={onStart} disabled={running}>
        ▶ {phase === "ended" ? "New game" : "Start"}
      </button>
      {!isPlay && (
        <button className="btn toggle" onClick={onToggleMode}>
          {mode === "god" ? "👁 God mode" : "🎲 Bettor mode"}
        </button>
      )}
    </header>
  );
}
