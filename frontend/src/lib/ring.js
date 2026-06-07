// Pure layout math: evenly place `total` items on a circle, starting at the top.
export function ringStyle(idx, total, radius = 230) {
  const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
  return {
    left: `calc(50% + ${Math.cos(angle) * radius}px)`,
    top: `calc(50% + ${Math.sin(angle) * radius}px)`,
    transform: "translate(-50%, -50%)",
  };
}
