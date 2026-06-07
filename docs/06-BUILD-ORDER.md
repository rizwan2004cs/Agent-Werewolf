# 06 — Build Order

> Build in this exact sequence. Each step ends with something runnable. Never move on with a broken state.

## Milestone 1 — Backend game loop (off-chain, console only)
Goal: a full Werewolf game plays out in the terminal with believable discussion. No chain, no frontend yet.

1. Scaffold `backend/` with `requirements.txt`, `.env` (user provides `ANTHROPIC_API_KEY`).
2. Build `game/state.py` (data model) and the `new_game()` roster setup.
3. Build `game/prompts.py` with all prompt templates from `04-BACKEND.md`.
4. Build `game/agents.py` — LLM calls for night pick, seer, speak, vote.
5. Build `game/loop.py` but **stub out `chain.py`** (make every chain call a no-op that returns fake market ids / empty pools).
6. Add a `__main__` that calls `run_game(new_game())` and prints each phase + every speech + the vote + the winner.

✅ **Done when:** running `python -m game.loop` plays a complete game start to finish in the console and it reads like a real Werewolf game.

## Milestone 2 — Serve state over HTTP
Goal: the frontend can read game state.

1. Build `server.py` (FastAPI) with `/health`, `/control/start`, `/state`.
2. Make `loop.STATE` a module global the loop updates as it runs; run the game in a background thread on `/control/start`.
3. Implement `serialize(state, mode)` with **fog-of-war stripping** for bettor mode.

✅ **Done when:** `POST /control/start` then polling `GET /state?mode=god` shows the game progressing phase by phase; `?mode=bettor` hides unrevealed roles.

## Milestone 3 — Frontend village scene (reads state, no betting yet)
Goal: watch the game as a beautiful village.

1. Scaffold `frontend/` (Vite React). Add `.env`.
2. Build `api.js`, `App.jsx` with the 500ms poll + mode toggle + Start button.
3. Build `VillageScene`, `Character`, `SpeechBubble`, `PrizePot`, `TopBar` per `05-FRONTEND.md`.
4. Wire day/night background, speaking glow, speech-cloud pop, dead/tombstone.
5. Build `ReasoningPanel` for god mode.

✅ **Done when:** pressing Start runs a game and you watch characters speak (clouds pop one at a time), the sky shifts night/day, and dead characters grey out. God mode shows roles + reasoning.

## Milestone 4 — Deploy the contract to Monad
Goal: the betting contract is live.

1. Create `contract/WerewolfArena.sol` from `03-CONTRACT.md`.
2. Deploy via Remix to Monad testnet (operator = deployer wallet).
3. Save the address + ABI into `backend/abi.json`, `frontend/src/abi.json`, and both `.env`s.

✅ **Done when:** the contract is deployed and you can call `openMarket` from Remix manually.

## Milestone 5 — Wire backend to chain
Goal: markets open/freeze/resolve for real.

1. Implement the real `game/chain.py` (web3.py) replacing the stub.
2. Hook `open_market` / `freeze_market` / `resolve_market` / `get_pools` into the loop phases.
3. Wrap every chain call in try/except — a failed tx must not crash the game.

✅ **Done when:** a game run creates real markets on-chain and resolves them; `/state` shows real pool numbers.

## Milestone 6 — Frontend betting
Goal: users bet real test MON.

1. Build `wallet.js` (ethers v6 + MetaMask, Monad chain switch).
2. Build `BettingPanel`: live odds from pools, pulsing CTA when open, lock state during discussion.
3. Wire `placeBet`; add a claim button on the game-over overlay.

✅ **Done when:** in bettor mode you can place a bet via MetaMask, see the pool/odds update on the next poll, and the market locks during discussion.

## Milestone 7 — Polish + demo safety
1. Tune `PERSONA` + prompts over several runs so wolves are believable and villagers reason.
2. Tighten pacing beats (holds at night/morning/elimination).
3. Build the game-over overlay: simultaneous role reveal + winner banner + prize.
4. Record a backup screen capture of a full clean game in case live fails.

✅ **Done when:** a full game looks and feels like a polished game from Start to winner reveal, with betting working, and you have a backup recording.

## Dependency notes
- Milestones 1–3 need no blockchain at all — build the whole game + UI against the stubbed chain first.
- The contract (M4) can be deployed in parallel any time after M1.
- M5/M6 layer chain on top of an already-working game. If chain breaks at demo time, the game still runs and you fall back to the stub.

## Definition of MVP done
A spectator presses Start, watches 7 AI characters play a believable round of Werewolf in a day/night village with speech clouds, while a bettor (in bettor mode) places a MON bet that settles on Monad when the game ends — all without manual intervention.
