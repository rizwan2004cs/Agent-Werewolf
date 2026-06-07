# 04 — Backend (AI Orchestration)

> Python. This is the brain: the game loop, the agents, the prompts, the chain calls, and the FastAPI server. The discussion engine is the most important thing here — agents talking believably is the whole show.

## Dependencies

`backend/requirements.txt`:
```
anthropic
web3
fastapi
uvicorn
python-dotenv
```

`backend/.env` (user provides keys):
```
ANTHROPIC_API_KEY=sk-ant-...
RPC_URL=https://testnet-rpc.monad.xyz
CHAIN_ID=10143
CONTRACT_ADDRESS=0x...        # from Remix deploy
OPERATOR_KEY=0x...            # the deployer wallet key (operator)
```

## 1. State model — `game/state.py`

```python
from dataclasses import dataclass, field
import time

@dataclass
class Player:
    idx: int
    name: str
    role: str                      # "wolf" | "seer" | "villager"
    alive: bool = True
    revealed_role: str | None = None
    current_speech: str | None = None

@dataclass
class Market:
    market_id: int
    type: str                      # "game_winner" | "who_voted_out"
    options: list[str]
    round: int = 1
    pools: dict[str, str] = field(default_factory=dict)
    frozen: bool = False
    resolved: bool = False
    winning_option: str | None = None

@dataclass
class GameState:
    game_id: int = 1
    phase: str = "setup"
    round: int = 1
    max_rounds: int = 2
    pot: str = "1.0"
    speaking_idx: int | None = None
    players: list[Player] = field(default_factory=list)
    night_result: dict | None = None
    discussion_log: list[dict] = field(default_factory=list)
    private_reasoning: list[dict] = field(default_factory=list)
    votes: list[dict] = field(default_factory=list)
    betting_open: bool = True
    markets: list[Market] = field(default_factory=list)
    winner: str | None = None

    def alive_players(self):
        return [p for p in self.players if p.alive]

    def wolves(self):
        return [p for p in self.players if p.role == "wolf"]

    def by_name(self, name):
        return next((p for p in self.players if p.name.lower() == name.lower()), None)
```

## 2. Roster setup

```python
import random

NAMES = ["Luna", "Caspian", "Mira", "Theron", "Dax", "Vera", "Orin"]
# personality flavour — tweak later
PERSONA = {
    "Luna": "measured and analytical, cites specific things people said",
    "Caspian": "charming, deflects with light humour, rarely accuses directly",
    "Mira": "blunt and aggressive, makes bold accusations",
    "Theron": "quiet, speaks late, sounds conclusive when he does",
    "Dax": "anxious and suspicious of everyone",
    "Vera": "calm mediator who weighs both sides",
    "Orin": "logical, talks in probabilities",
}

def new_game():
    roles = ["wolf", "wolf", "seer", "villager", "villager", "villager", "villager"]
    random.shuffle(roles)
    players = [Player(idx=i, name=NAMES[i], role=roles[i]) for i in range(7)]
    return GameState(players=players)
```

## 3. Agents + LLM — `game/agents.py`

```python
import os, re, random
from anthropic import Anthropic
from . import prompts

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

def _call(prompt: str, max_tokens: int = 220) -> str:
    resp = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()

def night_wolf_pick(state):
    wolves = state.wolves()
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    text = _call(prompts.wolf_night(wolves[0], targets), max_tokens=120)
    name = _extract(text, [p.name for p in targets])
    return state.by_name(name) or random.choice(targets)

def night_seer_pick(state):
    seer = next((p for p in state.alive_players() if p.role == "seer"), None)
    if not seer: return None, None
    targets = [p for p in state.alive_players() if p.idx != seer.idx]
    text = _call(prompts.seer_night(seer, targets), max_tokens=120)
    name = _extract(text, [p.name for p in targets])
    target = state.by_name(name) or random.choice(targets)
    return seer, target

def speak(player, state, seer_knowledge=None):
    text = _call(prompts.day_speak(player, state, seer_knowledge))
    # optional: a second hidden call for private reasoning (god mode). Keep cheap.
    return text

def vote(player, state, seer_knowledge=None):
    text = _call(prompts.vote(player, state, seer_knowledge), max_tokens=120)
    candidates = [p.name for p in state.alive_players() if p.idx != player.idx]
    name = _extract_vote(text, candidates)
    target = state.by_name(name)
    if not target or target.idx == player.idx:
        target = state.by_name(random.choice(candidates))
    return target, text

def _extract(text, names):
    for n in names:
        if re.search(rf"\b{re.escape(n)}\b", text, re.IGNORECASE):
            return n
    return None

def _extract_vote(text, names):
    m = re.search(r"VOTE:\s*(\w+)", text, re.IGNORECASE)
    if m and any(m.group(1).lower() == n.lower() for n in names):
        return m.group(1)
    return _extract(text, names)
```

## 4. Prompts — `game/prompts.py`

