const { expect } = require("chai");
const { ethers } = require("hardhat");

// Role enum (off-chain): wolf=1, villager=2, seer=3
function roleHash(role, idx, salt) {
  return ethers.solidityPackedKeccak256(["uint8", "uint8", "bytes32"], [role, idx, salt]);
}

describe("AgentWerewolf (operator-driven record)", function () {
  it("commits roles, records kills/votes, reveals, declares winner; gates on operator", async function () {
    const [op, other] = await ethers.getSigners();
    const Game = await ethers.getContractFactory("AgentWerewolf");
    const game = await Game.deploy();
    await game.waitForDeployment();

    const salt = ethers.id("salt");
    const roles = [1, 1, 3, 2, 2, 2, 2]; // 2 wolves, 1 seer, 4 villagers
    const hashes = roles.map((r, i) => roleHash(r, i, salt));

    await expect(game.createGame(hashes)).to.emit(game, "GameCreated").withArgs(0, 7);
    expect(await game.gameCount()).to.equal(1n);

    await expect(game.recordKill(0, 2)).to.emit(game, "PlayerKilled").withArgs(0, 2);
    expect((await game.getAlive(0))[2]).to.equal(false);

    await expect(game.recordVote(0, 1, 0)).to.emit(game, "VoteRecorded").withArgs(0, 1, 0);

    // Reveal the seer (idx 2, role 3) — must match the commitment.
    await expect(game.revealRole(0, 2, 3, salt)).to.emit(game, "RoleRevealed").withArgs(0, 2, 3);
    expect((await game.getRevealed(0))[2]).to.equal(3);
    await expect(game.revealRole(0, 2, 1, salt)).to.be.revertedWith("bad reveal");

    await game.declareWinner(0, 2); // village
    expect(await game.getWinner(0)).to.equal(2);

    // operator gate
    await expect(game.connect(other).recordKill(0, 1)).to.be.revertedWith("not operator");
    await expect(game.connect(other).createGame(hashes)).to.be.revertedWith("not operator");
  });
});

describe("WerewolfArena (parimutuel betting)", function () {
  it("splits the pool proportionally and gates operator actions", async function () {
    const [op, a, b, c] = await ethers.getSigners();
    const Arena = await ethers.getContractFactory("WerewolfArena");
    const arena = await Arena.deploy();
    await arena.waitForDeployment();

    await arena.openMarket(0, 2); // marketId 0, 2 options
    await arena.connect(a).placeBet(0, 0, { value: ethers.parseEther("0.1") });
    await arena.connect(b).placeBet(0, 0, { value: ethers.parseEther("0.2") });
    await arena.connect(c).placeBet(0, 1, { value: ethers.parseEther("0.7") });

    const pools = await arena.getPools(0);
    expect(pools[0]).to.equal(ethers.parseEther("0.3"));
    expect(pools[1]).to.equal(ethers.parseEther("0.7"));

    await arena.freezeMarket(0);
    await expect(
      arena.connect(a).placeBet(0, 0, { value: ethers.parseEther("0.1") })
    ).to.be.revertedWith("closed");

    await arena.resolveMarket(0, 0); // option 0 wins; total pool 1.0

    // a staked 0.1 of the 0.3 winning pool -> 1/3 of 1.0
    const before = await ethers.provider.getBalance(a.address);
    const tx = await arena.connect(a).claimWinnings(0);
    const rc = await tx.wait();
    const after = await ethers.provider.getBalance(a.address);
    const net = after + rc.gasUsed * rc.gasPrice - before;
    const expected =
      (ethers.parseEther("1.0") * ethers.parseEther("0.1")) / ethers.parseEther("0.3");
    expect(net).to.equal(expected);

    // double-claim blocked + operator gate
    await expect(arena.connect(a).claimWinnings(0)).to.be.revertedWith("already claimed");
    await expect(arena.connect(a).openMarket(0, 2)).to.be.revertedWith("not operator");
  });
});
