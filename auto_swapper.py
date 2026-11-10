import asyncio
import os
import time
from dotenv import load_dotenv
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# ==============================================================================
# PROJECT:     DeFi Revenue Auto-Swapper (Uniswap V3)
# DEVELOPER:   btctrl-labs (https://github.com)
# INTEGRATION: Stage 1 (Balances), Stage 2 (Quote) & Stage 3 (LIVE SWAP) - POLYGON
# ==============================================================================

# Load environment variables safely from the local .env file
load_dotenv()

RPC_URL = os.getenv("RPC_URL")
BOT_WALLET = os.getenv("BOT_WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Standard ERC-20 ABI minimal structure needed to read token balances
MINIMAL_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Minimal ABI for Uniswap V3 Quoter to fetch exact swap outputs
QUOTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
        ],
        "name": "quoteExactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Minimal ABI for Uniswap V3 SwapRouter (Exact Input Single)
ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Official Contract Addresses on Polygon PoS Mainnet
USDC_CONTRACT_ADDRESS     = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WMATIC_CONTRACT_ADDRESS   = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
UNISWAP_V3_QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
UNISWAP_V3_ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"

# LIVE SWAP PARAMETER: Amount of native POL (MATIC) you want to exchange
AMOUNT_TO_SWAP_POL = 5.0
SLIPPAGE_TOLERANCE_PERCENT = 1.0  # 1% Protection

async def main_pipeline():
    print("=" * 70)
    print("🚀 SYSTEM: DeFi Revenue Auto-Swapper [POLYGON FULL PIPELINE]")
    print("👨‍💻 ENGINE: Developed by btctrl-labs")
    print("=" * 70)
    
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    
    if await w3.is_connected():
        print("✅ Successfully connected to Polygon PoS blockchain!")
    else:
        print("❌ Network connection failed.")
        return

    if not BOT_WALLET or not PRIVATE_KEY:
        print("❌ Error: Credentials missing in .env file.")
        return

    # --------------------------------------------------------------------------
    # STAGE 1: Balance Check
    # --------------------------------------------------------------------------
    print("-" * 70)
    print("🔍 [STAGE 1] Fetching Live Asset Balances...")
    native_balance_wei = await w3.eth.get_balance(BOT_WALLET)
    native_balance = w3.from_wei(native_balance_wei, "ether")
    print(f"   🔹 Native Balance:  {native_balance:.6f} POL (MATIC)")

    usdc_contract = w3.eth.contract(address=USDC_CONTRACT_ADDRESS, abi=MINIMAL_ERC20_ABI)
    usdc_balance_raw = await usdc_contract.functions.balanceOf(BOT_WALLET).call()
    usdc_balance = usdc_balance_raw / (10 ** 6)
    print(f"   🔹 Token Balance:   {usdc_balance:.2f} USDC")

    if native_balance < AMOUNT_TO_SWAP_POL:
        print(f"❌ Aborting: Insufficient POL balance to swap {AMOUNT_TO_SWAP_POL} POL.")
        return

    # --------------------------------------------------------------------------
    # STAGE 2: Price Quoting (Dry Run)
    # --------------------------------------------------------------------------
    print("-" * 70)
    print(f"🔍 [STAGE 2] Fetching Live Uniswap V3 Quote...")
    amount_in_wei = w3.to_wei(AMOUNT_TO_SWAP_POL, "ether")
    quoter_contract = w3.eth.contract(address=UNISWAP_V3_QUOTER_ADDRESS, abi=QUOTER_ABI)
    
    raw_usdc_output = await quoter_contract.functions.quoteExactInputSingle(
        WMATIC_CONTRACT_ADDRESS, USDC_CONTRACT_ADDRESS, 500, amount_in_wei, 0
    ).call()
    
    expected_usdc = raw_usdc_output / (10 ** 6)
    print(f"   🔹 Market Output:   {expected_usdc:.4f} USDC for {AMOUNT_TO_SWAP_POL} POL")

    # Calculate Slippage boundaries (Minimum acceptable USDC amount)
    min_usdc_acceptable = expected_usdc * (1 - (SLIPPAGE_TOLERANCE_PERCENT / 100))
    min_usdc_raw = int(min_usdc_acceptable * (10 ** 6))
    print(f"   🔹 Slippage Floor:  {min_usdc_acceptable:.4f} USDC (Min. Guaranteed)")

    # --------------------------------------------------------------------------
    # STAGE 3: LIVE TRANSACTION EXECUTION
    # --------------------------------------------------------------------------
    print("-" * 70)
    print("🔥 [STAGE 3] Initiating LIVE Transaction on Uniswap V3...")
    
    # 20 minutes expiration window for the transaction pool
    deadline = int(time.time()) + 1200 
    
    router_contract = w3.eth.contract(address=UNISWAP_V3_ROUTER_ADDRESS, abi=ROUTER_ABI)
    
    # Structuring the payload parameters required by the Uniswap core contracts [1.5]
    swap_params = {
        "tokenIn": WMATIC_CONTRACT_ADDRESS,
        "tokenOut": USDC_CONTRACT_ADDRESS,
        "fee": 500,  # 0.05% Pool Tier
        "recipient": BOT_WALLET,
        "deadline": deadline,
        "amountIn": amount_in_wei,
        "amountOutMinimum": min_usdc_raw,
        "sqrtPriceLimitX96": 0
    }

    try:
        # Build transaction object dynamically pulling current chain parameters
        nonce = await w3.eth.get_transaction_count(BOT_WALLET)
        gas_estimate = await router_contract.functions.exactInputSingle(swap_params).estimate_gas({
            "from": BOT_WALLET,
            "value": amount_in_wei
        })
        
        # Pull competitive base fee stats to prevent sticking
        gas_price = await w3.eth.gas_price
        
        tx_build = await router_contract.functions.exactInputSingle(swap_params).build_transaction({
            "from": BOT_WALLET,
            "value": amount_in_wei,  # Senden von nativem POL via msg.value [1.5]
            "gas": int(gas_estimate * 1.2),  # 20% Buffer for state change variations
            "gasPrice": int(gas_price * 1.2), # 20% Premium for faster block insertion
            "nonce": nonce,
            "chainId": 137  # Polygon PoS Mainnet Chain ID
        })
        
        print("✍ Signing transaction with securely loaded Private Key...")
        signed_tx = w3.eth.account.sign_transaction(tx_build, private_key=PRIVATE_KEY)
        
        print("📡 Broadcasting signed raw payload to the network nodes...")
        tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"🎫 Transaction sent successfully! Hash: {tx_hash.hex()}")
        print("⏳ Waiting for block confirmation (this may take up to 30 seconds)...")
        
        # Block-level validation loop
        receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print("=" * 70)
            print("💸 [SUCCESS] Swap transaction successfully executed and mined!")
            print(f"📊 Block Number: #{receipt.blockNumber}")
            print(f"⛽ Gas Used:     {receipt.gasUsed}")
            print("=" * 70)
        else:
            print("❌ Transaction execution failed on-chain (Reverted).")

    except Exception as tx_error:
        print(f"❌ Execution Failure: {tx_error}")

if __name__ == "__main__":
    try:
        asyncio.run(main_pipeline())
    except KeyboardInterrupt:
        print("\n🛑 Execution aborted by user.")