```python
from .state import PERSONA  # or import from setup module

def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead

def _log(state, n=20):
    return "\n".join(f"{e['speaker']}: {e['text']}" for e in state.discussion_log[-n:]) or "(no discussion yet)"

def wolf_night(wolf, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {wolf.name}, a werewolf in a village game.
Living non-wolf players you can eliminate tonight: {names}.
Pick the most dangerous one to kill (the likely seer, or the sharpest reasoner).
Reply with just the name."""

def seer_night(seer, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {seer.name}, the village Seer.
Tonight you may secretly learn one player's true role.
Living players: {names}.
Pick who to investigate. Reply with just the name."""

def day_speak(player, state, seer_knowledge=None):
    alive, dead = _roster(state)
    persona = PERSONA.get(player.name, "")
    base = f"""You are {player.name}, playing Werewolf. You are {persona}.
Living players: {alive}. Dead: {dead}.
Discussion so far:
{_log(state)}

Speak as {player.name} in 2-3 sentences. Stay in character. Do not break the fourth wall."""
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        return base + f"""
SECRET: You are a WEREWOLF. Your partner is {partner}. Never admit it.
Sound like a sincere villager. Cast suspicion on a real villager. Defend your partner only subtly."""
    if player.role == "seer" and seer_knowledge:
        return base + f"""
SECRET: You are the SEER. You learned: {seer_knowledge['name']} is a {seer_knowledge['role']}.
Decide whether to reveal this (powerful but makes you a wolf target) or hint subtly."""
    return base + """
You are an honest villager. Reason from inconsistencies and share a genuine suspicion."""

def vote(player, state, seer_knowledge=None):
    alive, dead = _roster(state)
    candidates = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    role_note = ""
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        role_note = f"(You are secretly a wolf; your partner is {partner}. Vote to eliminate a villager, ideally one others already suspect.)"
    elif player.role == "seer" and seer_knowledge:
        role_note = f"(You are the seer; you know {seer_knowledge['name']} is a {seer_knowledge['role']}.)"
    return f"""You are {player.name}. {role_note}
Living players: {alive}.
Discussion:
{_log(state)}

Vote to eliminate one player from: {candidates}.
Give one sentence of reasoning, then on a new line output exactly:
VOTE:<name>"""
```

## 5. Chain calls — `game/chain.py`

```python
import os, json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
CHAIN_ID = int(os.environ["CHAIN_ID"])
ADDR = Web3.to_checksum_address(os.environ["CONTRACT_ADDRESS"])
KEY = os.environ["OPERATOR_KEY"]
ACCT = w3.eth.account.from_key(KEY)

with open("abi.json") as f:
    ABI = json.load(f)
arena = w3.eth.contract(address=ADDR, abi=ABI)

def _send(fn):
    tx = fn.build_transaction({
        "from": ACCT.address,
        "nonce": w3.eth.get_transaction_count(ACCT.address),
        "chainId": CHAIN_ID,
        "gas": 400000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = ACCT.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(h)

def open_market(game_id, num_options) -> int:
    rcpt = _send(arena.functions.openMarket(game_id, num_options))
    # marketId == marketCount-1 after the tx; read it back:
    return arena.functions.marketCount().call() - 1

def freeze_market(market_id):  return _send(arena.functions.freezeMarket(market_id))
def resolve_market(market_id, winning_idx): return _send(arena.functions.resolveMarket(market_id, winning_idx))

def get_pools(market_id):
    raw = arena.functions.getPools(market_id).call()  # wei per option
    return [str(Web3.from_wei(x, "ether")) for x in raw]
```

> If chain calls are flaky during the demo, wrap each in try/except and continue — the game must keep running even if a tx fails. Log and move on.

## 6. The game loop — `game/loop.py`

