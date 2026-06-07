import Character from "./Character";
import PrizePot from "./PrizePot";

function ringStyle(idx, total, radius = 240) {
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
          style={ringStyle(p.idx, total)}
        />
      ))}
    </div>
  );
}
