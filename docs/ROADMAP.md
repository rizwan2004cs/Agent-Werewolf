# Pack — Build Roadmap & TODO

> Phased plan to a winning Blitz submission. Spec: [SPEC.md](SPEC.md).
> Order is deliberate: **local works → real agents (the win) → deploy → submit.**
> ✅ done · 🔄 in progress · ⬜ todo · ⚠ blocked on user

---

## Phase 0 — Skeleton ✅ DONE
- [x] Monorepo scaffold: `contracts / orchestrator / frontend / shared / docs`
- [x] Contracts compile + pass smoke tests; ABIs exported to `shared/abi/`
- [x] Orchestrator: state, prompts, agents (mock), chain bridge (mock), loop, FastAPI
- [x] Frontend: god/bettor modes, board, feed, reasoning panel, betting panel — builds
- [x] Full mock game verified end-to-end over HTTP; fog-of-war confirmed
- [x] Initial commit

## Phase 1 — Local game is great (mock) 🔄
- [ ] Tune phase pacing so the feed reads like a broadcast (not a dump)
- [ ] Frontend pacing beats: night dim, morning flip, typewriter speeches, vote-bar fill, role-flip
- [ ] Game-over sequence: flip all cards, show winner + (mock) tx links
- [ ] Sanity-run 5+ mock games; fix any loop/edge-case bugs

## Phase 2 — Real LLM agents (THE WIN) ⚠ needs `ANTHROPIC_API_KEY`
- [ ] Drop in `ANTHROPIC_API_KEY`; flip agents from mock → real (`agents.py` already wired)
- [ ] Tune prompts: wolves deceive subtly, villagers name suspects, seer plays its info
- [ ] Run 5+ real games, read transcripts, iterate personalities until **watchable**
- [ ] Confirm private-reasoning (dramatic irony) reads well in god mode
- [ ] Tune token/latency so a full game fits comfortably in the demo window

## Phase 3 — Record & Replay (backup + latency hedge) ⬜
- [ ] Orchestrator: dump the `/state` timeline of a finished game to `shared/replays/*.json`
- [ ] Frontend: replay player that steps a recorded timeline with original pacing (no backend)
- [ ] Record one excellent real-agent game as the canonical demo replay

## Phase 4 — Deploy to Monad testnet ⚠ needs funded private key (faucet MON)
- [ ] Fund deployer wallet from the Monad faucet
- [ ] `contracts/.env` → deploy both contracts (`npm run deploy`); capture `shared/deployed.json`
- [ ] Verify contracts via the Monad verification API
- [ ] Orchestrator `.env`: `MOCK_CHAIN=0`, contract addresses, funded `ORCHESTRATOR_KEY`, agent wallets funded
- [ ] Run a full game **on testnet**; confirm createGame / vote / resolve / payout txs land
- [ ] Grab explorer links for the demo

## Phase 5 — Host the app ⬜
- [ ] Frontend → **Vercel**; set `VITE_ORCHESTRATOR_URL` + `VITE_EXPLORER_URL`
- [ ] Orchestrator: run locally behind a **tunnel** (ngrok/cloudflared) for the live demo
      *(stateful loop — do NOT attempt serverless; Render/Railway only if it's quick)*
- [ ] Verify hosted frontend drives a live game; CORS ok

## Phase 6 — Submit & demo ⬜
- [ ] Fork `monad-developers/monad-blitz-bangalore`; drop the monorepo in; push (public)
- [ ] Root README demo-ready: what it is, why novel, how to run, deployed addresses + links
- [ ] Submit on `blitz.devnads.com`: fork URL + demo URL — **before 5:30 PM**
- [ ] Rehearse the 3-min demo; capture screenshots + a screen recording as fallback

---

## Critical path & owners
1. **Phase 2 real agents** is the single highest-leverage item — it's what the innovation vote rewards.
2. **Phase 3 replay** de-risks the live demo; do it right after agents are good.
3. **Phases 4–5 deploy** are required for compliance but lower-risk; the tunnel keeps them cheap.

## Blocked-on-user (surface at the right phase, don't ask early)
- ⚠ `ANTHROPIC_API_KEY` → unblocks Phase 2
- ⚠ Funded Monad testnet private key (+ faucet MON) → unblocks Phase 4
- ⚠ **Detailed game logic** (coming) → may revise the provisional rules in SPEC §6 / `loop.py`
