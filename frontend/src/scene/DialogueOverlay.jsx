import { useState } from "react";

// Subject-focus dialogue (JRPG style): when an agent speaks, their portrait +
// name banner + line take over the bottom of the stage — the discussion is the
// show. In god mode the hidden thought rides along underneath (dramatic irony).
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const FACES = ["🧑‍🦰", "🧑‍🦱", "🧔", "🧑‍🦳", "👱", "🧑‍🎤", "🧓"];

// Latest real thought for this speaker (skip (night)/(vote) bookkeeping lines).
function latestThought(reasoning, name) {
  for (let i = (reasoning?.length ?? 0) - 1; i >= 0; i--) {
    const r = reasoning[i];
    if (r.speaker !== name) continue;
    const t = r.thought || "";
    if (t.startsWith("(night)") || t.startsWith("(vote)")) continue;
    return t;
  }
  return null;
}

export default function DialogueOverlay({ state, godMode }) {
  const [imgOk, setImgOk] = useState(true);
  const idx = state?.speakingIdx;
  const player = idx == null ? null : state?.players?.find((p) => p.idx === idx);
  if (!player || !player.currentSpeech) return null;

  const color = COLORS[player.idx % COLORS.length];
  const seed = encodeURIComponent(player.avatarSeed || player.name);
  const avatar = `https://api.dicebear.com/9.x/pixel-art/svg?seed=${seed}`;
  const thought = godMode ? latestThought(state.privateReasoning, player.name) : null;

  return (
    <div className="dialogue-overlay">
      <div className="dlg-portrait" style={{ "--c": color }}>
        {imgOk ? (
          <img src={avatar} alt={player.name} onError={() => setImgOk(false)} />
        ) : (
          <span className="dlg-face">{FACES[player.idx % FACES.length]}</span>
        )}
      </div>
      <div className="dlg-box">
        <div className="dlg-name">✦ {player.name} ✦</div>
        <div className="dlg-text">{player.currentSpeech}</div>
        {thought && <div className="dlg-thought">💭 {thought}</div>}
      </div>
    </div>
  );
}
