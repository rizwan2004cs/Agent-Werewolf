import { useState } from "react";
import { sendSpeech, sendVote } from "../api";

const ROLE_EMOJI = { wolf: "🐺", seer: "🔮", villager: "🧑‍🌾" };

// The human player's control panel (play-yourself games). Shows your secret
// role/knowledge, and — when the loop is waiting on YOU — a speak box or vote
// buttons. The rest of the time you're watching the village like a spectator.
export default function PlayPanel({ state }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const you = state?.you;
  const awaiting = state?.awaiting;
  if (!you) return null;

  const me = state.players?.find((p) => p.idx === you.idx);
  const dead = me && !me.alive;
  const myTurnSpeak = awaiting?.kind === "speak" && awaiting.playerIdx === you.idx;
  const myTurnVote = awaiting?.kind === "vote" && awaiting.playerIdx === you.idx;

  const submitSpeech = async () => {
    if (!text.trim()) return;
    setBusy(true);
    try { await sendSpeech(text); setText(""); } finally { setBusy(false); }
  };
  const submitVote = async (name) => {
    setBusy(true);
    try { await sendVote(name); } finally { setBusy(false); }
  };

  return (
    <section className="play-panel">
      <div className="you-banner">
        <span>You are</span> <b>{you.name}</b>
        <span className={`role-tag ${you.role}`}>{ROLE_EMOJI[you.role]} {you.role}</span>
        {dead && <span className="you-dead">💀 eliminated</span>}
      </div>

      {you.partner && (
        <div className="secret wolf">🐺 Your werewolf partner: <b>{you.partner}</b></div>
      )}
      {you.seer && (
        <div className="secret seer">🔮 You investigated <b>{you.seer.name}</b> — they are a <b>{you.seer.role}</b></div>
      )}

      {myTurnSpeak && (
        <div className="your-turn">
          <div className="turn-label">🗣️ Your turn to speak — convince the village</div>
          <textarea
            rows={3}
            value={text}
            disabled={busy}
            placeholder="Say something to the table… (the agents can't tell you're human)"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submitSpeech(); }}
          />
          <button className="btn start" disabled={busy || !text.trim()} onClick={submitSpeech}>
            Send {busy ? "…" : "▶"}
          </button>
        </div>
      )}

      {myTurnVote && (
        <div className="your-turn">
          <div className="turn-label">🗳️ Your vote — who is eliminated?</div>
          <div className="vote-opts">
            {awaiting.options.map((n) => (
              <button key={n} className="btn toggle" disabled={busy} onClick={() => submitVote(n)}>
                {n}
              </button>
            ))}
          </div>
        </div>
      )}

      {!myTurnSpeak && !myTurnVote && (
        <div className="watching">
          {dead
            ? "You're out — watch how it plays out."
            : "Watching the village… you'll be prompted on your turn."}
        </div>
      )}
    </section>
  );
}
