// MetaMask + ethers v6 — the only chain writes from the frontend (placeBet/claim).
import { BrowserProvider, Contract, parseEther } from "ethers";
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
  if (/insufficient funds/i.test(m)) return new Error("Not enough MON on this account (chain 143).");
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
    await ensureChain();
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
    const tx = await c.placeBet(marketId, optionIdx, { value: parseEther(String(amountMon)) });
    await tx.wait();
    return tx.hash;
  } catch (err) {
    throw friendly(err);
  }
}

export async function claimWinnings(marketId) {
  const c = await getContract();
  const tx = await c.claimWinnings(marketId);
  await tx.wait();
  return tx.hash;
}