```python
import time
from . import agents, chain
from .state import Market

DISCUSSION_SUBROUNDS = 2
STATE: "GameState" = None   # global, served by FastAPI

def run_game(state):
    global STATE; STATE = state
    setup_phase(state)
    for rnd in range(1, state.max_rounds + 1):
        state.round = rnd
        night_phase(state)
        morning_phase(state)
        if check_win(state): break
        discussion_phase(state)
        voting_phase(state)
        if check_win(state): break
    end_phase(state)

def setup_phase(state):
    state.phase = "setup"; state.betting_open = True
    mid = chain.open_market(state.game_id, 2)  # game_winner
    state.markets.append(Market(market_id=mid, type="game_winner",
                                options=["wolves", "village"]))
    _refresh_pools(state)
    time.sleep(2)

def night_phase(state):
    state.phase = "night"; state.speaking_idx = None; time.sleep(2)
    victim = agents.night_wolf_pick(state)
    seer, target = agents.night_seer_pick(state)
    state._seer_knowledge = ({"name": target.name, "role": target.role} if target else None)
    state._pending_kill = victim

def morning_phase(state):
    state.phase = "morning"
    v = state._pending_kill
    v.alive = False; v.revealed_role = v.role
    state.night_result = {"victimName": v.name, "victimIdx": v.idx}
    # open who_voted_out market over living players
    living = [p.name for p in state.alive_players()]
    mid = chain.open_market(state.game_id, len(living))
    state.markets.append(Market(market_id=mid, type="who_voted_out",
                                options=living, round=state.round))
    state.betting_open = True
    _refresh_pools(state)
    time.sleep(2)

def discussion_phase(state):
    state.phase = "discussion"; state.betting_open = False
    for m in state.markets:
        if not m.resolved and not m.frozen:
            try: chain.freeze_market(m.market_id)
            except Exception: pass
            m.frozen = True
    for _ in range(DISCUSSION_SUBROUNDS):
        for p in state.alive_players():
            state.speaking_idx = p.idx
            sk = state._seer_knowledge if p.role == "seer" else None
            line = agents.speak(p, state, sk)
            p.current_speech = line
            state.discussion_log.append({"round": state.round, "speaker": p.name,
                                         "text": line, "ts": int(time.time())})
            if p.role == "wolf":
                state.private_reasoning.append({"speaker": p.name, "role": "wolf",
                                                "thought": "(playing innocent)"})
            time.sleep(1.5)   # pacing beat
            p.current_speech = None
    state.speaking_idx = None

def voting_phase(state):
    state.phase = "voting"; state.votes = []
    counts = {}
    for p in state.alive_players():
        sk = state._seer_knowledge if p.role == "seer" else None
        target, _ = agents.vote(p, state, sk)
        state.votes.append({"voter": p.name, "target": target.name})
        counts[target.idx] = counts.get(target.idx, 0) + 1
        time.sleep(0.5)
    out_idx = max(counts, key=counts.get)
    out = state.players[out_idx]
    out.alive = False; out.revealed_role = out.role
    _resolve_who_voted_out(state, out.name)
    state.phase = "resolution"; time.sleep(1)

def end_phase(state):
    state.phase = "ended"
    state.winner = "village" if len(state.wolves()) == 0 or all(not w.alive for w in state.wolves()) else "wolves"
    for p in state.players: p.revealed_role = p.role
    # resolve game_winner market
    gw = next((m for m in state.markets if m.type == "game_winner"), None)
    if gw:
        win_idx = gw.options.index(state.winner)
        try: chain.resolve_market(gw.market_id, win_idx)
        except Exception: pass
        gw.resolved = True; gw.winning_option = state.winner

def check_win(state):
    alive_wolves = [w for w in state.wolves() if w.alive]
    alive_village = [p for p in state.alive_players() if p.role != "wolf"]
    if len(alive_wolves) == 0: state.winner = "village"; return True
    if len(alive_wolves) >= len(alive_village): state.winner = "wolves"; return True
    return False

def _refresh_pools(state):
    for m in state.markets:
        try:
            pools = chain.get_pools(m.market_id)
            m.pools = {opt: pools[i] for i, opt in enumerate(m.options)}
        except Exception:
            m.pools = {opt: "0" for opt in m.options}

def _resolve_who_voted_out(state, out_name):
    m = next((m for m in state.markets if m.type == "who_voted_out"
              and m.round == state.round and not m.resolved), None)
    if m and out_name in m.options:
        try: chain.resolve_market(m.market_id, m.options.index(out_name))
        except Exception: pass
        m.resolved = True; m.winning_option = out_name
```

## 7. FastAPI server — `server.py`

```python
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from game import loop
from game.state import GameState
from game.setup import new_game   # wherever new_game lives

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"ok": True}

@app.post("/control/start")
def start():
    state = new_game()
    threading.Thread(target=loop.run_game, args=(state,), daemon=True).start()
    return {"ok": True, "gameId": state.game_id}

@app.get("/state")
def get_state(mode: str = "bettor"):
    s = loop.STATE
    if s is None: return {"phase": "idle"}
    return serialize(s, mode)

def serialize(s, mode):
    players = []
    for p in s.players:
        role = p.role if (mode == "god" or p.revealed_role) else None
        players.append({
            "idx": p.idx, "name": p.name, "avatarSeed": p.name,
            "alive": p.alive, "role": role, "revealedRole": p.revealed_role,
            "currentSpeech": p.current_speech,
        })
    out = {
        "gameId": s.game_id, "phase": s.phase, "round": s.round,
        "maxRounds": s.max_rounds, "pot": s.pot, "speakingIdx": s.speaking_idx,
        "players": players, "nightResult": s.night_result,
        "discussionLog": s.discussion_log, "votes": s.votes,
        "bettingOpen": s.betting_open, "winner": s.winner,
        "markets": [vars(m) for m in s.markets],
    }
    if mode == "god":
        out["privateReasoning"] = s.private_reasoning
    return out
```

Run: `uvicorn server:app --reload --port 8000`

## Acceptance criteria
- [ ] `POST /control/start` runs a full game to completion in a background thread
- [ ] A complete game prints sensible discussion to console
- [ ] `/state?mode=bettor` hides unrevealed roles + omits privateReasoning
- [ ] `/state?mode=god` shows everything
- [ ] Markets open at setup + morning, freeze at discussion, resolve at vote + end
- [ ] Chain failures are caught and don't crash the game loop

## Tuning later
Agent quality lives entirely in `prompts.py` and `PERSONA`. To make wolves better liars, add "never over-defend, never be the first to accuse the person who'll be killed tonight." To make villagers sharper, add "always name one concrete suspect with a reason." Run several games and read transcripts.
