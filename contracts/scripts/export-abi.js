// Copies compiled ABIs into shared/abi/ so the orchestrator (B) and frontend (C)
// can import them. Run after `npx hardhat compile`.
const fs = require("fs");
const path = require("path");

const NAMES = ["AgentWerewolf", "WerewolfBetting"];
const artifactsDir = path.join(__dirname, "..", "artifacts", "contracts");
const outDir = path.join(__dirname, "..", "..", "shared", "abi");

fs.mkdirSync(outDir, { recursive: true });

for (const name of NAMES) {
  const src = path.join(artifactsDir, `${name}.sol`, `${name}.json`);
  if (!fs.existsSync(src)) {
    console.error(`Missing artifact for ${name} — run \`npx hardhat compile\` first.`);
    process.exit(1);
  }
  const artifact = JSON.parse(fs.readFileSync(src, "utf8"));
  // Write the full artifact (frontend/orchestrator read .abi off it).
  fs.writeFileSync(
    path.join(outDir, `${name}.json`),
    JSON.stringify({ contractName: name, abi: artifact.abi }, null, 2)
  );
  console.log(`Exported ${name} ABI -> shared/abi/${name}.json`);
}
