# Workstream A — Smart Contracts

> You own both contracts and the Monad deploy. Keep them minimal — the demo value is agents talking and money moving, not contract cleverness. Lean on a mentor for Solidity gotchas.

## Your files
- `contracts/contracts/AgentWerewolf.sol`
- `contracts/contracts/WerewolfBetting.sol`
- `contracts/scripts/deploy.js`
- export ABIs to `shared/abi/` after compile

## Build order

### Step 1 (Hour 1) — Skeleton + deploy pipeline
Write empty function signatures matching `INTERFACES.md` section 3. Get `deploy.js` working against Monad testnet with a trivial version. **Goal: a deployed address by end of Hour 1**, even if functions are stubs. This unblocks B from writing chain calls.

```javascript
// scripts/deploy.js
const hre = require("hardhat");
async function main() {
  const Game = await hre.ethers.getContractFactory("AgentWerewolf");
  const game = await Game.deploy();
  await game.waitForDeployment();
  console.log("AgentWerewolf:", await game.getAddress());

  const Betting = await hre.ethers.getContractFactory("WerewolfBetting");
  const betting = await Betting.deploy();
  await betting.waitForDeployment();
  console.log("WerewolfBetting:", await betting.getAddress());
}
main().catch((e) => { console.error(e); process.exit(1); });
```
Deploy: `npx hardhat run scripts/deploy.js --network monadTestnet`

