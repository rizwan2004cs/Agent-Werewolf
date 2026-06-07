// A villager seated at the table: pixel-art avatar, nameplate, speaking glow,
// death state, role tags. The spoken line itself is shown in the SpeakerStage,
// not here, so the table stays readable.
export default function Character({ player, isSpeaking, godMode, style }) {
  const avatar = `https://api.dicebear.com/9.x/pixel-art/svg?seed=${player.avatarSeed}`;
  const dead = !player.alive;
  const tagRole = player.revealedRole || (godMode ? player.role : null);

  return (
    <div
      className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`}
      style={style}
    >
      <div className="avatar-wrap">
        <img className="avatar" src={avatar} alt={player.name} />
        {dead && <span className="tombstone">🪦</span>}
        {isSpeaking && <span className="speaking-dot">💬</span>}
      </div>
      <div className="nameplate">{player.name}</div>
      {tagRole && (
        <div className={`role-tag ${tagRole} ${player.revealedRole ? "revealed" : ""}`}>
          {tagRole}
        </div>
      )}
    </div>
  );
}
