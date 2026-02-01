"""
Web3 tools for interacting with Arc blockchain.
"""

from typing import Any, Dict, Optional

from web3 import Web3
from web3.exceptions import Web3Exception

from src.utils import get_logger

logger = get_logger(__name__)


class Web3BalanceChecker:
    """
    Tool for checking wallet balances on Arc blockchain.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize balance checker.
        
        Args:
            rpc_url: Arc RPC endpoint URL
        """
        # Default to Ethereum mainnet for testing, can be changed to Arc RPC
        self.rpc_url = rpc_url or "https://eth.llamarpc.com"
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            connected = self.w3.is_connected()
            logger.info(
                "web3_balance_checker_initialized",
                rpc_url=self.rpc_url,
                connected=connected,
            )
        except Exception as e:
            logger.error("web3_connection_failed", error=str(e))
            self.w3 = None
    
    async def check_balance(self, address: str) -> Dict[str, Any]:
        """
        Check balance for an address.
        
        Args:
            address: Wallet address
            
        Returns:
            Balance information
        """
        logger.info("checking_balance", address=address[:10] + "...")
        
        if not self.w3:
            return {
                "address": address,
                "balance": "N/A",
                "network": "Unknown",
                "error": "Web3 connection not available",
            }
        
        try:
            # Check if address is valid
            if not Web3.is_address(address):
                return {
                    "address": address,
                    "balance": "N/A",
                    "error": "Invalid Ethereum address format",
                }
            
            # Get balance
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            # Get network info
            try:
                chain_id = self.w3.eth.chain_id
                network_name = {
                    1: "Ethereum Mainnet",
                    5: "Goerli Testnet",
                    11155111: "Sepolia Testnet",
                }.get(chain_id, f"Chain ID {chain_id}")
            except:
                network_name = "Unknown Network"
            
            logger.info(
                "balance_checked",
                address=address[:10] + "...",
                balance=str(balance_eth),
            )
            
            return {
                "address": address,
                "balance": f"{balance_eth:.6f} ETH",
                "balance_wei": str(balance_wei),
                "network": network_name,
                "rpc_url": self.rpc_url,
            }
            
        except Web3Exception as e:
            logger.error("web3_balance_error", address=address[:10], error=str(e))
            return {
                "address": address,
                "balance": "N/A",
                "error": f"Web3 error: {str(e)}",
            }
        except Exception as e:
            logger.error("balance_check_error", address=address[:10], error=str(e))
            return {
                "address": address,
                "balance": "N/A",
                "error": str(e),
            }


