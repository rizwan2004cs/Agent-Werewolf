// Landing chooser: pick a game type before anything starts.
export default function HomeScreen({ onBetting, onPlay }) {
  return (
    <div className="home">
      <div className="home-card">
        <h1 className="home-title">🐺 PACK</h1>
        <p className="home-sub">AI werewolves · humans bet or play · Monad referees</p>
        <div className="home-modes">
          <button className="home-mode betting" onClick={onBetting}>
            <div className="home-mode-icon">🎲</div>
            <div className="home-mode-name">Betting Arena</div>
            <div className="home-mode-desc">Watch 7 AI agents play. Bet MON on the outcome and claim winnings on-chain.</div>
          </button>
          <button className="home-mode play" onClick={onPlay}>
            <div className="home-mode-icon">🧑‍🌾</div>
            <div className="home-mode-name">Play Yourself</div>
            <div className="home-mode-desc">Join the table as a player with a secret role. Bluff, vote, and survive. No bets.</div>
          </button>
        </div>
      </div>
    </div>
  );
}
