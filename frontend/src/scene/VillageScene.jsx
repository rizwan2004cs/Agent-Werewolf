import { useEffect, useRef, useState } from "react";
import Character from "./Character";
import PrizePot from "./PrizePot";
import SpeakerStage from "./SpeakerStage";
import { ringStyle } from "../lib/ring";

// A round table with the cast seated around it. When someone speaks, the
// SpeakerStage overlays their portrait + dialogue (+ thought cloud in god mode).
export default function VillageScene({ state, godMode }) {
  const ref = useRef(null);
  const [radius, setRadius] = useState(220);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      setRadius(Math.max(120, Math.min(w, h) / 2 - 95));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  if (!state || state.phase === "idle") {
    return (
      <div className="scene empty" ref={ref}>
        Press ▶ Start to gather the table
      </div>
    );
  }

  const total = state.players.length;
  const speaker = state.players.find((p) => p.idx === state.speakingIdx);
  const speaking = speaker?.currentSpeech ? speaker : null;
  // current speaker's latest private thought (god mode only — fog of war)
  const thought =
    godMode && speaking
      ? [...(state.privateReasoning || [])]
          .reverse()
          .find((r) => r.speaker === speaking.name)?.thought
      : null;

  const tableSize = radius * 1.35;

  return (
    <div className="scene" ref={ref}>
      <div
        className="village-table"
        style={{ width: tableSize, height: tableSize }}
      />
      <PrizePot pot={state.pot} phase={state.phase} round={state.round} />
      {state.players.map((p) => (
        <Character
          key={p.idx}
          player={p}
          isSpeaking={state.speakingIdx === p.idx}
          godMode={godMode}
          style={ringStyle(p.idx, total, radius)}
        />
      ))}
      <SpeakerStage player={speaking} speech={speaking?.currentSpeech} thought={thought} />
    </div>
  );
}
