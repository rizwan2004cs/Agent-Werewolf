import { useEffect, useState } from "react";
import { fetchHistory } from "../api/client";

// Past completed games (persisted server-side). Opened from the TopBar.
export default function HistoryPanel({ open, onClose }) {
  const [games, setGames] = useState([]);

  useEffect(() => {
    if (open) fetchHistory().then(setGames).catch(() => setGames([]));
  }, [open]);

  if (!open) return null;
  return (
    <div className="overlay" onClick={onClose}>
      <div className="history-card" onClick={(e) => e.stopPropagation()}>
        <div className="history-head">
          <h2>📜 Game History</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>
        {!games.length && <div className="log-empty">No completed games yet.</div>}
        <div className="history-list">
          {games.map((g) => (
            <div className="history-row" key={g.gameId}>
              <div className="history-row-head">
                <span className="history-id">Game #{g.gameId}</span>
                <span className={`role-tag revealed ${g.winner === "village" ? "villager" : "wolf"}`}>
                  {g.winner === "village" ? "🏡 Village" : "🐺 Wolves"}
                </span>
                <span className="history-date">
                  {new Date(g.endedAt * 1000).toLocaleString()}
                </span>
              </div>
              <div className="history-roles">
                {g.players.map((p) => (
                  <span key={p.name} className={`history-chip ${p.role}`}>
                    {p.name}:{p.role}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
