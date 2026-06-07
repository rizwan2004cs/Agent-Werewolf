import { useEffect, useRef } from "react";

// Persistent, scrollable transcript of the whole game discussion so humans can
// read at their own pace (speech bubbles pop and fade; this is the record).
export default function DiscussionLog({ log, speakingName }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [log?.length]);

  return (
    <section className="discussion-log">
      <h3>💬 Discussion</h3>
      <div className="log-scroll" ref={ref}>
        {!log?.length && <div className="log-empty">No discussion yet…</div>}
        {log?.map((e, i) => (
          <div
            className={`log-entry ${e.speaker === speakingName ? "live" : ""}`}
            key={i}
          >
            <div className="log-meta">
              <span className="log-round">R{e.round}</span>
              <span className="log-speaker">{e.speaker}</span>
            </div>
            <div className="log-text">{e.text}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
