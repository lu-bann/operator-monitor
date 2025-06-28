"""
API models for HTTP request/response schemas.

These models define the structure for HTTP API requests and responses,
separate from the internal data models used by the business logic.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from models import DelegationQueryResult, ValidatorInfo, SignedDelegation


# Request Models

class ValidatorKeyRequest(BaseModel):
    """Request model for single validator operations."""
    validator_key: str = Field(..., description="Validator public key (hex, with or without 0x prefix)")
    details: bool = Field(False, description="Include detailed delegation messages")


class BatchValidatorsRequest(BaseModel):
    """Request model for batch validator operations."""
    validator_keys: List[str] = Field(..., description="List of validator public keys")
    
    @validator('validator_keys')
    def validate_non_empty(cls, v):
        if not v:
            raise ValueError("validator_keys cannot be empty")
        return v


class PostgresConfigRequest(BaseModel):
    """Request model for PostgreSQL configuration."""
    postgres_host: str = Field("localhost", description="PostgreSQL hostname")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_db: str = Field("helix_mev_relayer", description="PostgreSQL database name")
    postgres_user: str = Field("postgres", description="PostgreSQL user")
    postgres_password: str = Field("postgres", description="PostgreSQL password")


# Response Models

class DelegationDetailResponse(BaseModel):
    """Response model for individual delegation details."""
    action: str = Field(..., description="Action type: delegate or revoke")
    delegatee: str = Field(..., description="Delegatee public key")
    signature: str = Field(..., description="BLS signature (hex)")


class ValidatorDelegationResponse(BaseModel):
    """Response model for validator delegation status."""
    validator_pubkey: str = Field(..., description="Validator public key")
    has_delegations: bool = Field(..., description="Whether validator has any delegations")
    total_delegations: int = Field(..., description="Total number of delegation messages")
    active_delegations: int = Field(..., description="Number of active delegations")
    active_delegatees: List[str] = Field(..., description="List of active delegatee public keys")
    delegations: List[DelegationDetailResponse] = Field(default_factory=list, description="Detailed delegation messages")
    
    @classmethod
    def from_delegation_result(cls, result: DelegationQueryResult, include_details: bool = False) -> "ValidatorDelegationResponse":
        """Create response from DelegationQueryResult."""
        delegations = []
        if include_details:
            for delegation in result.delegations:
                delegations.append(DelegationDetailResponse(
                    action=delegation.message.action_name,
                    delegatee=delegation.delegatee_pubkey,
                    signature=f"0x{delegation.signature}"
                ))
        
        return cls(
            validator_pubkey=result.validator_pubkey,
            has_delegations=result.has_delegations,
            total_delegations=result.total_delegations,
            active_delegations=result.active_delegation_count,
            active_delegatees=result.active_delegatees,
            delegations=delegations
        )


class BatchSummaryResponse(BaseModel):
    """Response model for batch operation summary."""
    total_validators: int = Field(..., description="Total number of validators processed")
    validators_with_delegations: int = Field(..., description="Number of validators with delegations")
    total_active_delegations: int = Field(..., description="Total number of active delegations")


class ValidatorBatchResultResponse(BaseModel):
    """Response model for individual validator in batch results."""
    validator_pubkey: str = Field(..., description="Validator public key")
    has_delegations: bool = Field(..., description="Whether validator has any delegations")
    active_delegations: int = Field(..., description="Number of active delegations")
    active_delegatees: List[str] = Field(..., description="List of active delegatee public keys")
    
    @classmethod
    def from_delegation_result(cls, result: DelegationQueryResult) -> "ValidatorBatchResultResponse":
        """Create response from DelegationQueryResult."""
        return cls(
            validator_pubkey=result.validator_pubkey,
            has_delegations=result.has_delegations,
            active_delegations=result.active_delegation_count,
            active_delegatees=result.active_delegatees
        )


class BatchValidatorsResponse(BaseModel):
    """Response model for batch validator operations."""
    summary: BatchSummaryResponse = Field(..., description="Summary statistics")
    results: List[ValidatorBatchResultResponse] = Field(..., description="Individual validator results")
    
    @classmethod
    def from_batch_result(cls, batch_data: Dict[str, Any]) -> "BatchValidatorsResponse":
        """Create response from batch service result."""
        summary = BatchSummaryResponse(**batch_data["summary"])
        
        results = []
        for result in batch_data["results"]:
            results.append(ValidatorBatchResultResponse.from_delegation_result(result))
        
        return cls(summary=summary, results=results)


class ValidatorListResponse(BaseModel):
    """Response model for validator list operations."""
    validators: List[str] = Field(..., description="List of validator public keys with delegation data")
    count: int = Field(..., description="Total number of validators")
    
    @classmethod
    def from_validator_list(cls, validators: List[str]) -> "ValidatorListResponse":
        """Create response from validator list."""
        return cls(validators=validators, count=len(validators))


class ValidatorInfoResponse(BaseModel):
    """Response model for validator registration information."""
    validator_pubkey: str = Field(..., description="Validator public key")
    is_registered: bool = Field(..., description="Whether validator is registered in the database")
    
    @classmethod
    def from_validator_info(cls, info: ValidatorInfo) -> "ValidatorInfoResponse":
        """Create response from ValidatorInfo."""
        return cls(
            validator_pubkey=info.validator_pubkey,
            is_registered=info.is_registered
        )


class OperatorValidatorsResponse(BaseModel):
    """Response model for operator validator mappings."""
    operator_address: str = Field(..., description="Operator Ethereum address")
    validator_count: int = Field(..., description="Number of validators registered to this operator")
    validators: List[str] = Field(..., description="List of validator public keys")
    
    @classmethod
    def from_validator_list(cls, operator_address: str, validators: List[str]) -> "OperatorValidatorsResponse":
        """Create response from operator address and validator list."""
        return cls(
            operator_address=operator_address,
            validator_count=len(validators),
            validators=validators
        )


# Error Models

class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")
    
    @classmethod
    def validation_error(cls, message: str, details: Optional[List[ErrorDetail]] = None) -> "ErrorResponse":
        """Create validation error response."""
        return cls(error="validation_error", message=message, details=details)
    
    @classmethod
    def service_error(cls, message: str) -> "ErrorResponse":
        """Create service error response."""
        return cls(error="service_error", message=message)
    
    @classmethod
    def not_found_error(cls, message: str) -> "ErrorResponse":
        """Create not found error response."""
        return cls(error="not_found", message=message)


# Configuration Models

class ServerConfig(BaseModel):
    """Server configuration model."""
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")
    redis_timeout: int = Field(5, description="Redis connection timeout in seconds")
    redis_key_prefix: str = Field("validators_by_operator", description="Redis key prefix for operator-validator mappings")
    postgres_host: str = Field("localhost", description="PostgreSQL hostname")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_db: str = Field("helix_mev_relayer", description="PostgreSQL database name")
    postgres_user: str = Field("postgres", description="PostgreSQL user")
    postgres_password: str = Field("postgres", description="PostgreSQL password")


# Health Check Models

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status: healthy, unhealthy")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    timestamp: str = Field(..., description="Timestamp of health check")
    version: str = Field("1.0.0", description="API version")