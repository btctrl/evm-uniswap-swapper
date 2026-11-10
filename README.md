# EVM DeFi Revenue Auto-Swapper (Uniswap V3) 💸

A production-grade, high-performance asynchronous Python automation script that programmatically swaps native EVM assets (POL/MATIC) into USD Stablecoins (USDC) via Uniswap V3 core protocols. 

Built with strict separation of logic and credentials using secure environment routing, automated on-chain gas optimization, and algorithmic slippage protection.

## Architectural Features
- **Production Gas Engineering:** Dynamically fetches current network base fees and injects a 20% premium buffer alongside a 20% gas limit allowance to ensure near-instantaneous block insertion without transaction sticking.
- **Asynchronous Protocol Quoting:** Queries the official Uniswap V3 Quoter contract using read-only simulations (`quoteExactInputSingle`) to fetch sub-second execution rates before deploying capital.
- **Algorithmic Slippage Floor:** Enforces a strict 1.0% slippage threshold passed directly to the SwapRouter payload parameters to protect funds against front-running and sudden pool volatility.
- **Enterprise-Grade Security:** Zero hardcoded keys. Operates natively with `.env` variable loading.

## Technical Stack
- **Engine:** Python 3.10+ | Asynchronous Web3.py (v6)
- **Protocols Interacted:** Uniswap V3 (Quoter & SwapRouter)
- **Environment Management:** `python-dotenv`

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd defi-auto-swapper
   ```

2. **Configure Environment (`.env`):**
   Create a local `.env` file in the root directory (this file is excluded from git):
   ```text
   RPC_URL=https://polygon-rpc.com
   BOT_WALLET_ADDRESS=0x...
   PRIVATE_KEY=your_private_key_here
   ```

3. **Run Pipeline Execution:**
   ```bash
   python auto_swapper.py
   ```

## Production Verification Log
```text
🔄 Connecting to Polygon PoS network... Please wait...
✅ Successfully connected to Polygon PoS blockchain!
📡 Target Wallet Loaded: 0xe22...

🔍 [STAGE 1] Fetching Live Asset Balances...
   🔹 Native Balance:  87.586925 POL (MATIC)
   🔹 Token Balance:   19.15 USDC

🔍 [STAGE 2] Fetching Live Uniswap V3 Quote...
   🔹 Market Output:   0.4374 USDC for 5.0 POL
   🔹 Slippage Floor:  0.4331 USDC (Min. Guaranteed)

🔥 [STAGE 3] Initiating LIVE Transaction on Uniswap V3...
✍ Signing transaction with securely loaded Private Key...
📡 Broadcasting signed raw payload to the network nodes...
🎫 Transaction sent successfully! Hash: 0xb5e...
⏳ Waiting for block confirmation...

💸 [SUCCESS] Swap transaction successfully executed and mined!
📊 Block Number: #97067444
⛽ Gas Used:     174754
```