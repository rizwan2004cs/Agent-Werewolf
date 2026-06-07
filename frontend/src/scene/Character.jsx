import { useState } from "react";
import SpeechBubble from "./SpeechBubble";
import ThoughtBubble from "./ThoughtBubble";

// Distinct colour per seat. Human-character avatar (DiceBear "personas"), with a
// human-emoji fallback if the image service is blocked/offline.
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const FACES = ["🧑‍🦰", "🧑‍🦱", "🧔", "🧑‍🦳", "👱", "🧑‍🎤", "🧓"];
const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

export default function Character({ player, isSpeaking, godMode, thought, style }) {
  const [imgOk, setImgOk] = useState(true);
  const dead = !player.alive;
  const color = COLORS[player.idx % COLORS.length];
  const seed = encodeURIComponent(player.avatarSeed || player.name);
  const avatar = `https://api.dicebear.com/9.x/personas/svg?seed=${seed}`;
  const role = godMode ? player.role : null;
  const shownRole = player.revealedRole || role;

  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      {isSpeaking && player.currentSpeech && <SpeechBubble text={player.currentSpeech} />}

      <div className="pavatar" style={{ "--c": color }}>
        {imgOk ? (
          <img className="pavatar-img" src={avatar} alt={player.name} onError={() => setImgOk(false)} />
        ) : (
          <span className="pavatar-emoji">{FACES[player.idx % FACES.length]}</span>
        )}
        {dead && <span className="tombstone">🪦</span>}
      </div>

      <div className="nameplate">{player.name}</div>
      {shownRole && (
        <div className={`role-tag ${shownRole} ${player.revealedRole ? "revealed" : ""}`}>
          {ROLE_EMOJI[shownRole] || ""} {shownRole}
        </div>
      )}

      {godMode && isSpeaking && thought && <ThoughtBubble text={thought} />}
    </div>
  );
}
