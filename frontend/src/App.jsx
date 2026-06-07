import { useState } from "react";
import { startGame } from "./api/client";
import { useGameState } from "./hooks/useGameState";
import TopBar from "./scene/TopBar";
import VillageScene from "./scene/VillageScene";
import DiscussionLog from "./scene/DiscussionLog";
import GameOverOverlay from "./scene/GameOverOverlay";
import HistoryPanel from "./scene/HistoryPanel";
import PhaseToast from "./scene/PhaseToast";
import VoteTally from "./scene/VoteTally";
import BettingPanel from "./betting/BettingPanel";

// Layout: TopBar, then a 3-column row — left transcript, center table, right
// betting (bettor mode). God-mode "what they're thinking" is now the thought
// cloud over the speaker (in the scene), so there's no side reasoning panel to
// collide with the betting panel.
export default function App() {
  const [mode, setMode] = useState("bettor"); // "god" | "bettor" — audience bets by default
  const [showHistory, setShowHistory] = useState(false);
  const state = useGameState(mode);

  const phase = state?.phase ?? "idle";
  const isNight = phase === "night" || phase === "setup" || phase === "idle";

  return (
    <div className={`app ${isNight ? "night" : "day"} mode-${mode}`}>
      <TopBar
        state={state}
        mode={mode}
        onToggleMode={() => setMode((m) => (m === "god" ? "bettor" : "god"))}
        onStart={startGame}
        onShowHistory={() => setShowHistory(true)}
      />

      <div className="layout">
        <aside className="col col-left">
          <DiscussionLog
            log={state?.discussionLog}
            speakingName={
              state?.players?.find((p) => p.idx === state?.speakingIdx)?.name ?? null
            }
          />
        </aside>

        <main className="col col-center">
          <VillageScene state={state} godMode={mode === "god"} />
          <VoteTally state={state} />
        </main>

        {mode === "bettor" && (
          <aside className="col col-right">
            <BettingPanel state={state} />
          </aside>
        )}
      </div>

      <PhaseToast phase={phase} />
      <HistoryPanel open={showHistory} onClose={() => setShowHistory(false)} />
      {phase === "ended" && <GameOverOverlay state={state} onNewGame={startGame} />}
    </div>
  );
}
