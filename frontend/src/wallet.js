// MetaMask + ethers v6 — the only chain writes from the frontend (placeBet/claim).
import { BrowserProvider, Contract, parseEther, formatEther } from "ethers";
import abi from "./abi.json";

const ADDR = import.meta.env.VITE_CONTRACT_ADDRESS;
const CHAIN_ID = Number(import.meta.env.VITE_CHAIN_ID || 143);
const RPC_URL = import.meta.env.VITE_RPC_URL;
const HEX_CHAIN = "0x" + CHAIN_ID.toString(16);

function eth() {
  if (!window.ethereum) throw new Error("MetaMask not found — install the extension");
  return window.ethereum;
}

// Turn raw MetaMask errors into something a human can act on.
function friendly(err) {
  const m = (err && (err.message || String(err))) || "";
  if (/context invalidated|Extension context/i.test(m))
    return new Error("MetaMask was reloaded — refresh this page (F5), then try again.");
  if (err && err.code === 4001) return new Error("Request rejected in MetaMask.");
  if (/insufficient funds/i.test(m)) return new Error("Not enough MON on this account (chain 143). Fund it first.");
  if (/missing revert data|CALL_EXCEPTION|cannot estimate gas|execution reverted/i.test(m))
    return new Error("Bet rejected by the contract — the betting window has most likely locked for this phase. Try again when betting reopens.");
  return err instanceof Error ? err : new Error(m);
}

// Switch MetaMask to the contract.dev Monad network, adding it if it's missing.
export async function ensureChain() {
  const e = eth();
  try {
    await e.request({ method: "wallet_switchEthereumChain", params: [{ chainId: HEX_CHAIN }] });
  } catch (err) {
    if (err.code === 4902 || /Unrecognized|not been added/i.test(err.message || "")) {
      await e.request({
        method: "wallet_addEthereumChain",
        params: [{
          chainId: HEX_CHAIN,
          chainName: "Monad (contract.dev)",
          nativeCurrency: { name: "MON", symbol: "MON", decimals: 18 },
          rpcUrls: [RPC_URL],
        }],
      });
    } else {
      throw err;
    }
  }
}

export async function connect() {
  try {
    const e = eth();
    const accounts = await e.request({ method: "eth_requestAccounts" });
    // Best effort only: MetaMask often refuses to add private RPCs (contract.dev)
    // it can't probe. Sponsored bets only need the ADDRESS, so never let the
    // chain add/switch block connecting — just log it.
    try {
      await ensureChain();
    } catch (err) {
      console.warn("[wallet] chain add/switch skipped:", err?.message || err);
    }
    return accounts[0];
  } catch (err) {
    throw friendly(err);
  }
}

export function currentAccount() {
  return (window.ethereum && window.ethereum.selectedAddress) || null;
}

async function getContract() {
  if (!ADDR) throw new Error("Betting contract address not set (VITE_CONTRACT_ADDRESS)");
  await ensureChain();
  const provider = new BrowserProvider(eth());
  const signer = await provider.getSigner();
  return new Contract(ADDR, abi, signer);
}

export async function placeBet(marketId, optionIdx, amountMon = "0.05") {
  try {
    const c = await getContract();
    // Check balance up front so "no funds" and "window locked" give different errors.
    const provider = c.runner.provider;
    const me = await c.runner.getAddress();
    const bal = await provider.getBalance(me);
    if (bal < parseEther(String(amountMon)))
      throw new Error(`Not enough MON: balance is ${(Number(bal) / 1e18).toFixed(4)} MON on chain ${CHAIN_ID}. Fund this account from the operator wallet (public faucets can't reach this private stagenet).`);
    const tx = await c.placeBet(marketId, optionIdx, { value: parseEther(String(amountMon)) });
    await tx.wait();
    return tx.hash;
  } catch (err) {
    throw friendly(err);
  }
}

// Preflight: what the connected account can claim on a resolved market.
// Mirrors the contract math: payout = totalPool * myStake / winningPool.
// Returns { payout: "1.2345" (MON string), done: bool } — payout "0" if nothing.
export async function previewClaim(marketId) {
  const c = await getContract();
  const me = await c.runner.getAddress();
  const [, , totalPool, , resolved, winningOption] = await c.getMarket(marketId);
  if (!resolved) return { payout: "0", done: false };
  const done = await c.claimed(marketId, me);
  if (done) return { payout: "0", done: true };
  const myStake = await c.stakeOf(marketId, me, winningOption);
  if (myStake === 0n) return { payout: "0", done: false };
  const pools = await c.getPools(marketId);
  const winPool = pools[Number(winningOption)];
  const payout = winPool === 0n ? 0n : (totalPool * myStake) / winPool;
  return { payout: formatEther(payout), done: false };
}

export async function claimWinnings(marketId) {
  try {
    const c = await getContract();
    const tx = await c.claimWinnings(marketId);
    await tx.wait();
    return tx.hash;
  } catch (err) {
    const m = (err && (err.message || String(err))) || "";
    if (/nothing to claim/i.test(m)) throw new Error("Nothing to claim — you didn't stake the winning option.");
    if (/already claimed/i.test(m)) throw new Error("Already claimed for this market.");
    if (/unresolved/i.test(m)) throw new Error("Market isn't resolved yet.");
    if (/missing revert data|CALL_EXCEPTION|cannot estimate gas|execution reverted/i.test(m))
      throw new Error("Claim rejected — nothing to claim on this market (or already claimed).");
    throw friendly(err);
  }
}
