import { useEffect, useState } from "react";
import { fetchState, startGame } from "./api";
import { GodMode } from "./modes/GodMode";
import { BettorMode } from "./modes/BettorMode";
import "./App.css";

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

function Header({ mode, setMode, state, onStart }) {
  const winner = state.winner;
  return (
    <header className="topbar">
      <div className="brand">🐺 PACK</div>
      <div className="status">
        <span className={`phase phase-${state.phase}`}>{PHASE_LABEL[state.phase] || state.phase}</span>
        {state.round != null && state.phase !== "idle" && (
          <span className="round">Round {state.round}/{state.maxRounds}</span>
        )}
        {state.pot != null && <span className="pot">💰 {state.pot} MON</span>}
        {winner && <span className={`winner winner-${winner}`}>🏆 {winner} win</span>}
      </div>
      <div className="controls">
        <button
          className="start"
          onClick={onStart}
          disabled={state.phase !== "idle" && state.phase !== "ended"}
        >
          ▶ New game
        </button>
        <button className="toggle" onClick={() => setMode((m) => (m === "god" ? "bettor" : "god"))}>
          {mode === "god" ? "👁 God mode" : "🎲 Bettor mode"}
        </button>
      </div>
    </header>
  );
}

export default function App() {
  const [mode, setMode] = useState("god");
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        const s = await fetchState(mode);
        if (active) {
          setState(s);
          setErr(null);
        }
      } catch (e) {
        if (active) setErr(e.message);
      }
    };
    tick();
    const id = setInterval(tick, 500);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [mode]);

  const onStart = async () => {
    try {
      await startGame();
    } catch (e) {
      setErr(e.message);
    }
  };

  if (!state) {
    return (
      <div className="loading">
        <div className="brand-lg">🐺 PACK</div>
        <p>{err ? `Can't reach orchestrator: ${err}` : "Connecting to orchestrator…"}</p>
        <p className="muted">
          Start it with <code>uvicorn server:app --reload</code> in <code>orchestrator/</code>.
        </p>
      </div>
    );
  }

  return (
    <div className={`app ${mode}`}>
      <Header mode={mode} setMode={setMode} state={state} onStart={onStart} />
      {err && <div className="err-banner">⚠ {err}</div>}
      {state.phase === "idle" ? (
        <div className="idle-hero">
          <h1>Agent Werewolf</h1>
          <p>AI agents play social deduction. Humans bet. The chain referees.</p>
          <button className="start big" onClick={onStart}>
            ▶ Start a game
          </button>
        </div>
      ) : mode === "god" ? (
        <GodMode state={state} />
      ) : (
        <BettorMode state={state} />
      )}
    </div>
  );
}
