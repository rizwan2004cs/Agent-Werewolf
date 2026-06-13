import { useEffect, useRef, useState } from "react";
import { fetchState, startGame, pingHealth } from "./api";
import TopBar from "./scene/TopBar";
import HomeScreen from "./scene/HomeScreen";
import VillageScene from "./scene/VillageScene";
import DialogueOverlay from "./scene/DialogueOverlay";
import DiscussionFeed from "./scene/DiscussionFeed";
import ReasoningPanel from "./scene/ReasoningPanel";
import GameOverOverlay from "./scene/GameOverOverlay";
import WakeOverlay from "./scene/WakeOverlay";
import BettingPanel from "./betting/BettingPanel";
import PlayPanel from "./play/PlayPanel";
import "./styles.css";

export default function App() {
  // screen: "home" (chooser) | "betting" (watch + bet) | "play" (you're a player)
  const [screen, setScreen] = useState("home");
  const [mode, setMode] = useState("god"); // god|bettor — betting screen only
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);
  const [ready, setReady] = useState(false); // backend is awake & answering
  const [bootSecs, setBootSecs] = useState(0); // time spent waiting for the first live scene

  // What view mode we poll in: play games use the fog-aware "player" view.
  const pollMode = screen === "play" ? "player" : mode;
  const pollRef = useRef(pollMode);
  pollRef.current = pollMode;

  // Warm the backend as soon as the app loads. Render's free tier sleeps after
  // ~15 min idle and takes 30-60s to wake; probing on the home screen means it's
  // usually awake by the time the user actually picks a mode.
  useEffect(() => {
    let active = true;
    let timer;
    const probe = async () => {
      if (!active) return;
      const ok = await pingHealth();
      if (!active) return;
      setReady(ok);
      if (!ok) timer = setTimeout(probe, 2500);
    };
    probe();
    return () => { active = false; clearTimeout(timer); };
  }, []);

  // Poll game state while a game screen is open. Keeps the LAST good state on a
  // transient error so the scene never blanks out mid-game.
  useEffect(() => {
    if (screen === "home") return undefined;
    let active = true;
    let inflight = false;
    const tick = async () => {
      if (inflight) return; // don't pile up requests against a cold backend
      inflight = true;
      try {
        const s = await fetchState(pollRef.current);
        if (active) { setState(s); setErr(null); setReady(true); }
      } catch (e) {
        if (active) { setErr(e.message); setReady(false); }
      } finally {
        inflight = false;
      }
    };
    tick();
    const id = setInterval(tick, 600);
    return () => { active = false; clearInterval(id); };
  }, [screen]);

  const phase = state?.phase ?? "idle";
  const hasScene = !!state && phase !== "idle";
  // We're on a game screen but don't have a live scene yet → waking / setting up.
  const booting = screen !== "home" && !hasScene;

  // Count the wait so the wake overlay can reassure with a live timer.
  useEffect(() => {
    if (!booting) { setBootSecs(0); return undefined; }
    const start = Date.now();
    const id = setInterval(() => setBootSecs(Math.floor((Date.now() - start) / 1000)), 500);
    return () => clearInterval(id);
  }, [booting]);

  const begin = async (kind) => {
    setState(null);
    setErr(null);
    setScreen(kind === "human" ? "play" : "betting");
    if (kind !== "human") setMode("god");
    try { await startGame(kind); } catch (e) { setErr(e.message); }
  };

  const goHome = () => { setScreen("home"); setState(null); setErr(null); };

  if (screen === "home") {
    return (
      <HomeScreen
        ready={ready}
        onBetting={() => begin("betting")}
        onPlay={() => begin("human")}
      />
    );
  }

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
      {/* Gentle reconnect notice — only when we already had a scene and lost it,
          not during the expected cold-start wait (the wake overlay covers that). */}
      {err && !booting && (
        <div className="err-banner reconnect">↻ Connection hiccup — reconnecting to the server…</div>
      )}

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
      {booting && <WakeOverlay ready={ready} secs={bootSecs} onHome={goHome} />}
      <GameOverOverlay state={state} onNewGame={() => begin(isPlay ? "human" : "betting")} onHome={goHome} />
    </div>
  );
}
