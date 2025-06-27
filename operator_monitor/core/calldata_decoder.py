"""Transaction calldata decoding utilities"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)


class CalldataDecoder:
    """Decodes transaction calldata for blockchain function calls"""
    
    def __init__(self, web3: Web3):
        """
        Initialize calldata decoder
        
        Args:
            web3: Web3 instance for ABI decoding
        """
        self.web3 = web3
        
        # EigenLayerMiddleware registerValidators function ABI with correct BLS structure
        self.register_validators_abi = {
            "type": "function",
            "name": "registerValidators", 
            "inputs": [
                {
                    "name": "registrations",
                    "type": "tuple[]",
                    "components": [
                        {
                            "name": "pubkey",
                            "type": "tuple",
                            "components": [
                                {
                                    "name": "x",
                                    "type": "tuple",
                                    "components": [
                                        {"name": "a", "type": "uint256"},
                                        {"name": "b", "type": "uint256"}
                                    ]
                                },
                                {
                                    "name": "y",
                                    "type": "tuple",
                                    "components": [
                                        {"name": "a", "type": "uint256"},
                                        {"name": "b", "type": "uint256"}
                                    ]
                                }
                            ]
                        },
                        {
                            "name": "signature",
                            "type": "tuple", 
                            "components": [
                                {
                                    "name": "x",
                                    "type": "tuple",
                                    "components": [
                                        {
                                            "name": "c0",
                                            "type": "tuple",
                                            "components": [
                                                {"name": "a", "type": "uint256"},
                                                {"name": "b", "type": "uint256"}
                                            ]
                                        },
                                        {
                                            "name": "c1",
                                            "type": "tuple",
                                            "components": [
                                                {"name": "a", "type": "uint256"},
                                                {"name": "b", "type": "uint256"}
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "name": "y",
                                    "type": "tuple",
                                    "components": [
                                        {
                                            "name": "c0",
                                            "type": "tuple",
                                            "components": [
                                                {"name": "a", "type": "uint256"},
                                                {"name": "b", "type": "uint256"}
                                            ]
                                        },
                                        {
                                            "name": "c1",
                                            "type": "tuple",
                                            "components": [
                                                {"name": "a", "type": "uint256"},
                                                {"name": "b", "type": "uint256"}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "outputs": [{"name": "", "type": "bytes32"}],
            "stateMutability": "payable"
        }
        
        # Create contract interface for decoding
        try:
            self.contract_interface = self.web3.eth.contract(abi=[self.register_validators_abi])
            # Correct function selector based on complex BLS structure: 0x5bf6539f
            function_signature = "registerValidators((((uint256,uint256),(uint256,uint256)),(((uint256,uint256),(uint256,uint256)),((uint256,uint256),(uint256,uint256))))[])"
            self.function_selector = self.web3.keccak(text=function_signature)[0:4].hex()
            logger.info(f"CalldataDecoder initialized successfully with selector: {self.function_selector}")
        except Exception as e:
            logger.error(f"Error initializing CalldataDecoder: {e}")
            raise
    
    def is_register_validators_call(self, calldata: str) -> bool:
        """
        Check if transaction calldata is a registerValidators function call
        
        Args:
            calldata: Transaction input data as hex string
            
        Returns:
            bool: True if calldata matches registerValidators function signature
        """
        try:
            if not calldata or len(calldata) < 10:  # Must have at least function selector (4 bytes = 8 hex chars + 0x)
                return False
                
            # Extract function selector (first 4 bytes)
            selector = calldata[:8]
            return selector == self.function_selector
            
        except Exception as e:
            logger.debug(f"Error checking function selector: {e}")
            return False
    
    def decode_register_validators_calldata(self, calldata: str) -> Optional[Dict[str, Any]]:
        """
        Decode registerValidators function calldata
        
        Args:
            calldata: Transaction input data as hex string
            
        Returns:
            Dict containing decoded parameters or None if decoding fails
        """
        try:
            if not self.is_register_validators_call(calldata):
                logger.debug("Calldata is not a registerValidators function call")
                return None
            
            # Decode the function call
            decoded = self.contract_interface.decode_function_input(calldata)
            function_obj, inputs = decoded
            
            if function_obj.function_identifier != "registerValidators":
                logger.debug(f"Function identifier mismatch: {function_obj.function_identifier}")
                return None
            
            registrations = inputs.get('registrations', [])
            
            # Parse SignedRegistration array with complex BLS structure
            parsed_registrations = []
            for i, reg in enumerate(registrations):
                try:
                    pubkey = reg[0]  # First element is G1Point (pubkey)
                    signature = reg[1]  # Second element is G2Point (signature)
                    
                    # Extract G1Point coordinates (pubkey.x.a, pubkey.x.b, pubkey.y.a, pubkey.y.b)
                    pubkey_x_a = str(pubkey[0][0])  # pubkey.x.a
                    pubkey_x_b = str(pubkey[0][1])  # pubkey.x.b
                    pubkey_y_a = str(pubkey[1][0])  # pubkey.y.a
                    pubkey_y_b = str(pubkey[1][1])  # pubkey.y.b
                    
                    # Extract G2Point coordinates (signature.x.c0, signature.x.c1, signature.y.c0, signature.y.c1)
                    sig_x_c0_a = str(signature[0][0][0])  # signature.x.c0.a
                    sig_x_c0_b = str(signature[0][0][1])  # signature.x.c0.b
                    sig_x_c1_a = str(signature[0][1][0])  # signature.x.c1.a
                    sig_x_c1_b = str(signature[0][1][1])  # signature.x.c1.b
                    sig_y_c0_a = str(signature[1][0][0])  # signature.y.c0.a
                    sig_y_c0_b = str(signature[1][0][1])  # signature.y.c0.b
                    sig_y_c1_a = str(signature[1][1][0])  # signature.y.c1.a
                    sig_y_c1_b = str(signature[1][1][1])  # signature.y.c1.b
                    
                    parsed_reg = {
                        'index': i,
                        'pubkey': {
                            'x': {'a': pubkey_x_a, 'b': pubkey_x_b},
                            'y': {'a': pubkey_y_a, 'b': pubkey_y_b}
                        },
                        'signature': {
                            'x': {
                                'c0': {'a': sig_x_c0_a, 'b': sig_x_c0_b},
                                'c1': {'a': sig_x_c1_a, 'b': sig_x_c1_b}
                            },
                            'y': {
                                'c0': {'a': sig_y_c0_a, 'b': sig_y_c0_b},
                                'c1': {'a': sig_y_c1_a, 'b': sig_y_c1_b}
                            }
                        },
                        'pubkey_hex': f"0x{int(pubkey_x_a):064x}{int(pubkey_x_b):064x}{int(pubkey_y_a):064x}{int(pubkey_y_b):064x}",
                        'signature_hex': f"0x{int(sig_x_c0_a):064x}{int(sig_x_c0_b):064x}{int(sig_x_c1_a):064x}{int(sig_x_c1_b):064x}{int(sig_y_c0_a):064x}{int(sig_y_c0_b):064x}{int(sig_y_c1_a):064x}{int(sig_y_c1_b):064x}"
                    }
                    parsed_registrations.append(parsed_reg)
                except Exception as e:
                    logger.warning(f"Error parsing registration {i}: {e}")
                    continue
            
            result = {
                'function': 'registerValidators',
                'validator_count': len(parsed_registrations),
                'registrations': parsed_registrations,
                'raw_inputs': inputs
            }
            
            logger.debug(f"Successfully decoded registerValidators calldata with {len(parsed_registrations)} validators")
            return result
            
        except Exception as e:
            logger.error(f"Error decoding registerValidators calldata: {e}")
            return None
    
    def format_bls_pubkey(self, pubkey: Dict[str, Any]) -> str:
        """
        Format BLS public key for display
        
        Args:
            pubkey: Dictionary with nested 'x' and 'y' coordinates containing 'a' and 'b' values
            
        Returns:
            Formatted public key string
        """
        try:
            # Handle new nested structure: pubkey.x.a, pubkey.x.b, pubkey.y.a, pubkey.y.b
            x_a = int(pubkey['x']['a'])
            x_b = int(pubkey['x']['b'])
            y_a = int(pubkey['y']['a'])
            y_b = int(pubkey['y']['b'])
            
            x_hex = f"{x_a:064x}{x_b:064x}"
            y_hex = f"{y_a:064x}{y_b:064x}"
            return f"0x{x_hex[:8]}...{y_hex[-8:]}"
        except Exception as e:
            logger.debug(f"Error formatting BLS pubkey: {e}")
            return "Invalid pubkey"
    
    def format_decoded_registrations(self, decoded: Dict[str, Any]) -> str:
        """
        Format decoded registration data for display
        
        Args:
            decoded: Decoded calldata from decode_register_validators_calldata
            
        Returns:
            Formatted string for display
        """
        if not decoded:
            return "❌ Failed to decode calldata"
        
        formatted = f"📋 Transaction Analysis:\n"
        formatted += f"   🔍 Function: {decoded['function']}()\n"
        formatted += f"   📊 Validators Registered: {decoded['validator_count']}\n"
        
        if decoded['validator_count'] > 0:
            formatted += f"   🔑 Validator Public Keys:\n"
            
            # Show first few validators with truncated keys for readability
            max_display = min(5, decoded['validator_count'])
            for i in range(max_display):
                reg = decoded['registrations'][i]
                short_key = self.format_bls_pubkey(reg['pubkey'])
                formatted += f"     - Validator #{i+1}: {short_key}\n"
            
            if decoded['validator_count'] > max_display:
                remaining = decoded['validator_count'] - max_display
                formatted += f"     - ... and {remaining} more validators\n"
        
        formatted += f"   ✅ Triggered by EigenLayerMiddleware\n"
        
        return formatted
    
    def analyze_transaction_for_registry_event(self, transaction: Dict[str, Any], 
                                               eigenlayer_middleware_address: str) -> Optional[str]:
        """
        Analyze transaction for Registry OperatorRegistered events
        
        Args:
            transaction: Transaction data dict
            eigenlayer_middleware_address: EigenLayerMiddleware contract address to check against
            
        Returns:
            Formatted analysis string or None if not applicable
        """
        try:
            # Check if transaction was sent to EigenLayerMiddleware
            to_address = transaction.get('to', '').lower()
            middleware_address = eigenlayer_middleware_address.lower()
            
            if to_address != middleware_address:
                logger.debug(f"Transaction not sent to EigenLayerMiddleware: {to_address} vs {middleware_address}")
                return None
            
            # Decode the calldata
            calldata = transaction.get('input', '0x')
            decoded = self.decode_register_validators_calldata(calldata)
            
            if decoded:
                return self.format_decoded_registrations(decoded)
            else:
                logger.debug("Transaction to EigenLayerMiddleware but not registerValidators call")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing transaction for registry event: {e}")
            return None