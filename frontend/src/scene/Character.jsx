import SpeechBubble from "./SpeechBubble";
import ThoughtBubble from "./ThoughtBubble";

// Among Us-style crewmate colours, one per seat.
const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

export default function Character({ player, isSpeaking, godMode, thought, style }) {
  const dead = !player.alive;
  const color = COLORS[player.idx % COLORS.length];
  const role = godMode ? player.role : null;
  const shownRole = player.revealedRole || role;

  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      {isSpeaking && player.currentSpeech && <SpeechBubble text={player.currentSpeech} />}

      <div className="crewmate" style={{ "--c": color }}>
        <div className="cm-backpack" />
        <div className="cm-body">
          <div className="cm-visor" />
        </div>
        <div className="cm-legs"><span /><span /></div>
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
