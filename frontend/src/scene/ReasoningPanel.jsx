// God-mode dramatic-irony panel: what agents are really thinking.
const ROLE_CLASS = { wolf: "wolf", seer: "seer", villager: "villager" };

export default function ReasoningPanel({ reasoning }) {
  return (
    <section className="reasoning-panel">
      <h3>🧠 What they're really thinking</h3>
      <div className="panel-scroll">
        {!reasoning?.length && (
          <div className="log-empty">Private thoughts appear during discussion…</div>
        )}
        {reasoning?.slice(-20).map((r, i) => (
          <div key={i} className="thought">
            <b className={ROLE_CLASS[r.role] || ""}>{r.speaker}</b>
            <span className="thought-role"> ({r.role})</span>: <i>{r.thought}</i>
          </div>
        ))}
      </div>
    </section>
  );
}
