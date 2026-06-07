import { PlayerCard } from "../components/PlayerCard";
import { DiscussionFeed } from "../components/DiscussionFeed";
import { BettingPanel } from "../components/BettingPanel";

export function BettorMode({ state }) {
  return (
    <div className="mode-bettor">
      <div className="board-wrap">
        <div className={`board ${state.phase === "night" ? "night" : ""}`}>
          {state.players.map((p) => (
            <PlayerCard key={p.idx} player={p} godMode={false} />
          ))}
        </div>
        {state.phase === "night" && <div className="night-overlay">🌙 The village sleeps…</div>}
      </div>
      <div className="bettor-grid">
        <DiscussionFeed log={state.discussionLog} />
        <BettingPanel state={state} />
      </div>
    </div>
  );
}
