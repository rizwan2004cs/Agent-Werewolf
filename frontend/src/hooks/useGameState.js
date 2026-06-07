import { useEffect, useState } from "react";
import { fetchState } from "../api/client";

// Polls GET /state every `interval` ms for the given view mode.
// Returns the latest state (or null before the first successful poll).
export function useGameState(mode, interval = 500) {
  const [state, setState] = useState(null);

  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        const s = await fetchState(mode);
        if (active) setState(s);
      } catch {
        /* backend not up yet — keep last state, try again next tick */
      }
    };
    tick();
    const id = setInterval(tick, interval);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [mode, interval]);

  return state;
}
