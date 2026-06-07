import { useEffect, useRef, useState } from "react";
import { fetchState, startGame } from "./api";
import TopBar from "./scene/TopBar";
import VillageScene from "./scene/VillageScene";
import DialogueOverlay from "./scene/DialogueOverlay";
import DiscussionFeed from "./scene/DiscussionFeed";
import ReasoningPanel from "./scene/ReasoningPanel";
import GameOverOverlay from "./scene/GameOverOverlay";
import BettingPanel from "./betting/BettingPanel";
import "./styles.css";

export default function App() {
  const [mode, setMode] = useState("god");
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);
  const modeRef = useRef(mode);
  modeRef.current = mode;

  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        const s = await fetchState(modeRef.current);
        if (active) { setState(s); setErr(null); }
      } catch (e) {
        if (active) setErr(e.message);
      }
    };
    tick();
    const id = setInterval(tick, 500);
    return () => { active = false; clearInterval(id); };
  }, []);

  const onStart = async () => {
    try { await startGame(); } catch (e) { setErr(e.message); }
  };

  const phase = state?.phase ?? "idle";
  const isNight = phase === "night" || phase === "setup";
  const godMode = mode === "god";
  const playing = phase !== "idle";

  return (
    <div className={`app ${isNight ? "night" : "day"} ${mode}`}>
      <TopBar
        state={state}
        mode={mode}
        onToggleMode={() => setMode((m) => (m === "god" ? "bettor" : "god"))}
        onStart={onStart}
      />
      {err && <div className="err-banner">⚠ Can't reach backend ({err}). Is uvicorn running on :8000?</div>}

      <div className="main">
        <div className="stage">
          <VillageScene state={state} godMode={godMode} />
          {playing && <DialogueOverlay state={state} godMode={godMode} />}
          {isNight && playing && <div className="night-toast">🌙 The village sleeps…</div>}
        </div>
        {playing && (
          <aside className="sidebar">
            <DiscussionFeed log={state?.discussionLog} players={state?.players} />
            {godMode && <ReasoningPanel reasoning={state?.privateReasoning} players={state?.players} />}
          </aside>
        )}
      </div>

      {!godMode && <BettingPanel state={state} />}
      <GameOverOverlay state={state} onNewGame={onStart} />
    </div>
  );
}