### Step 2 (Hour 2) — AgentWerewolf core
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AgentWerewolf {
    enum Phase { Night, Day, Ended }
    enum Team  { None, Wolf, Village }

    struct Game {
        address[]  players;
        bytes32[]  roleHashes;
        bool[]     alive;
        uint256    pot;
        Phase      phase;
        uint8      round;
        bytes32    nightKillHash;
        bool       killRevealed;
        Team       winner;
        bool       prizeClaimed;
    }

    mapping(uint256 => Game) public games;
    mapping(uint256 => mapping(address => uint8)) public voteOf;   // voter => targetIdx+1 (0 = not voted)
    mapping(uint256 => uint256[]) public tally;                    // votes per player idx
    uint256 public gameCount;

    event GameCreated(uint256 gameId, uint256 pot);
    event NightKillCommitted(uint256 gameId);
    event PlayerEliminated(uint256 gameId, uint8 playerIdx, bool wasWolf);
    event VoteCast(uint256 gameId, address voter, uint8 targetIdx);
    event Winner(uint256 gameId, uint8 team);

    function createGame(address[] calldata players, bytes32[] calldata roleHashes)
        external payable returns (uint256 gameId)
    {
        require(players.length == roleHashes.length, "len mismatch");
        gameId = gameCount++;
        Game storage g = games[gameId];
        g.players = players;
        g.roleHashes = roleHashes;
        g.pot = msg.value;
        g.phase = Phase.Night;
        g.round = 1;
        for (uint i = 0; i < players.length; i++) g.alive.push(true);
        tally[gameId] = new uint256[](players.length);
        emit GameCreated(gameId, msg.value);
    }

    function commitNightKill(uint256 gameId, bytes32 killHash) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Night, "not night");
        g.nightKillHash = killHash;
        g.killRevealed = false;
        emit NightKillCommitted(gameId);
    }

    function revealNightKill(uint256 gameId, uint8 victimIdx, bytes32 salt) external {
        Game storage g = games[gameId];
        require(keccak256(abi.encodePacked(victimIdx, salt)) == g.nightKillHash, "bad reveal");
        require(g.alive[victimIdx], "already dead");
        g.alive[victimIdx] = false;
        g.killRevealed = true;
        g.phase = Phase.Day;
        emit PlayerEliminated(gameId, victimIdx, false); // role-agnostic at night
    }

    function submitVote(uint256 gameId, uint8 targetIdx) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Day, "not day");
        require(_isPlayer(g, msg.sender), "not a player");
        require(voteOf[gameId][msg.sender] == 0, "already voted");
        voteOf[gameId][msg.sender] = targetIdx + 1;
        tally[gameId][targetIdx]++;
        emit VoteCast(gameId, msg.sender, targetIdx);
    }

    function resolveVote(uint256 gameId) external {
        Game storage g = games[gameId];
        // find max-voted alive player
        uint8 out; uint256 best;
        for (uint8 i = 0; i < g.players.length; i++) {
            if (g.alive[i] && tally[gameId][i] > best) { best = tally[gameId][i]; out = i; }
        }
        g.alive[out] = false;
        bool wasWolf = _verifyWolf(g, out);   // see note below
        emit PlayerEliminated(gameId, out, wasWolf);
        _checkWin(gameId);
        // reset tally for next round
        for (uint8 i = 0; i < g.players.length; i++) tally[gameId][i] = 0;
        if (g.phase != Phase.Ended) { g.round++; g.phase = Phase.Night; }
    }

    function claimPrize(uint256 gameId) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Ended, "not over");
        require(!g.prizeClaimed, "claimed");
        require(_onWinningTeam(g, msg.sender), "not winner");
        g.prizeClaimed = true;
        payable(msg.sender).transfer(g.pot);
    }

    function forceEnd(uint256 gameId) external {
        games[gameId].phase = Phase.Ended;
    }

    // ---- helpers (implement) ----
    function _isPlayer(Game storage g, address a) internal view returns (bool) { /* loop players */ }
    function _verifyWolf(Game storage g, uint8 idx) internal view returns (bool) { /* off-chain reveal feeds this */ }
    function _onWinningTeam(Game storage g, address a) internal view returns (bool) { /* ... */ }
    function _checkWin(uint256 gameId) internal { /* count alive wolves vs villagers, set winner + Ended */ }
}
```

> **Role verification shortcut for the demo:** doing full on-chain role verification (matching every roleHash with salt) is fiddly. For the hackathon, the orchestrator can pass the eliminated player's role + salt into `resolveVote` / a `revealRole(gameId, idx, role, salt)` call, and the contract verifies `keccak256(role, idx, salt) == roleHashes[idx]`. That keeps it provably-fair without complex state. Discuss with a mentor — don't burn an hour here.

### Step 3 (Hour 2-3) — WerewolfBetting (parimutuel)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract WerewolfBetting {
    struct Market {
        uint256 gameId;
        uint8   marketType;
        uint8   numOptions;
        uint256[] pools;          // staked per option
        uint256 totalPool;
        bool    frozen;
        bool    resolved;
        uint8   winningOption;
    }

    mapping(uint256 => Market) public markets;
    mapping(uint256 => mapping(address => mapping(uint8 => uint256))) public stakeOf; // market => bettor => option => amount
    mapping(uint256 => mapping(address => bool)) public claimed;
    uint256 public marketCount;

    event MarketOpened(uint256 marketId, uint256 gameId, uint8 marketType);
    event BetPlaced(uint256 marketId, address bettor, uint8 optionIdx, uint256 amount);
    event MarketResolved(uint256 marketId, uint8 winningOption);

    function openMarket(uint256 gameId, uint8 marketType, uint8 numOptions)
        external returns (uint256 marketId)
    {
        marketId = marketCount++;
        Market storage m = markets[marketId];
        m.gameId = gameId;
        m.marketType = marketType;
        m.numOptions = numOptions;
        m.pools = new uint256[](numOptions);
        emit MarketOpened(marketId, gameId, marketType);
    }

    function placeBet(uint256 marketId, uint8 optionIdx) external payable {
        Market storage m = markets[marketId];
        require(!m.frozen && !m.resolved, "closed");
        require(optionIdx < m.numOptions, "bad option");
        require(msg.value > 0, "no stake");
        m.pools[optionIdx] += msg.value;
        m.totalPool += msg.value;
        stakeOf[marketId][msg.sender][optionIdx] += msg.value;
        emit BetPlaced(marketId, msg.sender, optionIdx, msg.value);
    }

    function freezeMarket(uint256 marketId) external { markets[marketId].frozen = true; }

    function resolveMarket(uint256 marketId, uint8 winningOption) external {
        Market storage m = markets[marketId];
        m.resolved = true;
        m.winningOption = winningOption;
        emit MarketResolved(marketId, winningOption);
    }

    // Parimutuel payout: winners split the whole pool proportionally
    function claimWinnings(uint256 marketId) external {
        Market storage m = markets[marketId];
        require(m.resolved, "unresolved");
        require(!claimed[marketId][msg.sender], "claimed");
        uint256 myStake = stakeOf[marketId][msg.sender][m.winningOption];
        require(myStake > 0, "no winning stake");
        uint256 winPool = m.pools[m.winningOption];
        uint256 payout = (m.totalPool * myStake) / winPool;
        claimed[marketId][msg.sender] = true;
        payable(msg.sender).transfer(payout);
    }

    function getPools(uint256 marketId) external view returns (uint256[] memory) {
        return markets[marketId].pools;
    }
}
```

### Step 4 — After compile, export ABIs
```bash
npx hardhat compile
cp artifacts/contracts/AgentWerewolf.sol/AgentWerewolf.json ../shared/abi/
cp artifacts/contracts/WerewolfBetting.sol/WerewolfBetting.json ../shared/abi/
```
Tell B the two deployed addresses → they go in `orchestrator/.env`.

## Acceptance criteria
- [ ] Both contracts deployed to Monad testnet, addresses shared
- [ ] `createGame` locks a pot, emits event
- [ ] `submitVote` from 4 different wallets tallies correctly
- [ ] `resolveVote` eliminates the right player, emits `PlayerEliminated`, sets `Winner` when conditions met
- [ ] `placeBet` updates pools; `claimWinnings` pays parimutuel share
- [ ] ABIs in `shared/abi/`

## If you fall behind
Cut commit/reveal night kill — let the orchestrator just call a simple `eliminate(gameId, idx)`. Keep `submitVote` + `resolveVote` + `claimPrize` + the whole betting contract. Those are the demo.
