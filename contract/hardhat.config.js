require("@nomicfoundation/hardhat-toolbox");
const path = require("path");
// Single source of truth: the monorepo root .env.
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

// Only accept a real 32-byte private key (0x + 64 hex). An address (0x + 40)
// or empty value is ignored, so compile/test never break before a key is set.
const RAW_KEY = process.env.PRIVATE_KEY || "";
const PRIVATE_KEY = /^0x[0-9a-fA-F]{64}$/.test(RAW_KEY) ? RAW_KEY : undefined;

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
