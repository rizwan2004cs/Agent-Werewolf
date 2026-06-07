// A dashed "thinking" cloud shown under a character in god mode — the hidden
// scheme they'd never say out loud (dramatic irony).
export default function ThoughtBubble({ text }) {
  return (
    <div className="thought-bubble">
      <span className="tb-dots">💭</span>
      {text}
    </div>
  );
}
