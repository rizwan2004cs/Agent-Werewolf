// Live MetaMask betting (ethers v6) is wired in M6. Until then this stub keeps
// the betting UI demoable: odds + the discussion freeze are already live; a click
// just explains that on-chain betting connects in M6.
export async function placeBet(/* marketId, optionIdx */) {
  throw new Error("On-chain betting connects in M6 — live odds & the freeze are working now.");
}

export async function claimWinnings(/* marketId */) {
  throw new Error("On-chain betting connects in M6.");
}
