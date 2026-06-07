import { PlayerCard } from "../components/PlayerCard";
import { DiscussionFeed } from "../components/DiscussionFeed";

function PrivateReasoning({ reasoning }) {
  return (
    <aside className="reasoning">
      <h3>🧠 What they're really thinking</h3>
      <div className="feed-scroll">
        {(!reasoning || reasoning.length === 0) && <div className="muted">No private thoughts yet…</div>}
        {reasoning?.map((r, i) => (
          <div key={i} className="thought">
            <b>{r.speaker}</b>: <i>{r.thought}</i>
          </div>
        ))}
      </div>
    </aside>
  );
}

export function GodMode({ state }) {
  return (
    <div className="mode-god">
      <div className="board-wrap">
        <div className={`board ${state.phase === "night" ? "night" : ""}`}>
          {state.players.map((p) => (
            <PlayerCard key={p.idx} player={p} godMode />
          ))}
        </div>
        {state.phase === "night" && <div className="night-overlay">🌙 The village sleeps…</div>}
      </div>
      <div className="god-grid">
        <DiscussionFeed log={state.discussionLog} />
        <PrivateReasoning reasoning={state.privateReasoning} />
      </div>
    </div>
  );
}
