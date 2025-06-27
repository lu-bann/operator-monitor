"""
Pydantic models for Helix relay delegation messages and validation.

These models match the Rust structures used in the Helix relay:
- SignedDelegation
- DelegationMessage
- SignedRevocation
- RevocationMessage
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import json
from enum import IntEnum
from datetime import datetime


class DelegationAction(IntEnum):
    """Delegation action types matching Helix relay constants."""
    DELEGATE = 0
    REVOKE = 1


class DelegationMessage(BaseModel):
    """
    Delegation message structure matching Helix relay DelegationMessage.
    
    Fields match the Rust struct:
    - action: u8 (0 = delegate, 1 = revoke)
    - validator_pubkey: BlsPublicKey (48 bytes hex)
    - delegatee_pubkey: BlsPublicKey (48 bytes hex)
    """
    action: int = Field(..., description="Action type: 0=delegate, 1=revoke")
    validator_pubkey: str = Field(..., description="Validator BLS public key (hex)")
    delegatee_pubkey: str = Field(..., description="Delegatee BLS public key (hex)")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action is valid delegation action."""
        if v not in [DelegationAction.DELEGATE, DelegationAction.REVOKE]:
            raise ValueError(f"Invalid action: {v}. Must be 0 (delegate) or 1 (revoke)")
        return v
    
    @validator('validator_pubkey', 'delegatee_pubkey')
    def validate_bls_pubkey(cls, v):
        """Validate BLS public key format (48 bytes hex with 0x prefix)."""
        if isinstance(v, str):
            # Require 0x prefix
            if not v.startswith('0x'):
                raise ValueError(f"Public key must start with '0x': {v}")
            
            hex_part = v[2:]
            
            # Check hex format and length
            if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
                raise ValueError(f"Invalid hex format: {v}")
            
            if len(hex_part) != 96:  # 48 bytes = 96 hex characters
                raise ValueError(f"Invalid BLS pubkey length: {len(hex_part)}. Expected 96 hex chars (48 bytes)")
            
            return v  # Keep exactly as provided
        
        raise ValueError(f"Public key must be hex string, got {type(v)}")
    
    @property
    def action_name(self) -> str:
        """Get human-readable action name."""
        return "delegate" if self.action == DelegationAction.DELEGATE else "revoke"
    
    def __str__(self) -> str:
        return f"DelegationMessage(action={self.action_name}, validator={self.validator_pubkey[:10]}..., delegatee={self.delegatee_pubkey[:10]}...)"


class SignedDelegation(BaseModel):
    """
    Signed delegation structure matching Helix relay SignedDelegation.
    
    Contains:
    - message: DelegationMessage
    - signature: BLS signature (hex string)
    """
    message: DelegationMessage = Field(..., description="Delegation message")
    signature: str = Field(..., description="BLS signature (hex)")
    
    @validator('signature')
    def validate_signature(cls, v):
        """Validate BLS signature format."""
        if isinstance(v, str):
            # Remove 0x prefix if present
            if v.startswith('0x'):
                v = v[2:]
            
            # Check hex format
            if not all(c in '0123456789abcdefABCDEF' for c in v):
                raise ValueError(f"Invalid signature hex format: {v}")
            
            # BLS signatures are typically 96 bytes (192 hex chars)
            if len(v) != 192:
                raise ValueError(f"Invalid signature length: {len(v)}. Expected 192 hex chars (96 bytes)")
            
            return v.lower()  # Normalize to lowercase
        
        raise ValueError(f"Signature must be hex string, got {type(v)}")
    
    @property
    def validator_pubkey(self) -> str:
        """Get validator public key from message."""
        return self.message.validator_pubkey
    
    @property
    def delegatee_pubkey(self) -> str:
        """Get delegatee public key from message."""
        return self.message.delegatee_pubkey
    
    @property
    def is_delegation(self) -> bool:
        """Check if this is a delegation (not revocation)."""
        return self.message.action == DelegationAction.DELEGATE
    
    @property
    def is_revocation(self) -> bool:
        """Check if this is a revocation."""
        return self.message.action == DelegationAction.REVOKE
    
    def __str__(self) -> str:
        action = "delegates to" if self.is_delegation else "revokes delegation to"
        return f"{self.validator_pubkey[:10]}... {action} {self.delegatee_pubkey[:10]}..."


