const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const Game = await hre.ethers.getContractFactory("AgentWerewolf");
  const game = await Game.deploy();
  await game.waitForDeployment();
  const gameAddr = await game.getAddress();
  console.log("AgentWerewolf:", gameAddr);

  const Arena = await hre.ethers.getContractFactory("WerewolfArena");
  const arena = await Arena.deploy();
  await arena.waitForDeployment();
  const arenaAddr = await arena.getAddress();
  console.log("WerewolfArena: ", arenaAddr);

  const out = {
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    AgentWerewolf: gameAddr,
    WerewolfArena: arenaAddr,
  };
  const sharedDir = path.join(__dirname, "..", "..", "shared");
  fs.mkdirSync(sharedDir, { recursive: true });
  fs.writeFileSync(path.join(sharedDir, "deployed.json"), JSON.stringify(out, null, 2));

  console.log("\nWrote shared/deployed.json. Put these in the root .env:");
  console.log(`  GAME_CONTRACT=${gameAddr}`);
  console.log(`  BETTING_CONTRACT=${arenaAddr}`);
  console.log("And in frontend/.env:");
  console.log(`  VITE_CONTRACT_ADDRESS=${arenaAddr}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
