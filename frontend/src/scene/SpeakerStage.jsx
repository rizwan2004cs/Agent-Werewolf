// Visual-novel speaking view: when an agent talks, their portrait rises with a
// parchment dialogue box (what they SAY). In god mode a thought cloud floats
// above them (what they're REALLY thinking). Hidden in bettor mode (fog of war).
export default function SpeakerStage({ player, speech, thought }) {
  if (!player || !speech) return null;
  const portrait = `https://api.dicebear.com/9.x/pixel-art/svg?seed=${player.avatarSeed}`;

  return (
    <div className="speaker-stage" key={player.idx + speech.slice(0, 12)}>
      <div className="stage-portrait-col">
        {thought && (
          <div className="thought-cloud">
            <span className="thought-label">🧠 really thinking…</span>
            <span className="thought-body">{thought}</span>
            <span className="thought-puff puff1" />
            <span className="thought-puff puff2" />
          </div>
        )}
        <img className="stage-portrait" src={portrait} alt={player.name} />
      </div>

      <div className="dialogue-box">
        <div className="dialogue-name">{player.name}</div>
        <div className="dialogue-text">{speech}</div>
      </div>
    </div>
  );
}