class RevocationMessage(BaseModel):
    """
    Revocation message structure matching Helix relay RevocationMessage.
    
    Same structure as DelegationMessage but used for revocations.
    """
    action: int = Field(..., description="Action type: 1=revoke")
    validator_pubkey: str = Field(..., description="Validator BLS public key (hex)")
    delegatee_pubkey: str = Field(..., description="Delegatee BLS public key (hex)")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action is revocation."""
        if v != DelegationAction.REVOKE:
            raise ValueError(f"Invalid revocation action: {v}. Must be 1 (revoke)")
        return v
    
    @validator('validator_pubkey', 'delegatee_pubkey')
    def validate_bls_pubkey(cls, v):
        """Validate BLS public key format (48 bytes hex)."""
        # Same validation as DelegationMessage
        return DelegationMessage.validate_bls_pubkey(v)


class SignedRevocation(BaseModel):
    """
    Signed revocation structure matching Helix relay SignedRevocation.
    """
    message: RevocationMessage = Field(..., description="Revocation message")
    signature: str = Field(..., description="BLS signature (hex)")
    
    @validator('signature')
    def validate_signature(cls, v):
        """Validate BLS signature format."""
        return SignedDelegation.validate_signature(v)


class DelegationQueryResult(BaseModel):
    """Result of querying delegations for a validator."""
    validator_pubkey: str = Field(..., description="Queried validator public key")
    delegations: List[SignedDelegation] = Field(default_factory=list, description="Found delegations")
    active_delegatees: List[str] = Field(default_factory=list, description="Currently active delegatee pubkeys")
    total_delegations: int = Field(0, description="Total number of delegation messages")
    has_delegations: bool = Field(False, description="Whether validator has any delegations")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        self.total_delegations = len(self.delegations)
        self.has_delegations = self.total_delegations > 0
        
        # Calculate active delegatees (delegations minus revocations)
        delegated = set()
        revoked = set()
        
        for delegation in self.delegations:
            if delegation.is_delegation:
                delegated.add(delegation.delegatee_pubkey)
            elif delegation.is_revocation:
                revoked.add(delegation.delegatee_pubkey)
        
        self.active_delegatees = list(delegated - revoked)
    
    @property
    def active_delegation_count(self) -> int:
        """Number of currently active delegations."""
        return len(self.active_delegatees)
    
    def is_delegated_to(self, delegatee_pubkey: str) -> bool:
        """Check if validator is currently delegated to specific delegatee."""
        # Compare pubkeys directly (both should have 0x prefix)
        return delegatee_pubkey in self.active_delegatees


class ValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(..., description="Field that failed validation")
    error: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value")


def parse_delegation_json(delegation_data: Union[str, List[Dict[str, Any]]]) -> List[SignedDelegation]:
    """
    Parse delegation JSON data into SignedDelegation objects.
    
    Args:
        delegation_data: Raw JSON string or parsed list of dictionaries
        
    Returns:
        List of validated SignedDelegation objects
        
    Raises:
        ValueError: If data is malformed or validation fails
    """
    if isinstance(delegation_data, str):
        try:
            data = json.loads(delegation_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    else:
        data = delegation_data
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of delegations, got {type(data)}")
    
    delegations = []
    errors = []
    
    for i, item in enumerate(data):
        try:
            delegation = SignedDelegation(**item)
            delegations.append(delegation)
        except Exception as e:
            errors.append(ValidationError(
                field=f"delegation[{i}]",
                error=str(e),
                value=item
            ))
    
    if errors:
        error_details = "; ".join([f"{err.field}: {err.error}" for err in errors])
        raise ValueError(f"Validation errors: {error_details}")
    
    return delegations


def create_delegation_result(validator_pubkey: str, delegations: List[SignedDelegation]) -> DelegationQueryResult:
    """
    Create a DelegationQueryResult from delegation list.
    
    Args:
        validator_pubkey: Validator public key
        delegations: List of signed delegations
        
    Returns:
        DelegationQueryResult with computed fields
    """
    # Keep validator pubkey as provided (with 0x prefix)
    
    return DelegationQueryResult(
        validator_pubkey=validator_pubkey,
        delegations=delegations
    )


# PostgreSQL Data Models

class ValidatorInfo(BaseModel):
    """Simplified validator information showing only registration status."""
    validator_pubkey: str = Field(..., description="Validator BLS public key (hex with 0x prefix)")
    is_registered: bool = Field(False, description="Whether validator is registered")