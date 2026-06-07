import { useState } from "react";
import SpeechBubble from "./SpeechBubble";
import ThoughtBubble from "./ThoughtBubble";

// A distinct colour per player seat (used for the avatar frame).
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

export default function Character({ player, isSpeaking, godMode, thought, style }) {
  const [imgOk, setImgOk] = useState(true);
  const dead = !player.alive;
  const color = COLORS[player.idx % COLORS.length];
  const role = godMode ? player.role : null;
  const shownRole = player.revealedRole || role;
  const seed = encodeURIComponent(player.avatarSeed || player.name);
  const avatar = `https://api.dicebear.com/9.x/adventurer/svg?seed=${seed}&radius=50`;

  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      {isSpeaking && player.currentSpeech && <SpeechBubble text={player.currentSpeech} />}

      <div className="pavatar" style={{ "--c": color }}>
        {imgOk ? (
          <img className="pavatar-img" src={avatar} alt={player.name} onError={() => setImgOk(false)} />
        ) : (
          <svg className="pavatar-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-5 0-9 2.6-9 6v2h18v-2c0-3.4-4-6-9-6z" />
          </svg>
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
