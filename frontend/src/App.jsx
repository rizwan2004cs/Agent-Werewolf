import { useEffect, useRef, useState } from "react";
import { fetchState, startGame } from "./api";
import TopBar from "./scene/TopBar";
import HomeScreen from "./scene/HomeScreen";
import VillageScene from "./scene/VillageScene";
import DialogueOverlay from "./scene/DialogueOverlay";
import DiscussionFeed from "./scene/DiscussionFeed";
import ReasoningPanel from "./scene/ReasoningPanel";
import GameOverOverlay from "./scene/GameOverOverlay";
import BettingPanel from "./betting/BettingPanel";
import PlayPanel from "./play/PlayPanel";
import "./styles.css";

export default function App() {
  // screen: "home" (chooser) | "betting" (watch + bet) | "play" (you're a player)
  const [screen, setScreen] = useState("home");
  const [mode, setMode] = useState("god"); // god|bettor — betting screen only
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);

  // What view mode we poll in: play games use the fog-aware "player" view.
  const pollMode = screen === "play" ? "player" : mode;
  const pollRef = useRef(pollMode);
  pollRef.current = pollMode;

  useEffect(() => {
    if (screen === "home") return undefined;
    let active = true;
    const tick = async () => {
      try {
        const s = await fetchState(pollRef.current);
        if (active) { setState(s); setErr(null); }
      } catch (e) {
        if (active) setErr(e.message);
      }
    };
    tick();
    const id = setInterval(tick, 500);
    return () => { active = false; clearInterval(id); };
  }, [screen]);

  const begin = async (kind) => {
    setState(null);
    setScreen(kind === "human" ? "play" : "betting");
    if (kind !== "human") setMode("god");
    try { await startGame(kind); } catch (e) { setErr(e.message); }
  };

  const goHome = () => { setScreen("home"); setState(null); };

  if (screen === "home") {
    return <HomeScreen onBetting={() => begin("betting")} onPlay={() => begin("human")} />;
  }

  const phase = state?.phase ?? "idle";
  const isNight = phase === "night" || phase === "setup";
  const isPlay = screen === "play";
  const godMode = !isPlay && mode === "god";
  const playing = phase !== "idle";

  return (
    <div className={`app ${isNight ? "night" : "day"} ${isPlay ? "player" : mode}`}>
      <TopBar
        state={state}
        mode={mode}
        screen={screen}
        onToggleMode={() => setMode((m) => (m === "god" ? "bettor" : "god"))}
        onStart={() => begin(isPlay ? "human" : "betting")}
        onHome={goHome}
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
            {isPlay
              ? <PlayPanel state={state} />
              : godMode && <ReasoningPanel reasoning={state?.privateReasoning} players={state?.players} />}
          </aside>
        )}
      </div>

      {screen === "betting" && !godMode && <BettingPanel state={state} />}
      <GameOverOverlay state={state} onNewGame={() => begin(isPlay ? "human" : "betting")} onHome={goHome} />
    </div>
  );
}
