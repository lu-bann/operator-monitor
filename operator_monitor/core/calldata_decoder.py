"""Transaction calldata decoding utilities"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)


class BLSUtils:
    """BLS12-381 utilities for G1 point compression"""
    
    # BLS12-381 field modulus as defined in the Solidity contract
    BASE_FIELD_MODULUS = [
        0x000000000000000000000000000000001a0111ea397fe69a4b1ba7b6434bacd7,
        0x64774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
    ]
    
    @staticmethod
    def _greater_than(a_high: int, a_low: int, b_high: int, b_low: int) -> bool:
        """
        Returns true if `a` is lexicographically greater than `b`
        Adapted from the Solidity _greaterThan function
        """
        # Only compare the unequal words
        if a_high == b_high:
            word_a = a_low
            word_b = b_low
            mask = 1 << 255
        else:
            word_a = a_high
            word_b = b_high
            mask = 1 << 127  # Only check for lower 16 bytes in the first word
        
        # Bit-wise comparison
        for i in range(256):
            x = word_a & mask
            y = word_b & mask
            
            if x == 0 and y != 0:
                return False
            if x != 0 and y == 0:
                return True
            
            mask = mask >> 1
        
        return False
    
    @staticmethod
    def negate_g1_point(x_a: int, x_b: int, y_a: int, y_b: int) -> tuple:
        """
        Negates a G1 point by reflecting it over the x-axis
        Returns (x_a, x_b, y_neg_a, y_neg_b)
        """
        field_modulus = BLSUtils.BASE_FIELD_MODULUS.copy()
        
        # Perform word-wise elementary subtraction: field_modulus - y
        if field_modulus[1] < y_b:
            y_neg_b = (2**256 - 1) - (y_b - field_modulus[1]) + 1
            field_modulus[0] -= 1  # borrow
        else:
            y_neg_b = field_modulus[1] - y_b
        
        y_neg_a = field_modulus[0] - y_a
        
        return x_a, x_b, y_neg_a, y_neg_b
    
    @staticmethod
    def compress_g1_point(x_a: int, x_b: int, y_a: int, y_b: int) -> tuple:
        """
        Compresses a G1 point according to BLS12-381 compression standard
        Returns (compressed_x_a, compressed_x_b) as the compressed form
        """
        # Start with the x coordinate
        r_a = x_a
        r_b = x_b
        
        # Set the first MSB (compression flag)
        r_a = r_a | (1 << 127)
        
        # Second MSB is left to be 0 since we assume no infinity points
        
        # Set the third MSB if point.y is lexicographically larger than the y in negated point
        _, _, neg_y_a, neg_y_b = BLSUtils.negate_g1_point(x_a, x_b, y_a, y_b)
        
        if BLSUtils._greater_than(y_a, y_b, neg_y_a, neg_y_b):
            r_a = r_a | (1 << 125)
        
        return r_a, r_b


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
                
            # Extract function selector (first 4 bytes), handling 0x prefix
            if calldata.startswith('0x'):
                selector = calldata[2:10]  # Skip 0x prefix, take next 8 chars (4 bytes)
            else:
                selector = calldata[:8]
            return selector == self.function_selector
            
        except Exception as e:
            logger.debug(f"Error checking function selector: {e}")
            return False
    
    def decode_register_validators_calldata(self, calldata: str) -> Optional[Dict[str, Any]]:
        """
        Decode registerValidators function calldata using contract ABI
        
        Args:
            calldata: Transaction input data as hex string
            
        Returns:
            Dict containing decoded parameters or None if decoding fails
        """
        try:
            if not self.is_register_validators_call(calldata):
                logger.debug("Calldata is not a registerValidators function call")
                return None
            
            # Use contract ABI to decode the function input
            func_obj, func_params = self.contract_interface.decode_function_input(calldata)
            
            # Extract the registrations array from decoded parameters
            registrations_array = func_params.get('registrations', [])
            
            if not registrations_array:
                logger.debug("No registrations found in decoded parameters")
                return None
            
            # Sanity check: reject unreasonably large array lengths
            if len(registrations_array) > 1000:  # Reasonable upper bound for validator registrations
                logger.warning(f"Array length {len(registrations_array)} exceeds reasonable limit")
                return None
            
            parsed_registrations = []
            
            for i, registration in enumerate(registrations_array):
                try:
                    # Extract pubkey and signature from the decoded registration
                    # ABI decoder returns structured dict with 'pubkey' and 'signature' keys
                    pubkey_data = registration['pubkey']
                    signature_data = registration['signature']
                    
                    # Parse G1Point pubkey - already structured as {'x': {'a': val, 'b': val}, 'y': {'a': val, 'b': val}}
                    pubkey = {
                        'x': {
                            'a': str(pubkey_data['x']['a']),
                            'b': str(pubkey_data['x']['b'])
                        },
                        'y': {
                            'a': str(pubkey_data['y']['a']),
                            'b': str(pubkey_data['y']['b'])
                        }
                    }
                    
                    # Parse G2Point signature - already structured 
                    signature = {
                        'x': {
                            'c0': {
                                'a': str(signature_data['x']['c0']['a']),
                                'b': str(signature_data['x']['c0']['b'])
                            },
                            'c1': {
                                'a': str(signature_data['x']['c1']['a']),
                                'b': str(signature_data['x']['c1']['b'])
                            }
                        },
                        'y': {
                            'c0': {
                                'a': str(signature_data['y']['c0']['a']),
                                'b': str(signature_data['y']['c0']['b'])
                            },
                            'c1': {
                                'a': str(signature_data['y']['c1']['a']),
                                'b': str(signature_data['y']['c1']['b'])
                            }
                        }
                    }
                    
                    # Create compressed pubkey using BLS compression
                    compressed_x_a, compressed_x_b = BLSUtils.compress_g1_point(
                        pubkey_data['x']['a'], pubkey_data['x']['b'],
                        pubkey_data['y']['a'], pubkey_data['y']['b']
                    )
                    # Format as hex without leading zeros (except for 0x prefix)
                    pubkey_hex = f"0x{compressed_x_a:x}{compressed_x_b:064x}"
                    
                    # Create full signature hex representation
                    signature_hex = f"0x{signature_data['x']['c0']['a']:064x}{signature_data['x']['c0']['b']:064x}{signature_data['x']['c1']['a']:064x}{signature_data['x']['c1']['b']:064x}{signature_data['y']['c0']['a']:064x}{signature_data['y']['c0']['b']:064x}{signature_data['y']['c1']['a']:064x}{signature_data['y']['c1']['b']:064x}"
                    
                    parsed_reg = {
                        'index': i,
                        'pubkey': pubkey,
                        'signature': signature,
                        'pubkey_hex': pubkey_hex,
                        'signature_hex': signature_hex
                    }
                    parsed_registrations.append(parsed_reg)
                    
                except Exception as e:
                    logger.warning(f"Error parsing registration {i}: {e}")
                    continue
            
            result = {
                'function': 'registerValidators',
                'validator_count': len(parsed_registrations),
                'registrations': parsed_registrations
            }
            
            logger.debug(f"Successfully decoded registerValidators calldata with {len(parsed_registrations)} validators")
            return result
            
        except Exception as e:
            logger.error(f"Error decoding registerValidators calldata: {e}")
            return None
    
    def format_bls_pubkey(self, pubkey: Dict[str, Any], truncate: bool = True) -> str:
        """
        Format BLS public key for display using compressed form
        
        Args:
            pubkey: Dictionary with nested 'x' and 'y' coordinates containing 'a' and 'b' values
            truncate: Whether to truncate the key for display (default True)
            
        Returns:
            Formatted public key string (compressed)
        """
        try:
            # Get the coordinates
            x_a = int(pubkey['x']['a'])
            x_b = int(pubkey['x']['b'])
            y_a = int(pubkey['y']['a'])
            y_b = int(pubkey['y']['b'])
            
            # Compress the point
            compressed_x_a, compressed_x_b = BLSUtils.compress_g1_point(x_a, x_b, y_a, y_b)
            compressed_hex = f"{compressed_x_a:x}{compressed_x_b:064x}"
            
            if truncate:
                return f"0x{compressed_hex[:8]}...{compressed_hex[-8:]}"
            else:
                return f"0x{compressed_hex}"
        except Exception as e:
            logger.debug(f"Error formatting BLS pubkey: {e}")
            return "Invalid pubkey"
    
    def format_decoded_registrations(self, decoded: Dict[str, Any], full_pubkeys: bool = False) -> str:
        """
        Format decoded registration data for display
        
        Args:
            decoded: Decoded calldata from decode_register_validators_calldata
            full_pubkeys: Whether to show full pubkeys (True) or truncated (False)
            
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
            
            # Show first few validators 
            max_display = min(5, decoded['validator_count'])
            for i in range(max_display):
                reg = decoded['registrations'][i]
                if full_pubkeys:
                    # Show full compressed pubkey
                    pubkey_display = reg['pubkey_hex']
                else:
                    # Show truncated pubkey for console readability
                    pubkey_display = self.format_bls_pubkey(reg['pubkey'], truncate=True)
                formatted += f"     - Validator #{i+1}: {pubkey_display}\n"
            
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
                return self.format_decoded_registrations(decoded, full_pubkeys=True)
            else:
                logger.debug("Transaction to EigenLayerMiddleware but not registerValidators call")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing transaction for registry event: {e}")
            return None