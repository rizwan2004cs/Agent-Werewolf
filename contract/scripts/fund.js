// Send MON from the operator wallet (PRIVATE_KEY in root .env) to a bettor
// address — the private contract.dev stagenet has no public faucet, so this
// is how a MetaMask account gets funded.
//
// Usage (from contract/):
//   TO=0x<metamask-address> AMOUNT=5 npx hardhat run scripts/fund.js --network monad
// Windows PowerShell:
//   $env:TO="0x<metamask-address>"; $env:AMOUNT="5"; npx hardhat run scripts/fund.js --network monad
const hre = require("hardhat");

async function main() {
  const to = process.env.TO;
  const amount = process.env.AMOUNT || "5";
  if (!to || !/^0x[0-9a-fA-F]{40}$/.test(to)) {
    throw new Error("Set TO=0x<40-hex address> (the MetaMask account to fund)");
  }
  const [operator] = await hre.ethers.getSigners();
  if (!operator) throw new Error("No operator signer — is PRIVATE_KEY set in the root .env?");

  const balBefore = await hre.ethers.provider.getBalance(operator.address);
  console.log(`operator ${operator.address}: ${hre.ethers.formatEther(balBefore)} MON`);

  const tx = await operator.sendTransaction({ to, value: hre.ethers.parseEther(amount) });
  console.log(`sending ${amount} MON -> ${to} (tx ${tx.hash})…`);
  await tx.wait();

  const balTo = await hre.ethers.provider.getBalance(to);
  console.log(`done. ${to} now has ${hre.ethers.formatEther(balTo)} MON`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
