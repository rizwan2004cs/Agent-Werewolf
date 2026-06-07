// Shows the live vote roll + running tally during voting/resolution.
export default function VoteTally({ state }) {
  const active =
    state &&
    (state.phase === "voting" || state.phase === "resolution") &&
    state.votes?.length;
  if (!active) return null;

  const counts = {};
  for (const v of state.votes) counts[v.target] = (counts[v.target] || 0) + 1;
  const leader = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];

  return (
    <aside className="vote-tally">
      <h3>🗳️ The Vote</h3>
      <div className="vote-rolls">
        {state.votes.map((v, i) => (
          <div className="vote-row" key={i}>
            {v.voter} <span className="vote-arrow">→</span>{" "}
            <b className={v.target === leader ? "vote-leader" : ""}>{v.target}</b>
          </div>
        ))}
      </div>
      <div className="vote-counts">
        {Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .map(([name, n]) => (
            <div className="count-row" key={name}>
              <span>{name}</span>
              <span className="count-bar">
                <span
                  className="count-fill"
                  style={{ width: `${(n / state.votes.length) * 100}%` }}
                />
              </span>
              <span className="count-n">{n}</span>
            </div>
          ))}
      </div>
    </aside>
  );
}
