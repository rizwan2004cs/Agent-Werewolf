const ROLE_EMOJI = { wolf: "🐺", villager: "🧑‍🌾", seer: "🔮" };

export function PlayerCard({ player, godMode }) {
  const role = player.role || player.revealedRole;
  const showRole = (godMode && player.role) || player.revealedRole;
  return (
    <div className={`card ${player.alive ? "" : "dead"}`}>
      <div className="avatar">{player.alive ? "🧑" : "💀"}</div>
      <div className="name">{player.name}</div>
      {showRole && <div className={`role role-${role}`}>{ROLE_EMOJI[role] || ""} {role}</div>}
      {player.lastSpeech && <div className="bubble">{player.lastSpeech}</div>}
    </div>
  );
}
