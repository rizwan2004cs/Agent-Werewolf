import SpeechBubble from "./SpeechBubble";
import ThoughtBubble from "./ThoughtBubble";

// Distinct colour + character per seat — emoji renders offline (no network).
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const FACES = ["🦊", "🐯", "🐻", "🐼", "🦉", "🐵", "🐸"];
const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

export default function Character({ player, isSpeaking, godMode, thought, style }) {
  const dead = !player.alive;
  const color = COLORS[player.idx % COLORS.length];
  const face = FACES[player.idx % FACES.length];
  const role = godMode ? player.role : null;
  const shownRole = player.revealedRole || role;

  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      {isSpeaking && player.currentSpeech && <SpeechBubble text={player.currentSpeech} />}

      <div className="pavatar" style={{ "--c": color }}>
        <span className="pavatar-emoji">{face}</span>
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
