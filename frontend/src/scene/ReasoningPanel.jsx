// God-mode dramatic irony: what the agents are really thinking, as it happens.
export default function ReasoningPanel({ reasoning }) {
  const items = (reasoning || []).slice(-9).reverse();
  return (
    <aside className="reasoning-panel">
      <h3>🧠 What they're really thinking</h3>
      {items.length === 0 && <div className="muted">Secrets will surface here…</div>}
      {items.map((r, i) => (
        <div key={i} className={`thought ${r.role}`}>
          <b>{r.speaker}</b>
          {r.role && <span className={`mini-role ${r.role}`}>{r.role}</span>}
          <i>{r.thought}</i>
        </div>
      ))}
    </aside>
  );
}
