require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const PRIVATE_KEY = process.env.PRIVATE_KEY;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    // Generic Monad network — drives off RPC_URL + CHAIN_ID in .env.
    // Works for the contract.dev stagenet (143) or any custom endpoint.
    monad: {
      url: process.env.RPC_URL || "https://testnet-rpc.monad.xyz",
      chainId: Number(process.env.CHAIN_ID || 143),
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
    // Public Monad testnet (chainId 10143) — for a judge-reachable, explorer-verifiable deploy.
    monadTestnet: {
      url: "https://testnet-rpc.monad.xyz",
      chainId: 10143,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};
