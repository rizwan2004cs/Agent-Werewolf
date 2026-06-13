const PHASE_LABEL = {
  idle: "Press Start",
  setup: "Setup",
  night: "Night falls",
  morning: "Morning",
  discussion: "Discussion",
  voting: "Voting",
  resolution: "Resolution",
  ended: "Game Over",
};

export default function PrizePot({ pot, phase, round, maxRounds }) {
  return (
    <div className="prize-pot">
      <div className="pot-glow" />
      <div className="pot-amount">💰 {pot}</div>
      <div className="pot-unit">pts</div>
      <div className="pot-phase">{PHASE_LABEL[phase] || phase}</div>
      {phase !== "idle" && phase !== "ended" && (
        <div className="pot-round">Round {round}/{maxRounds}</div>
      )}
    </div>
  );
}
