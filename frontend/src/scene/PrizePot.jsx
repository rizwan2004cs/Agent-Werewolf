// Central glowing prize pot. Shows the pot and a short phase caption.
const CAPTION = {
  setup: "Placing bets…",
  night: "🌙 The village sleeps",
  morning: "☀ A body is found",
  discussion: "Who do you trust?",
  voting: "The vote is cast",
  resolution: "…",
  ended: "Game over",
};

export default function PrizePot({ pot, phase, round }) {
  return (
    <div className="prize-pot">
      <div className="pot-amount">{pot} MON</div>
      <div className="pot-caption">{CAPTION[phase] ?? ""}</div>
    </div>
  );
}
