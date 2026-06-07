const { expect } = require("chai");
const { ethers } = require("hardhat");

// Role enum: Unknown=0, Wolf=1, Villager=2, Seer=3
function roleHash(role, idx, salt) {
  return ethers.solidityPackedKeccak256(["uint8", "uint8", "bytes32"], [role, idx, salt]);
}

describe("AgentWerewolf", function () {
  it("runs a vote round and pays the winning team", async function () {
    const signers = await ethers.getSigners();
    const players = signers.slice(0, 4);
    const addrs = players.map((p) => p.address);
    const salt = ethers.id("salt");
    // 0=Wolf, 1,2,3 = Villagers
    const roles = [1, 2, 2, 2];
    const hashes = roles.map((r, i) => roleHash(r, i, salt));

    const Game = await ethers.getContractFactory("AgentWerewolf");
    const game = await Game.deploy();
    await game.waitForDeployment();

    await game.createGame(addrs, hashes, { value: ethers.parseEther("1") });
    const gameId = 0;

    // Reveal the wolf's night kill is skipped; jump to Day via revealNightKill.
    const victimIdx = 3;
    const killHash = ethers.solidityPackedKeccak256(["uint8", "bytes32"], [victimIdx, salt]);
    await game.commitNightKill(gameId, killHash);
    await game.revealNightKill(gameId, victimIdx, salt);

    // Day: players 1,2 vote out the wolf (idx 0); player 0 votes idx 1.
    await game.connect(players[1]).submitVote(gameId, 0);
    await game.connect(players[2]).submitVote(gameId, 0);
    await game.connect(players[0]).submitVote(gameId, 1);

    const tally = await game.getTally(gameId);
    expect(tally[0]).to.equal(2n);

    // Reveal the eliminated wolf's role so wasWolf is true.
    await game.revealRole(gameId, 0, 1, salt);
    await expect(game.resolveVote(gameId))
      .to.emit(game, "PlayerEliminated")
      .withArgs(gameId, 0, true);

    // Village wins; reveal a villager and let them claim the pot.
    await game.declareWinner(gameId, 2); // Team.Village
    await game.revealRole(gameId, 1, 2, salt);
    const before = await ethers.provider.getBalance(players[1].address);
    const tx = await game.connect(players[1]).claimPrize(gameId);
    const rc = await tx.wait();
    const after = await ethers.provider.getBalance(players[1].address);
    const gas = rc.gasUsed * rc.gasPrice;
    expect(after + gas - before).to.equal(ethers.parseEther("1"));
  });
});

describe("WerewolfBetting", function () {
  it("splits the pool parimutuel-style", async function () {
    const [, a, b, c] = await ethers.getSigners();
    const Betting = await ethers.getContractFactory("WerewolfBetting");
    const betting = await Betting.deploy();
    await betting.waitForDeployment();

    await betting.openMarket(0, 1, 2); // marketId 0, 2 options
    const marketId = 0;

    // a + b back option 0 (0.3 total), c backs option 1 (0.7).
    await betting.connect(a).placeBet(marketId, 0, { value: ethers.parseEther("0.1") });
    await betting.connect(b).placeBet(marketId, 0, { value: ethers.parseEther("0.2") });
    await betting.connect(c).placeBet(marketId, 1, { value: ethers.parseEther("0.7") });

    const pools = await betting.getPools(marketId);
    expect(pools[0]).to.equal(ethers.parseEther("0.3"));
    expect(pools[1]).to.equal(ethers.parseEther("0.7"));

    await betting.freezeMarket(marketId);
    await betting.resolveMarket(marketId, 0); // option 0 wins, total pool = 1.0

    // a staked 0.1 of 0.3 winning pool -> gets 1/3 of 1.0 = 0.3333...
    const before = await ethers.provider.getBalance(a.address);
    const tx = await betting.connect(a).claimWinnings(marketId);
    const rc = await tx.wait();
    const after = await ethers.provider.getBalance(a.address);
    const gas = rc.gasUsed * rc.gasPrice;
    const net = after + gas - before;
    const expected = (ethers.parseEther("1.0") * ethers.parseEther("0.1")) / ethers.parseEther("0.3");
    expect(net).to.equal(expected);
  });
});
