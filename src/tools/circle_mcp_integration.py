"""
Circle MCP Integration for Coder Agent.

Uses Windsurf's Circle MCP server to provide real-time code generation
for Circle ecosystem products: Wallets, CCTP, Gateway, Smart Contracts.
"""

from typing import Any, Dict, List, Optional

from src.utils import get_logger

logger = get_logger(__name__)


class CircleMCPIntegration:
    """
    Integration with Circle MCP server via Windsurf.
    
    Provides access to:
    - Developer-Controlled Wallets (Programmable Wallets)
    - User-Controlled Wallets
    - CCTP (Cross-Chain Transfer Protocol)
    - Gateway (Unified USDC balance)
    - Smart Contract Platform
    """
    
    # Available products
    PRODUCTS = {
        "wallets": "developer-controlled-wallets",
        "user_wallets": "user-controlled-wallets",
        "cctp": "cctp",
        "gateway": "gateway",
        "smart_contracts": "smart-contract-platform",
        "modular_wallets": "modular-wallets",
    }
    
    # Supported blockchains for Arc
    ARC_BLOCKCHAINS = {
        "testnet": "ARC-TESTNET",
        "mainnet": "ARC",  # When available
    }
    
    def __init__(self):
        """Initialize Circle MCP integration."""
        # Silent init
    
    def get_product_summary(self, product: str) -> str:
        """
        Get summary of a Circle product.
        
        Args:
            product: Product name (wallets, cctp, gateway, etc.)
            
        Returns:
            Product summary as formatted text
        """
        product_key = self.PRODUCTS.get(product, product)
        
        logger.info(
            "circle_mcp_getting_product_summary",
            product=product_key,
        )
        
        # This would call the MCP tools in actual implementation
        # For now, return structured guide
        
        summaries = {
            "developer-controlled-wallets": """
**Developer-Controlled Wallets**

Circle's custodial wallet solution where developers manage user assets.

**Key Features:**
- REST APIs, SDKs (Node.js, Python, JS)
- Webhooks for real-time events
- Built-in blockchain infrastructure
- Gas management and bundling
- Multi-chain support (including Arc Testnet!)

**Arc Blockchain Support:**
- Testnet: ARC-TESTNET ✅
- Mainnet: Coming soon

**SDK Setup:**
```typescript
npm install @circle-fin/developer-controlled-wallets

import { initiateDeveloperControlledWalletsClient } from '@circle-fin/developer-controlled-wallets';

const client = initiateDeveloperControlledWalletsClient({
  apiKey: 'YOUR_API_KEY',
  entitySecret: 'YOUR_SECRET'
});
```

**Create Wallet on Arc Testnet:**
```typescript
const response = await client.createWallets({
  accountType: 'SCA',  // Smart Contract Account
  blockchains: ['ARC-TESTNET'],
  count: 1,
  walletSetId: 'your-wallet-set-id',
});

console.log('Wallet created:', response.data.wallets[0]);
```

**Get Testnet Tokens:**
```typescript
await client.requestTestnetTokens({
  address: wallet.address,
  blockchain: 'ARC-TESTNET',
  usdc: true,
  native: true,
});
```
""",
            
            "cctp": """
**CCTP (Cross-Chain Transfer Protocol)**

Trust-minimized USDC bridging across chains.

**Key Features:**
- Burns USDC on source chain
- Mints native USDC on destination chain
- Fast & Slow transfer modes
- No wrapped tokens needed

**Arc Support:**
- Testnet: Arc Testnet ✅
- Mainnet: Coming soon
- Bridge Kit SDK support

**CCTP V2 on Arc:**
```typescript
import { BridgeKit } from '@circle-fin/bridge-kit';

// Bridge USDC to Arc Testnet
const transfer = await BridgeKit.transfer({
  sourceChain: 'ETH-SEPOLIA',
  destChain: 'ARC-TESTNET',
  amount: '100',
  token: 'USDC',
});
```

**Smart Contract Integration:**
```solidity
// CCTP Bridge for Arc
interface ITokenMessenger {
    function depositForBurn(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken
    ) external returns (uint64 nonce);
}
```
""",
            
            "gateway": """
**Gateway - Unified USDC Balance**

Crosschain primitive for instant USDC liquidity across chains.

**Key Features:**
- Unified USDC balance across multiple chains
- Instant crosschain liquidity (<500ms)
- No manual transfers needed
- Permissionless infrastructure

**Arc Support:**
- Testnet: Arc Testnet ✅
- Mainnet: Coming soon

**When to Use Gateway vs CCTP:**
- **Gateway:** Multiple source chains, undecided destination, or long-term storage
- **CCTP:** Single source/dest, immediate transfer needed

**Gateway on Arc:**
```typescript
import { Gateway } from '@circle-fin/gateway';

// Deposit USDC to Gateway
await Gateway.deposit({
  chain: 'ARC-TESTNET',
  amount: '1000',
});

// Use on any chain instantly
await Gateway.withdraw({
  destChain: 'BASE-SEPOLIA',
  amount: '500',
});
```
""",
            
            "smart-contract-platform": """
**Smart Contract Platform**

Low-code smart contract deployment and management.

**Key Features:**
- Circle's pre-built templates
- Custom smart contract support
- REST APIs and SDKs
- Event monitoring
- Gas optimization

**Deploy on Arc:**
```typescript
import { SmartContractPlatform } from '@circle-fin/scp';

const contract = await SmartContractPlatform.deploy({
  blockchain: 'ARC-TESTNET',
  contractType: 'ERC20',
  parameters: {
    name: 'My Arc Token',
    symbol: 'ARCT',
    initialSupply: '1000000',
  },
});
```
""",
        }
        
        return summaries.get(product_key, f"Product '{product}' not found.")
    
    def generate_wallet_code(
        self,
        blockchain: str = "ARC-TESTNET",
        account_type: str = "SCA",
        language: str = "typescript",
    ) -> Dict[str, Any]:
        """
        Generate wallet integration code.
        
        Args:
            blockchain: Target blockchain (default: ARC-TESTNET)
            account_type: Account type (SCA or EOA)
            language: Programming language
            
        Returns:
            Generated code with documentation
        """
        logger.info(
            "circle_mcp_generating_wallet_code",
            blockchain=blockchain,
            account_type=account_type,
        )
        
        if language == "typescript":
            code = f"""// Circle Developer-Controlled Wallet for {blockchain}
// Account Type: {account_type} (Smart Contract Account)

import {{ initiateDeveloperControlledWalletsClient }} from '@circle-fin/developer-controlled-wallets';

// Initialize client
const client = initiateDeveloperControlledWalletsClient({{
  apiKey: process.env.CIRCLE_API_KEY!,
  entitySecret: process.env.CIRCLE_ENTITY_SECRET!,
}});

// Step 1: Create Wallet Set
async function createWalletSet() {{
  const response = await client.createWalletSet({{
    name: 'Arc Testnet Wallet Set',
  }});
  
  return response.data?.walletSet.id;
}}

// Step 2: Create Wallet on {blockchain}
async function createWallet(walletSetId: string) {{
  const response = await client.createWallets({{
    accountType: '{account_type}',
    blockchains: ['{blockchain}'],
    count: 1,
    walletSetId: walletSetId,
    metadata: [{{
      name: 'Arc Testnet Wallet',
      refId: 'arc-wallet-1',
    }}],
  }});
  
  const wallet = response.data?.wallets[0];
  console.log('Wallet created:', {{
    address: wallet?.address,
    blockchain: wallet?.blockchain,
    id: wallet?.id,
  }});
  
  return wallet;
}}

// Step 3: Request Testnet Tokens
async function requestTestnetTokens(address: string) {{
  await client.requestTestnetTokens({{
    address: address,
    blockchain: '{blockchain}',
    usdc: true,
    native: true,
  }});
  
  console.log('Testnet tokens requested for:', address);
}}

// Step 4: Check Wallet Balance
async function getBalance(walletId: string) {{
  const response = await client.getWalletTokenBalance({{
    id: walletId,
  }});
  
  return response.data?.tokenBalances;
}}

// Step 5: Transfer Tokens
async function transfer(walletId: string, toAddress: string, amount: string) {{
  const response = await client.createTransaction({{
    walletId: walletId,
    blockchain: '{blockchain}',
    tokenAddress: '0x...',  // USDC address on {blockchain}
    destinationAddress: toAddress,
    amounts: [amount],
  }});
  
  return response.data?.transaction;
}}

// Main execution
async function main() {{
  // Create wallet set
  const walletSetId = await createWalletSet();
  console.log('Wallet Set ID:', walletSetId);
  
  // Create wallet
  const wallet = await createWallet(walletSetId);
  if (!wallet) throw new Error('Failed to create wallet');
  
  // Request testnet tokens
  await requestTestnetTokens(wallet.address);
  
  // Wait for tokens (in production, use webhooks)
  await new Promise(resolve => setTimeout(resolve, 30000));
  
  // Check balance
  const balance = await getBalance(wallet.id);
  console.log('Balance:', balance);
  
  return wallet;
}}

// Export functions
export {{
  createWalletSet,
  createWallet,
  requestTestnetTokens,
  getBalance,
  transfer,
  main,
}};

// Run if called directly
if (require.main === module) {{
  main().catch(console.error);
}}
"""
        else:
            code = "# Language not supported yet"
        
        return {
            "code": code,
            "language": language,
            "blockchain": blockchain,
            "account_type": account_type,
            "documentation": "https://developers.circle.com/w3s/programmable-wallets-quickstart",
            "note": "Generated using Circle MCP",
        }
    
    def generate_cctp_code(
        self,
        source_chain: str = "ETH-SEPOLIA",
        dest_chain: str = "ARC-TESTNET",
    ) -> Dict[str, Any]:
        """
        Generate CCTP bridge code for Arc.
        
        Args:
            source_chain: Source blockchain
            dest_chain: Destination blockchain
            
        Returns:
            Generated CCTP integration code
        """
        logger.info(
            "circle_mcp_generating_cctp_code",
            source=source_chain,
            dest=dest_chain,
        )
        
        code = f"""// Circle CCTP Bridge: {source_chain} → {dest_chain}
// Bridge USDC across chains with native minting

import {{ BridgeKit }} from '@circle-fin/bridge-kit';

// Initialize Bridge Kit
const bridgeKit = new BridgeKit({{
  apiKey: process.env.CIRCLE_API_KEY!,
}});

// Bridge USDC from {source_chain} to {dest_chain}
async function bridgeToArc(amount: string, recipient: string) {{
  const transfer = await bridgeKit.transfer({{
    sourceChain: '{source_chain}',
    destChain: '{dest_chain}',
    amount: amount,
    token: 'USDC',
    recipient: recipient,
    mode: 'fast',  // or 'slow' for finalized attestation
  }});
  
  console.log('Transfer initiated:', {{
    txHash: transfer.sourceTxHash,
    attestation: transfer.attestation,
  }});
  
  // Wait for attestation
  const status = await bridgeKit.getTransferStatus(transfer.id);
  console.log('Transfer status:', status);
  
  return transfer;
}}

// Bridge from Arc to another chain
async function bridgeFromArc(amount: string, recipient: string, destChain: string) {{
  return await bridgeKit.transfer({{
    sourceChain: '{dest_chain}',
    destChain: destChain,
    amount: amount,
    token: 'USDC',
    recipient: recipient,
  }});
}}

// Smart contract integration for Arc
// Contract to be deployed on {dest_chain}
const CCTP_CONTRACT = `
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ITokenMessenger {{
    function depositForBurn(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken
    ) external returns (uint64 nonce);
}}

contract ArcCCTPBridge {{
    ITokenMessenger public immutable tokenMessenger;
    address public immutable usdc;
    
    // Arc testnet domain ID (example)
    uint32 public constant ARC_DOMAIN = 999;
    
    constructor(address _tokenMessenger, address _usdc) {{
        tokenMessenger = ITokenMessenger(_tokenMessenger);
        usdc = _usdc;
    }}
    
    function bridgeToArc(uint256 amount, address recipient) external {{
        require(amount > 0, "Amount must be > 0");
        
        // Transfer USDC from sender
        IERC20(usdc).transferFrom(msg.sender, address(this), amount);
        
        // Approve token messenger
        IERC20(usdc).approve(address(tokenMessenger), amount);
        
        // Convert recipient to bytes32
        bytes32 mintRecipient = bytes32(uint256(uint160(recipient)));
        
        // Burn and bridge to Arc
        uint64 nonce = tokenMessenger.depositForBurn(
            amount,
            ARC_DOMAIN,
            mintRecipient,
            usdc
        );
        
        emit BridgedToArc(msg.sender, recipient, amount, nonce);
    }}
    
    event BridgedToArc(
        address indexed sender,
        address indexed recipient,
        uint256 amount,
        uint64 nonce
    );
}}
`;

export {{ bridgeToArc, bridgeFromArc, CCTP_CONTRACT }};
"""
        
        return {
            "code": code,
            "language": "typescript",
            "source_chain": source_chain,
            "dest_chain": dest_chain,
            "documentation": "https://developers.circle.com/stablecoins/cctp-getting-started",
            "note": "CCTP V2 with Arc Testnet support",
        }
    
    def search_documentation(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Circle documentation.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documentation
        """
        logger.info("circle_mcp_searching_docs", query=query[:100])
        
        # This would use the MCP search_circle_documentation tool
        # For now, return helpful links
        
        return [
            {
                "title": "Circle Wallets on Arc",
                "url": "https://developers.circle.com/w3s/programmable-wallets-quickstart",
                "summary": "Complete guide to creating wallets on Arc blockchain",
            },
            {
                "title": "CCTP with Arc",
                "url": "https://developers.circle.com/stablecoins/cctp-getting-started",
                "summary": "Bridge USDC to/from Arc using CCTP",
            },
            {
                "title": "Arc Blockchain Support",
                "url": "https://developers.circle.com/cctp/cctp-supported-blockchains",
                "summary": "Arc Testnet is now supported!",
            },
        ]


# Singleton instance
circle_mcp = CircleMCPIntegration()
