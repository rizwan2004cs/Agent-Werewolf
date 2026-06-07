import { useEffect, useRef } from "react";

// Stable colour per speaker name.
const COLORS = ["#7dd3fc", "#f9a8d4", "#86efac", "#fcd34d", "#c4b5fd", "#fda4af"];
function colorFor(name) {
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % COLORS.length;
  return COLORS[h];
}

export function DiscussionFeed({ log }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log?.length]);

  return (
    <div className="feed">
      <h3>💬 Discussion</h3>
      <div className="feed-scroll">
        {(!log || log.length === 0) && <div className="muted">Waiting for the village to speak…</div>}
        {log?.map((e, i) => (
          <div key={i} className="line" style={{ animationDelay: "0s" }}>
            <span className="speaker" style={{ color: colorFor(e.speaker) }}>{e.speaker}</span>
            <span className="text">{e.text}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
