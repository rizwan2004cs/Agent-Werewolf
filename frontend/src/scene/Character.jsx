import { useState } from "react";

// Distinct colour per seat. Pixel-art avatar (DiceBear "pixel-art"), with a
// human-emoji fallback if the image service is blocked/offline.
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const FACES = ["🧑‍🦰", "🧑‍🦱", "🧔", "🧑‍🦳", "👱", "🧑‍🎤", "🧓"];
const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

export default function Character({ player, isSpeaking, godMode, style }) {
  const [imgOk, setImgOk] = useState(true);
  const dead = !player.alive;
  const color = COLORS[player.idx % COLORS.length];
  const seed = encodeURIComponent(player.avatarSeed || player.name);
  const avatar = `https://api.dicebear.com/9.x/pixel-art/svg?seed=${seed}`;
  const role = godMode ? player.role : null;
  const shownRole = player.revealedRole || role;

  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      <div className="pavatar" style={{ "--c": color }}>
        {imgOk ? (
          <img className="pavatar-img" src={avatar} alt={player.name} onError={() => setImgOk(false)} />
        ) : (
          <span className="pavatar-emoji">{FACES[player.idx % FACES.length]}</span>
        )}
        {dead && <span className="tombstone">🪦</span>}
      </div>

      {/* first name on the ring chip; the full name shows in the dialogue box / feed */}
      <div className="nameplate">{player.name.split(" ")[0]}</div>
      {shownRole && (
        <div className={`role-tag ${shownRole} ${player.revealedRole ? "revealed" : ""}`}>
          {ROLE_EMOJI[shownRole] || ""} {shownRole}
        </div>
      )}
    </div>
  );
}
