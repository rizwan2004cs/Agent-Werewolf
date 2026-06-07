// The only chain *writes* from the frontend: connect, placeBet, claimWinnings.
// ethers v6 + MetaMask, against the contract.dev stagenet. All reads (pools/
// odds) come through the backend /state — never from here.
import { BrowserProvider, Contract, parseEther } from "ethers";
import abi from "./abi.json";

const ADDR = import.meta.env.VITE_CONTRACT_ADDRESS;
const CHAIN_ID = Number(import.meta.env.VITE_CHAIN_ID);
const RPC_URL = import.meta.env.VITE_RPC_URL;
const EXPLORER = import.meta.env.VITE_EXPLORER_URL;
const CHAIN_HEX = "0x" + CHAIN_ID.toString(16);

async function ensureChain() {
  try {
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: CHAIN_HEX }],
    });
  } catch (err) {
    // 4902 = chain unknown to the wallet → add it, then it's selected.
    if (err?.code === 4902 || /Unrecognized chain/i.test(err?.message || "")) {
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [
          {
            chainId: CHAIN_HEX,
            chainName: "contract.dev Stagenet",
            nativeCurrency: { name: "MON", symbol: "MON", decimals: 18 },
            rpcUrls: [RPC_URL],
            blockExplorerUrls: EXPLORER ? [EXPLORER] : [],
          },
        ],
      });
    } else {
      throw err;
    }
  }
}

async function getContract() {
  if (!window.ethereum) throw new Error("Install MetaMask to bet");
  if (!ADDR) throw new Error("Contract address not configured");
  const provider = new BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  await ensureChain();
  const signer = await provider.getSigner();
  return new Contract(ADDR, abi, signer);
}

export async function connectWallet() {
  if (!window.ethereum) throw new Error("Install MetaMask to bet");
  const provider = new BrowserProvider(window.ethereum);
  const accounts = await provider.send("eth_requestAccounts", []);
  await ensureChain();
  return accounts[0];
}

export async function placeBet(marketId, optionIdx, amountMon = "0.05") {
  const c = await getContract();
  const tx = await c.placeBet(marketId, optionIdx, { value: parseEther(amountMon) });
  await tx.wait();
  return tx.hash;
}

export async function claimWinnings(marketId) {
  const c = await getContract();
  const tx = await c.claimWinnings(marketId);
  await tx.wait();
  return tx.hash;
}
