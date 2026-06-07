// Cloud-style speech bubble. `below` renders it under the avatar (used for
// top-arc characters so it never clips the top of the viewport).
export default function SpeechBubble({ text, below }) {
  return (
    <div className={`speech-bubble ${below ? "below" : ""}`}>
      {text}
      <div className="speech-tail" />
    </div>
  );
}
