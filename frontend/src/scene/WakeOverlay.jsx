// Shown while we're on a game screen but don't have a live scene yet.
// Two distinct situations, so the message is honest about what's happening:
//   - backend not answering yet  -> the free host is waking from sleep (slow)
//   - backend awake, no scene yet -> dealing roles / warming the agents (fast)
export default function WakeOverlay({ ready, secs, onHome }) {
  // Once we've waited a while with no response, the dyno is almost certainly
  // doing a full cold start — set expectations honestly.
  const longWait = !ready && secs >= 8;

  const title = ready ? "Gathering the village…" : "Waking the server…";
  const msg = ready
    ? "Dealing secret roles and warming up the AI agents. The first turn can take a few seconds."
    : longWait
      ? "This app runs on a free host that goes to sleep when idle. A full wake-up takes about 30–60 seconds — hang tight, it only happens on the first visit."
      : "Connecting to the server…";

  return (
    <div className="overlay wake">
      <div className="overlay-card wake-card">
        <div className="wake-icon">🐺</div>
        <div className="wake-bar"><span style={{ animationDelay: "0s" }} /><span style={{ animationDelay: ".15s" }} /><span style={{ animationDelay: ".3s" }} /></div>
        <div className="wake-title">{title}</div>
        <div className="wake-msg">{msg}</div>
        <div className="wake-secs">
          {secs}s{secs > 75 ? " — almost there, still waking…" : ""}
        </div>
        {secs > 90 && (
          <button className="btn" onClick={onHome}>← Back home</button>
        )}
      </div>
    </div>
  );
}
