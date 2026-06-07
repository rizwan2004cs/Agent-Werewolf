// Exports compiled ABIs into shared/abi/ (source of truth) and copies them where
// the backend + frontend import them. Run after `npx hardhat compile`.
const fs = require("fs");
const path = require("path");

const NAMES = ["AgentWerewolf", "WerewolfArena"];
const artifactsDir = path.join(__dirname, "..", "artifacts", "contracts");
const sharedDir = path.join(__dirname, "..", "..", "shared", "abi");
const frontendAbi = path.join(__dirname, "..", "..", "frontend", "src", "abi.json");

fs.mkdirSync(sharedDir, { recursive: true });

const abis = {};
for (const name of NAMES) {
  const src = path.join(artifactsDir, `${name}.sol`, `${name}.json`);
  if (!fs.existsSync(src)) {
    console.error(`Missing artifact for ${name} — run \`npx hardhat compile\` first.`);
    process.exit(1);
  }
  const artifact = JSON.parse(fs.readFileSync(src, "utf8"));
  abis[name] = artifact.abi;
  fs.writeFileSync(
    path.join(sharedDir, `${name}.json`),
    JSON.stringify({ contractName: name, abi: artifact.abi }, null, 2)
  );
  console.log(`Exported ${name} ABI -> shared/abi/${name}.json`);
}

// The frontend only touches the betting contract (placeBet/claim).
fs.writeFileSync(frontendAbi, JSON.stringify(abis.WerewolfArena, null, 2));
console.log("Copied WerewolfArena ABI -> frontend/src/abi.json");
