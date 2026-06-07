export default function SpeechBubble({ text }) {
  return (
    <div className="speech-bubble">
      {text}
      <div className="speech-tail" />
    </div>
  );
}
