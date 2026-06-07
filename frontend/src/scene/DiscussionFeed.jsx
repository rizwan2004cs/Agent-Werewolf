import { useEffect, useRef } from "react";

const COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#f472b6", "#f59e0b", "#a855f7", "#06b6d4"];
function colorFor(name, players) {
  const p = players?.find((x) => x.name === name);
  return p ? COLORS[p.idx % COLORS.length] : "#cbd5e1";
}

export default function DiscussionFeed({ log, players }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log?.length]);

  return (
    <div className="feed">
      <h3>💬 Discussion</h3>
      <div className="feed-scroll">
        {(!log || !log.length) && <div className="muted">The discussion will appear here…</div>}
        {log?.map((e, i) => (
          <div key={i} className="chat-line">
            <b style={{ color: colorFor(e.speaker, players) }}>{e.speaker}</b>
            <span>{e.text}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
