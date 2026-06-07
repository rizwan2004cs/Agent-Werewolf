import { useEffect, useRef, useState } from "react";

// Transient banner that pops on each phase change — a pacing beat for the show.
const MESSAGE = {
  setup: "🎲 Place your bets — roles are being dealt",
  night: "🌙 The village sleeps…",
  morning: "☀️ Dawn breaks — a body is found",
  discussion: "💬 Discussion begins",
  voting: "🗳️ The village votes",
  resolution: "⚖️ The verdict is in",
  ended: "🏁 Game over",
};

export default function PhaseToast({ phase }) {
  const [msg, setMsg] = useState(null);
  const prev = useRef(null);

  useEffect(() => {
    if (phase && phase !== prev.current && MESSAGE[phase]) {
      prev.current = phase;
      setMsg(MESSAGE[phase]);
      const t = setTimeout(() => setMsg(null), 2200);
      return () => clearTimeout(t);
    }
  }, [phase]);

  if (!msg) return null;
  return (
    <div className="phase-toast" key={msg}>
      {msg}
    </div>
  );
}
