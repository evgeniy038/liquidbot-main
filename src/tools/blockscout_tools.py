"""
Blockscout API tools for blockchain exploration and testnet operations.
Documentation: https://docs.blockscout.com/devs
"""

import os
from typing import Any, Dict, List, Optional

import httpx

from src.utils import get_logger

logger = get_logger(__name__)


class BlockscoutAPI:
    """
    Blockscout API integration for blockchain exploration.
    Supports account, transaction, block, contract, token, and stats queries.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Blockscout API client.
        
        Args:
            base_url: Blockscout instance URL (e.g., https://eth.blockscout.com)
            api_key: Optional API key for authenticated requests
        """
        self.base_url = base_url or "https://eth.blockscout.com"
        self.api_key = api_key or os.getenv("BLOCKSCOUT_API_KEY", "")
        self.api_endpoint = f"{self.base_url}/api"
        self.timeout = 15.0
        
        logger.info(
            "blockscout_api_initialized",
            base_url=self.base_url,
            has_api_key=bool(self.api_key),
        )
    
    async def _make_request(
        self,
        module: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make API request to Blockscout.
        
        Args:
            module: API module (account, transaction, block, etc.)
            action: API action
            params: Additional parameters
            
        Returns:
            API response data
        """
        request_params = {
            "module": module,
            "action": action,
        }
        
        if params:
            request_params.update(params)
        
        if self.api_key:
            request_params["apikey"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.api_endpoint,
                    params=request_params,
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "0" and data.get("message") == "NOTOK":
                    logger.warning(
                        "blockscout_api_error",
                        module=module,
                        action=action,
                        error=data.get("result", "Unknown error"),
                    )
                    return {
                        "error": data.get("result", "API request failed"),
                        "status": "0",
                    }
                
                return data
                
        except httpx.TimeoutException:
            logger.error(
                "blockscout_api_timeout",
                module=module,
                action=action,
            )
            return {
                "error": "Request timed out",
                "status": "0",
            }
        except Exception as e:
            logger.error(
                "blockscout_api_request_error",
                module=module,
                action=action,
                error=str(e),
            )
            return {
                "error": str(e),
                "status": "0",
            }
    
    # Account Module
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get ETH balance for an address.
        
        Args:
            address: Wallet address
            
        Returns:
            Balance information
        """
        logger.info("blockscout_get_balance", address=address[:10] + "...")
        
        result = await self._make_request(
            module="account",
            action="balance",
            params={"address": address},
        )
        
        if "error" in result:
            return result
        
        balance_wei = result.get("result", "0")
        balance_eth = int(balance_wei) / 10**18
        
        return {
            "address": address,
            "balance_wei": balance_wei,
            "balance_eth": f"{balance_eth:.6f}",
            "status": "1",
        }
    
    async def get_balance_multi(self, addresses: List[str]) -> Dict[str, Any]:
        """
        Get ETH balance for multiple addresses.
        
        Args:
            addresses: List of wallet addresses (max 20)
            
        Returns:
            Balance information for all addresses
        """
        logger.info("blockscout_get_balance_multi", count=len(addresses))
        
        address_list = ",".join(addresses[:20])  # Max 20 addresses
        
        result = await self._make_request(
            module="account",
            action="balancemulti",
            params={"address": address_list},
        )
        
        if "error" in result:
            return result
        
        balances = result.get("result", [])
        
        for balance in balances:
            balance_wei = int(balance.get("balance", "0"))
            balance["balance_eth"] = f"{balance_wei / 10**18:.6f}"
        
        return {
            "addresses": addresses,
            "balances": balances,
            "status": "1",
        }
    
    async def get_transactions(
        self,
        address: str,
        startblock: int = 0,
        endblock: int = 99999999,
        page: int = 1,
        offset: int = 10,
        sort: str = "desc",
    ) -> Dict[str, Any]:
        """
        Get list of transactions for an address.
        
        Args:
            address: Wallet address
            startblock: Starting block number
            endblock: Ending block number
            page: Page number
            offset: Number of transactions per page (max 10000)
            sort: Sort order (asc/desc)
            
        Returns:
            Transaction list
        """
        logger.info("blockscout_get_transactions", address=address[:10] + "...")
        
        result = await self._make_request(
            module="account",
            action="txlist",
            params={
                "address": address,
                "startblock": startblock,
                "endblock": endblock,
                "page": page,
                "offset": offset,
                "sort": sort,
            },
        )
        
        return result
    
    async def get_token_balance(
        self,
        address: str,
        contract_address: str,
    ) -> Dict[str, Any]:
        """
        Get token balance for an address.
        
        Args:
            address: Wallet address
            contract_address: Token contract address
            
        Returns:
            Token balance
        """
        logger.info(
            "blockscout_get_token_balance",
            address=address[:10] + "...",
            contract=contract_address[:10] + "...",
        )
        
        result = await self._make_request(
            module="account",
            action="tokenbalance",
            params={
                "address": address,
                "contractaddress": contract_address,
            },
        )
        
        return result
    
    # Transaction Module
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction execution status.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction status
        """
        logger.info("blockscout_get_tx_status", tx_hash=tx_hash[:10] + "...")
        
        result = await self._make_request(
            module="transaction",
            action="gettxreceiptstatus",
            params={"txhash": tx_hash},
        )
        
        if "error" in result:
            return result
        
        status_data = result.get("result", {})
        status = status_data.get("status", "")
        
        return {
            "tx_hash": tx_hash,
            "status": "Success" if status == "1" else "Failed" if status == "0" else "Unknown",
            "raw_status": status,
        }
    
    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt
        """
        logger.info("blockscout_get_tx_receipt", tx_hash=tx_hash[:10] + "...")
        
        result = await self._make_request(
            module="transaction",
            action="gettxinfo",
            params={"txhash": tx_hash},
        )
        
        return result
    
    # Block Module
    async def get_block_reward(self, block_number: int) -> Dict[str, Any]:
        """
        Get block and uncle rewards.
        
        Args:
            block_number: Block number
            
        Returns:
            Block reward information
        """
        logger.info("blockscout_get_block_reward", block=block_number)
        
        result = await self._make_request(
            module="block",
            action="getblockreward",
            params={"blockno": block_number},
        )
        
        return result
    
    async def get_block_countdown(self, block_number: int) -> Dict[str, Any]:
        """
        Get estimated time remaining until a certain block is mined.
        
        Args:
            block_number: Target block number
            
        Returns:
            Block countdown information
        """
        logger.info("blockscout_get_block_countdown", block=block_number)
        
        result = await self._make_request(
            module="block",
            action="getblockcountdown",
            params={"blockno": block_number},
        )
        
        return result
    
    # Contract Module
    async def get_contract_abi(self, contract_address: str) -> Dict[str, Any]:
        """
        Get contract ABI for verified contracts.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract ABI
        """
        logger.info("blockscout_get_contract_abi", contract=contract_address[:10] + "...")
        
        result = await self._make_request(
            module="contract",
            action="getabi",
            params={"address": contract_address},
        )
        
        return result
    
    async def get_contract_source(self, contract_address: str) -> Dict[str, Any]:
        """
        Get contract source code for verified contracts.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract source code
        """
        logger.info("blockscout_get_contract_source", contract=contract_address[:10] + "...")
        
        result = await self._make_request(
            module="contract",
            action="getsourcecode",
            params={"address": contract_address},
        )
        
        return result
    
    # Token Module
    async def get_token_info(self, contract_address: str) -> Dict[str, Any]:
        """
        Get token information.
        
        Args:
            contract_address: Token contract address
            
        Returns:
            Token information
        """
        logger.info("blockscout_get_token_info", contract=contract_address[:10] + "...")
        
        result = await self._make_request(
            module="token",
            action="getToken",
            params={"contractaddress": contract_address},
        )
        
        return result
    
    async def get_token_holders(
        self,
        contract_address: str,
        page: int = 1,
        offset: int = 10,
    ) -> Dict[str, Any]:
        """
        Get token holder list.
        
        Args:
            contract_address: Token contract address
            page: Page number
            offset: Number of holders per page
            
        Returns:
            Token holder list
        """
        logger.info("blockscout_get_token_holders", contract=contract_address[:10] + "...")
        
        result = await self._make_request(
            module="token",
            action="getTokenHolders",
            params={
                "contractaddress": contract_address,
                "page": page,
                "offset": offset,
            },
        )
        
        return result
    
    # Stats Module
    async def get_total_supply(self) -> Dict[str, Any]:
        """
        Get total ETH supply.
        
        Returns:
            Total supply information
        """
        logger.info("blockscout_get_total_supply")
        
        result = await self._make_request(
            module="stats",
            action="ethsupply",
        )
        
        return result
    
    async def get_eth_price(self) -> Dict[str, Any]:
        """
        Get ETH price in USD and BTC.
        
        Returns:
            Price information
        """
        logger.info("blockscout_get_eth_price")
        
        result = await self._make_request(
            module="stats",
            action="ethprice",
        )
        
        return result


class BlockscoutToolsManager:
    """
    Manager for Blockscout API tools with formatted outputs.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Blockscout tools manager.
        
        Args:
            base_url: Blockscout instance URL
            api_key: Optional API key
        """
        self.api = BlockscoutAPI(base_url, api_key)
        logger.info("blockscout_tools_manager_initialized")
    
    def format_balance_result(self, result: Dict[str, Any]) -> str:
        """Format balance result for display."""
        if "error" in result:
            return f"❌ **Error:** {result['error']}"
        
        return (
            f"💰 **Balance for {result['address'][:10]}...{result['address'][-8:]}**\n\n"
            f"**ETH:** {result['balance_eth']}\n"
            f"**Wei:** {result['balance_wei']}"
        )
    
    def format_transactions_result(self, result: Dict[str, Any]) -> str:
        """Format transactions result for display."""
        if "error" in result:
            return f"❌ **Error:** {result['error']}"
        
        txs = result.get("result", [])
        
        if not txs:
            return "📭 No transactions found."
        
        formatted = f"📜 **Recent Transactions** (showing {len(txs)})\n\n"
        
        for i, tx in enumerate(txs[:5], 1):  # Show first 5
            status = "✅" if tx.get("txreceipt_status") == "1" else "❌"
            formatted += (
                f"{status} **Tx {i}**\n"
                f"Hash: `{tx.get('hash', '')[:20]}...`\n"
                f"From: `{tx.get('from', '')[:10]}...`\n"
                f"To: `{tx.get('to', '')[:10]}...`\n"
                f"Value: {int(tx.get('value', 0)) / 10**18:.6f} ETH\n\n"
            )
        
        if len(txs) > 5:
            formatted += f"_...and {len(txs) - 5} more transactions_"
        
        return formatted
    
    def format_token_info_result(self, result: Dict[str, Any]) -> str:
        """Format token info result for display."""
        if "error" in result:
            return f"❌ **Error:** {result['error']}"
        
        token = result.get("result", {})
        
        if not token:
            return "❌ Token information not available."
        
        return (
            f"🪙 **Token Information**\n\n"
            f"**Name:** {token.get('name', 'N/A')}\n"
            f"**Symbol:** {token.get('symbol', 'N/A')}\n"
            f"**Decimals:** {token.get('decimals', 'N/A')}\n"
            f"**Total Supply:** {token.get('totalSupply', 'N/A')}\n"
            f"**Contract:** `{token.get('contractAddress', 'N/A')}`"
        )
