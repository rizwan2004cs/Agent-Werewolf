import Character from "./Character";
import PrizePot from "./PrizePot";

// Fit the ring to the viewport so nothing hides behind the betting bar / header.
function ringRadius() {
  const h = typeof window !== "undefined" ? window.innerHeight : 800;
  const w = typeof window !== "undefined" ? window.innerWidth : 1200;
  const byHeight = (h - 470) / 2;   // leave room for header + betting bar + labels
  const byWidth = w * 0.34;
  return Math.max(140, Math.min(230, Math.round(Math.min(byHeight, byWidth))));
}

function ringStyle(idx, total, radius) {
  const a = (idx / total) * 2 * Math.PI - Math.PI / 2; // start at top, clockwise
  return {
    left: `calc(50% + ${Math.cos(a) * radius}px)`,
    top: `calc(50% + ${Math.sin(a) * radius}px)`,
    transform: "translate(-50%, -50%)",
  };
}

// Latest "real thought" per speaker (skip the (night)/(vote) bookkeeping lines).
function latestThoughts(reasoning) {
  const map = {};
  for (const r of reasoning || []) {
    const t = r.thought || "";
    if (t.startsWith("(night)") || t.startsWith("(vote)")) continue;
    map[r.speaker] = t;
  }
  return map;
}

export default function VillageScene({ state, godMode }) {
  if (!state || state.phase === "idle" || !state.players?.length) {
    return (
      <div className="scene empty">
        <PrizePot pot={state?.pot ?? "—"} phase="idle" />
        <div className="empty-hint">Press ▶ Start to gather the village</div>
      </div>
    );
  }
  const total = state.players.length;
  const radius = ringRadius();
  const thoughts = godMode ? latestThoughts(state.privateReasoning) : {};
  return (
    <div className="scene">
      <PrizePot
        pot={state.pot}
        phase={state.phase}
        round={state.round}
        maxRounds={state.maxRounds}
      />
      {state.players.map((p) => (
        <Character
          key={p.idx}
          player={p}
          isSpeaking={state.speakingIdx === p.idx}
          godMode={godMode}
          thought={thoughts[p.name]}
          style={ringStyle(p.idx, total, radius)}
        />
      ))}
    </div>
  );
}
