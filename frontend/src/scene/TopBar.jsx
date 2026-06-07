// Top bar: logo, phase/round badge, pot, Start button, mode toggle.
const PHASE_LABEL = {
  idle: "Idle",
  setup: "Setup",
  night: "Night",
  morning: "Morning",
  discussion: "Discussion",
  voting: "Voting",
  resolution: "Resolution",
  ended: "Game Over",
};

export default function TopBar({ state, mode, onToggleMode, onStart, onShowHistory }) {
  const phase = state?.phase ?? "idle";
  const round = state?.round ?? 0;
  const maxRounds = state?.maxRounds ?? 2;
  const gameId = state?.gameId;

  return (
    <header className="topbar">
      <div className="brand">
        🐺 PACK
        {gameId != null && <span className="game-id">#{gameId}</span>}
      </div>

      <div className="phase-badge">
        <span className={`phase-dot ${phase}`} />
        {PHASE_LABEL[phase] ?? phase}
        {phase !== "idle" && phase !== "ended" && (
          <span className="round-tag">
            Round {round}/{maxRounds}
          </span>
        )}
      </div>

      <div className="topbar-right">
        <div className="pot-badge">💰 {state?.pot ?? "0"} MON</div>
        <button className="ghost-btn" onClick={onShowHistory}>
          📜 History
        </button>
        <button className="mode-toggle" onClick={onToggleMode}>
          {mode === "god" ? "👁 God" : "🎲 Bettor"}
        </button>
        <button className="start-btn" onClick={onStart}>
          ▶ Start
        </button>
      </div>
    </header>
  );
}
