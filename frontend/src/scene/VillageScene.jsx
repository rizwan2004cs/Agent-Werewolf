import { useEffect, useState } from "react";
import Character from "./Character";
import PrizePot from "./PrizePot";

// Pure-CSS pixel-art atmosphere layered behind the village ring. Decorative
// only (pointer-events: none) and painted under the characters/pot.
function SceneBackdrop() {
  return (
    <div className="scene-bg" aria-hidden="true">
      <div className="sky" />
      <div className="celestial" />
      <div className="stars" />
      <div className="clouds" />
      <div className="treeline">
        {Array.from({ length: 22 }).map((_, i) => (
          <i className="pine" key={i} style={{ "--i": i }} />
        ))}
      </div>
      <div className="huts">
        <i className="hut" /><i className="hut tall" /><i className="hut" />
      </div>
      <div className="ground-glow" />
      {Array.from({ length: 12 }).map((_, i) => (
        <i className="firefly" key={i} style={{ "--i": i }} />
      ))}
      <div className="vignette" />
    </div>
  );
}

// Fit the ring inside the ACTUAL stage box (measured live with a
// ResizeObserver), so characters never slide under the top bar, sidebar or
// betting bar. Margins reserve space for the avatar + name chip + role tag.
const MARGIN_X = 135;   // half character width + side breathing room
const MARGIN_TOP = 120; // avatar half above the ring line
const MARGIN_BOTTOM = 175; // avatar half + nameplate + role tag below it

function useRingRadius() {
  const [el, setEl] = useState(null);
  const [radius, setRadius] = useState(170);
  useEffect(() => {
    if (!el) return;
    const measure = () => {
      const { width: w, height: h } = el.getBoundingClientRect();
      const byH = (h - MARGIN_TOP - MARGIN_BOTTOM) / 2;
      const byW = w / 2 - MARGIN_X;
      setRadius(Math.max(140, Math.min(320, Math.round(Math.min(byH, byW)))));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [el]);
  return [setEl, radius];
}

function ringStyle(idx, total, radius) {
  const a = (idx / total) * 2 * Math.PI - Math.PI / 2; // start at top, clockwise
  return {
    left: `calc(50% + ${Math.cos(a) * radius}px)`,
    top: `calc(50% + ${Math.sin(a) * radius}px)`,
    transform: "translate(-50%, -50%)",
  };
}

export default function VillageScene({ state, godMode }) {
  const [sceneRef, radius] = useRingRadius();
  if (!state || state.phase === "idle" || !state.players?.length) {
    return (
      <div className="scene empty" ref={sceneRef}>
        <SceneBackdrop />
        <PrizePot pot={state?.pot ?? "—"} phase="idle" />
        <div className="empty-hint">Press ▶ Start to gather the village</div>
      </div>
    );
  }
  const total = state.players.length;
  return (
    <div className="scene" ref={sceneRef}>
      <SceneBackdrop />
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
          style={ringStyle(p.idx, total, radius)}
        />
      ))}
    </div>
  );
}
