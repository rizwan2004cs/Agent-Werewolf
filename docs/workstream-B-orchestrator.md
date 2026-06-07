# Workstream B — Orchestrator & Agents

> You own the brain: the game loop, the agents, the prompts, and the bridge to both the chain and the frontend. **The discussion engine is the demo — that's your priority.** Everything else is plumbing around it.

## Your files
- `orchestrator/game/loop.py` — main game loop
- `orchestrator/game/agents.py` — LLM agent wrappers
- `orchestrator/game/prompts.py` — all prompt templates
- `orchestrator/game/chain.py` — web3 contract calls
- `orchestrator/game/state.py` — game state model
- `orchestrator/server.py` — FastAPI serving `/state`

## Build order

### Step 1 (Hour 1) — One agent speaks
Get a single LLM call working with a wolf prompt. Define the state model. Don't touch the chain yet.

```python
# game/state.py
from dataclasses import dataclass, field

@dataclass
class Player:
    idx: int
    name: str
    address: str
    role: str            # "wolf" | "villager" | "seer"
    alive: bool = True
    revealed_role: str | None = None

@dataclass
class GameState:
    game_id: int = 0
    phase: str = "setup"
    round: int = 1
    max_rounds: int = 2
    pot: str = "0"
    players: list[Player] = field(default_factory=list)
    discussion_log: list[dict] = field(default_factory=list)
    private_reasoning: list[dict] = field(default_factory=list)
    night_result: dict | None = None
    votes: list[dict] = field(default_factory=list)
    betting_open: bool = True
    winner: str | None = None

    def alive_players(self):
        return [p for p in self.players if p.alive]
```

```python
# game/agents.py
import os, re, json, random
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"   # fast + cheap for discussion

def call_llm(prompt: str, max_tokens: int = 200) -> str:
    resp = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text

def agent_speak(player, state):
    from .prompts import day_prompt
    text = call_llm(day_prompt(player, state))
    return text.strip()

def agent_vote(player, state):
    from .prompts import vote_prompt
    text = call_llm(vote_prompt(player, state), max_tokens=120)
    m = re.search(r"VOTE:\s*(\w+)", text, re.IGNORECASE)
    if m:
        name = m.group(1)
        target = next((p for p in state.alive_players() if p.name.lower() == name.lower()), None)
        if target and target.idx != player.idx:
            return target, text
    # fallback
    others = [p for p in state.alive_players() if p.idx != player.idx]
    return random.choice(others), text
```

### Step 2 (Hour 2) — Night phase + chain wiring
```python
# game/chain.py
import os, json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
GAME_ADDR = os.environ["GAME_CONTRACT"]
BET_ADDR = os.environ["BETTING_CONTRACT"]

with open("../shared/abi/AgentWerewolf.json") as f:
    GAME_ABI = json.load(f)["abi"]
game = w3.eth.contract(address=GAME_ADDR, abi=GAME_ABI)

def _send(fn, signer_key, value=0):
    acct = w3.eth.account.from_key(signer_key)
    tx = fn.build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "value": value,
        "chainId": int(os.environ["CHAIN_ID"]),
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(h)

def create_game(player_addrs, role_hashes, pot_wei, key):
    return _send(game.functions.createGame(player_addrs, role_hashes), key, value=pot_wei)

def submit_vote(game_id, target_idx, agent_key):
    return _send(game.functions.submitVote(game_id, target_idx), agent_key)

def resolve_vote(game_id, key):
    return _send(game.functions.resolveVote(game_id), key)
```

### Step 3 (Hour 3) — THE DISCUSSION ENGINE (your main job)
This is what wins the room. Spend the most time tuning prompts so wolves are believable and villagers reason. Two rounds, fixed turn order, full context each call.

```python
# game/loop.py
import asyncio, time
from .agents import agent_speak, agent_vote
from . import chain

DISCUSSION_ROUNDS = 2

def run_discussion(state):
    for d in range(DISCUSSION_ROUNDS):
        for p in state.alive_players():
            speech = agent_speak(p, state)
            state.discussion_log.append({
                "round": state.round, "turn": p.idx,
                "speaker": p.name, "text": speech, "ts": int(time.time())
            })
            p.lastSpeech = speech
            time.sleep(1)        # pacing beat for the frontend

def run_voting(state):
    for p in state.alive_players():
        target, reasoning = agent_vote(p, state)
        chain.submit_vote(state.game_id, target.idx, agent_key(p))
        state.votes.append({"voter": p.name, "target": target.name})
    chain.resolve_vote(state.game_id, orchestrator_key())
```

### Step 4 (Hour 3-4) — Full loop + betting calls
```python
def run_game(state):
    setup(state)                       # assign roles, commit hashes, create_game
    open_markets(state)                # game_winner, seer_survives
    for rnd in range(1, state.max_rounds + 1):
        state.round = rnd
        night(state)                   # wolf + seer LLM calls, commit kill
        morning(state)                 # reveal kill
        open_round_markets(state)      # who_voted_out, catches_wolf
        if check_win(state): break
        state.phase = "discussion"
        freeze_markets(state)          # BETTING FREEZES HERE
        run_discussion(state)
        state.phase = "voting"
        run_voting(state)
        resolve_round_markets(state)   # settle who_voted_out etc.
        if check_win(state): break
    state.phase = "ended"
    settle_game_markets(state)
    reveal_all_roles(state)
```

### Step 5 — Serve state to frontend
```python
# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATE = None  # holds the live GameState

@app.get("/state")
def get_state(mode: str = "bettor"):
    s = serialize(STATE)
    if mode == "bettor":
        for p in s["players"]:
            if not p["revealedRole"]:
                p["role"] = None          # FOG OF WAR enforced here
        s.pop("privateReasoning", None)
    return s

@app.post("/control/start")
def start():
    import threading
    threading.Thread(target=lambda: run_game(new_state())).start()
    return {"ok": True}
```

## Prompts — keep them in `prompts.py`
Pull the exact templates from `agent-werewolf-spec.md` sections 4. Give each agent a personality line (Luna = analytical, Caspian = deflects with humour, etc.) — it's the difference between robotic and watchable.

> **Tuning tip:** wolves should be Caspian + Theron in your test runs. Run discussion 5+ times and read the transcripts. If wolves are too obvious, add "be subtle, never over-defend" to their prompt. If villagers are passive, add "name a specific suspect every turn."

## Acceptance criteria
- [ ] 5 agents assigned roles, hashes committed via `createGame`
- [ ] Night: wolf picks victim, seer investigates, kill committed
- [ ] Discussion: 2 rounds, every alive agent speaks with full context
- [ ] Voting: each agent's vote submitted from its own wallet, `resolveVote` called
- [ ] `/state?mode=bettor` hides roles; `/state?mode=god` shows everything
- [ ] Markets open/freeze/resolve at the right phases (see INTERFACES section 5)

## If you fall behind
Skip the chain for night kill (eliminate off-chain). Keep votes on-chain. If even votes are flaky, mock the chain calls and keep the discussion engine perfect — a great conversation with a clear winner is the demo; the chain is the credibility layer on top.
