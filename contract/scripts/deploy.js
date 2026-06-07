const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const Game = await hre.ethers.getContractFactory("AgentWerewolf");
  const game = await Game.deploy();
  await game.waitForDeployment();
  const gameAddr = await game.getAddress();
  console.log("AgentWerewolf: ", gameAddr);

  const Betting = await hre.ethers.getContractFactory("WerewolfBetting");
  const betting = await Betting.deploy();
  await betting.waitForDeployment();
  const bettingAddr = await betting.getAddress();
  console.log("WerewolfBetting:", bettingAddr);

  // Persist addresses so the orchestrator can pick them up.
  const out = {
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    AgentWerewolf: gameAddr,
    WerewolfBetting: bettingAddr,
  };
  const sharedDir = path.join(__dirname, "..", "..", "shared");
  fs.mkdirSync(sharedDir, { recursive: true });
  fs.writeFileSync(
    path.join(sharedDir, "deployed.json"),
    JSON.stringify(out, null, 2)
  );
  console.log("\nWrote shared/deployed.json");
  console.log("Put these in orchestrator/.env:");
  console.log(`  GAME_CONTRACT=${gameAddr}`);
  console.log(`  BETTING_CONTRACT=${bettingAddr}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