class Web3TransactionInfo:
    """
    Tool for getting transaction information.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize transaction info tool.
        
        Args:
            rpc_url: Arc RPC endpoint URL
        """
        self.rpc_url = rpc_url or "https://eth.llamarpc.com"
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            connected = self.w3.is_connected()
            logger.info(
                "web3_transaction_info_initialized",
                rpc_url=self.rpc_url,
                connected=connected,
            )
        except Exception as e:
            logger.error("web3_connection_failed", error=str(e))
            self.w3 = None
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction details.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction information
        """
        logger.info("getting_transaction", tx_hash=tx_hash[:10] + "...")
        
        if not self.w3:
            return {
                "hash": tx_hash,
                "status": "Unknown",
                "error": "Web3 connection not available",
            }
        
        try:
            # Get transaction
            tx = self.w3.eth.get_transaction(tx_hash)
            
            if not tx:
                return {
                    "hash": tx_hash,
                    "status": "Not Found",
                    "error": "Transaction not found on this network",
                }
            
            # Get transaction receipt for status
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                status = "Success" if receipt['status'] == 1 else "Failed"
                gas_used = receipt.get('gasUsed', 0)
            except:
                status = "Pending"
                gas_used = None
            
            # Get network info
            try:
                chain_id = self.w3.eth.chain_id
                network_name = {
                    1: "Ethereum Mainnet",
                    5: "Goerli Testnet",
                    11155111: "Sepolia Testnet",
                }.get(chain_id, f"Chain ID {chain_id}")
            except:
                network_name = "Unknown Network"
            
            result = {
                "hash": tx_hash,
                "status": status,
                "from": tx['from'],
                "to": tx.get('to', 'Contract Creation'),
                "value": f"{self.w3.from_wei(tx['value'], 'ether')} ETH",
                "gas_price": f"{self.w3.from_wei(tx['gasPrice'], 'gwei')} gwei",
                "network": network_name,
            }
            
            if gas_used is not None:
                result["gas_used"] = gas_used
            
            logger.info(
                "transaction_retrieved",
                tx_hash=tx_hash[:10] + "...",
                status=status,
            )
            
            return result
            
        except Web3Exception as e:
            logger.error("web3_tx_error", tx_hash=tx_hash[:10], error=str(e))
            return {
                "hash": tx_hash,
                "status": "Error",
                "error": f"Web3 error: {str(e)}",
            }
        except Exception as e:
            logger.error("tx_lookup_error", tx_hash=tx_hash[:10], error=str(e))
            return {
                "hash": tx_hash,
                "status": "Error",
                "error": str(e),
            }


class Web3ContractReader:
    """
    Tool for reading smart contract data.
    """
    
    # Standard ERC20 ABI for basic token info
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
    ]
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize contract reader.
        
        Args:
            rpc_url: Arc RPC endpoint URL
        """
        self.rpc_url = rpc_url or "https://eth.llamarpc.com"
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            connected = self.w3.is_connected()
            logger.info(
                "web3_contract_reader_initialized",
                rpc_url=self.rpc_url,
                connected=connected,
            )
        except Exception as e:
            logger.error("web3_connection_failed", error=str(e))
            self.w3 = None
    
    async def read_contract(
        self,
        contract_address: str,
        function_name: Optional[str] = None,
        abi: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Read data from a smart contract.
        
        Args:
            contract_address: Contract address
            function_name: Function to call (optional, defaults to ERC20 info)
            abi: Contract ABI (optional, defaults to ERC20)
            
        Returns:
            Function result
        """
        logger.info(
            "reading_contract",
            address=contract_address[:10] + "...",
            function=function_name or "token_info",
        )
        
        if not self.w3:
            return {
                "contract": contract_address,
                "error": "Web3 connection not available",
            }
        
        try:
            # Check if address is valid
            if not Web3.is_address(contract_address):
                return {
                    "contract": contract_address,
                    "error": "Invalid contract address format",
                }
            
            checksum_address = Web3.to_checksum_address(contract_address)
            
            # Use ERC20 ABI by default
            contract_abi = abi or self.ERC20_ABI
            contract = self.w3.eth.contract(
                address=checksum_address,
                abi=contract_abi,
            )
            
            # If no function specified, try to get ERC20 token info
            if not function_name:
                try:
                    name = contract.functions.name().call()
                    symbol = contract.functions.symbol().call()
                    decimals = contract.functions.decimals().call()
                    total_supply = contract.functions.totalSupply().call()
                    
                    return {
                        "contract": contract_address,
                        "type": "ERC20 Token",
                        "name": name,
                        "symbol": symbol,
                        "decimals": decimals,
                        "total_supply": str(total_supply),
                        "total_supply_formatted": f"{total_supply / (10 ** decimals):,.2f}",
                    }
                except Exception as e:
                    return {
                        "contract": contract_address,
                        "error": f"Not an ERC20 token or function not available: {str(e)}",
                        "note": "Provide ABI for custom contract interaction",
                    }
            else:
                # Call specific function
                try:
                    func = getattr(contract.functions, function_name)
                    result = func().call()
                    
                    return {
                        "contract": contract_address,
                        "function": function_name,
                        "result": str(result),
                    }
                except AttributeError:
                    return {
                        "contract": contract_address,
                        "function": function_name,
                        "error": "Function not found in ABI",
                    }
                except Exception as e:
                    return {
                        "contract": contract_address,
                        "function": function_name,
                        "error": str(e),
                    }
                    
        except Web3Exception as e:
            logger.error("web3_contract_error", address=contract_address[:10], error=str(e))
            return {
                "contract": contract_address,
                "error": f"Web3 error: {str(e)}",
            }
        except Exception as e:
            logger.error("contract_read_error", address=contract_address[:10], error=str(e))
            return {
                "contract": contract_address,
                "error": str(e),
            }


class Web3ToolsManager:
    """
    Manager for all Web3 tools.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Web3 tools manager.
        
        Args:
            rpc_url: Arc RPC endpoint URL
        """
        self.rpc_url = rpc_url
        
        # Initialize tools
        self.balance_checker = Web3BalanceChecker(rpc_url)
        self.transaction_info = Web3TransactionInfo(rpc_url)
        self.contract_reader = Web3ContractReader(rpc_url)
        
        logger.info("web3_tools_manager_initialized")
    
    def get_tool(self, tool_name: str):
        """
        Get a specific Web3 tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance
        """
        tools = {
            "balance_checker": self.balance_checker,
            "transaction_info": self.transaction_info,
            "contract_reader": self.contract_reader,
        }
        
        return tools.get(tool_name)
