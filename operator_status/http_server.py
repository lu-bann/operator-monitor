"""
FastAPI HTTP server for Helix validator delegation operations.

This module provides REST API endpoints for the validator delegation
checking functionality, exposing the same operations available in the CLI.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from services import (
    ValidatorDelegationService, 
    ValidatorRegistrationService,
    OperatorValidatorService,
    create_validator_delegation_service,
    create_validator_info_service_instance,
    create_operator_service_instance
)
from api_models import (
    ValidatorDelegationResponse,
    BatchValidatorsRequest,
    BatchValidatorsResponse,
    ValidatorListResponse,
    ValidatorInfoResponse,
    OperatorValidatorsResponse,
    ErrorResponse,
    HealthCheckResponse,
    ServerConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HelixValidatorAPI:
    """Main API class that holds configuration and creates services."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize with configuration."""
        self.config = config or ServerConfig()
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="Helix Validator Delegation API",
            description="REST API for checking validator delegation submission rights in Helix MEV relay",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self._add_routes(app)
        
        # Add exception handlers
        self._add_exception_handlers(app)
        
        return app
    
    def _get_delegation_service(self) -> ValidatorDelegationService:
        """Create validator delegation service with current configuration."""
        return create_validator_delegation_service(
            redis_url=self.config.redis_url,
            timeout=self.config.redis_timeout
        )
    
    def _get_validator_info_service(self) -> ValidatorRegistrationService:
        """Create validator info service with current configuration."""
        return create_validator_info_service_instance(
            postgres_host=self.config.postgres_host,
            postgres_port=self.config.postgres_port,
            postgres_db=self.config.postgres_db,
            postgres_user=self.config.postgres_user,
            postgres_password=self.config.postgres_password
        )
    
    def _get_operator_service(self) -> OperatorValidatorService:
        """Create operator validator service with current configuration."""
        return create_operator_service_instance(
            redis_url=self.config.redis_url,
            timeout=self.config.redis_timeout,
            key_prefix=self.config.redis_key_prefix
        )

    
    def _add_exception_handlers(self, app: FastAPI):
        """Add exception handlers to the app."""
        
        @app.exception_handler(ValidationError)
        async def validation_exception_handler(request, exc: ValidationError):
            """Handle Pydantic validation errors."""
            details = []
            for error in exc.errors():
                details.append({
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "code": error["type"]
                })
            
            error_response = ErrorResponse.validation_error(
                message="Request validation failed",
                details=details
            )
            return JSONResponse(
                status_code=422,
                content=error_response.dict()
            )

        @app.exception_handler(ValueError)
        async def value_error_handler(request, exc: ValueError):
            """Handle value errors from services."""
            error_response = ErrorResponse.validation_error(message=str(exc))
            return JSONResponse(
                status_code=400,
                content=error_response.dict()
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc: Exception):
            """Handle general exceptions."""
            logger.error(f"Unhandled exception in {request.url}: {exc}")
            error_response = ErrorResponse.service_error(
                message="Internal server error occurred"
            )
            return JSONResponse(
                status_code=500,
                content=error_response.dict()
            )

    
    def _add_routes(self, app: FastAPI):
        """Add API routes to the app."""

        @app.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """Health check endpoint."""
            try:
                # Test Redis connection
                redis_status = "healthy"
                try:
                    delegation_service = self._get_delegation_service()
                    # Try to connect to Redis by calling a simple operation
                    delegation_service._get_parser()
                except Exception as e:
                    redis_status = f"unhealthy: {str(e)}"
                
                # Test PostgreSQL connection
                postgres_status = "healthy"
                try:
                    info_service = self._get_validator_info_service()
                    # Try to connect to PostgreSQL
                    info_service._get_service()
                    info_service.disconnect()
                except Exception as e:
                    postgres_status = f"unhealthy: {str(e)}"
                
                overall_status = "healthy" if redis_status == "healthy" and postgres_status == "healthy" else "unhealthy"
                
                return HealthCheckResponse(
                    status=overall_status,
                    services={
                        "redis": redis_status,
                        "postgresql": postgres_status
                    },
                    timestamp=datetime.utcnow().isoformat(),
                    version="1.0.0"
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return HealthCheckResponse(
                    status="unhealthy",
                    services={"error": str(e)},
                    timestamp=datetime.utcnow().isoformat(),
                    version="1.0.0"
                )

        from fastapi import Query
        
        @app.get("/validator-delegation/{validator_key}", response_model=ValidatorDelegationResponse)
        async def get_validator_delegation(
            validator_key: str = Path(..., description="Validator public key (hex, with or without 0x prefix)"),
            details: bool = Query(False, description="Include detailed delegation messages")
        ):
            """
            Get delegation status for a single validator.
            
            This endpoint checks the delegation status of a validator by querying
            Redis for delegation messages and calculating active delegations.
            """
            try:
                delegation_service = self._get_delegation_service()
                result = delegation_service.get_validator_delegation_status(validator_key)
                return ValidatorDelegationResponse.from_delegation_result(result, include_details=details)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting validator delegation for {validator_key}: {e}")
                raise HTTPException(status_code=500, detail="Failed to query delegation status")


        
        @app.post("/batch", response_model=BatchValidatorsResponse)
        async def batch_validator_delegations(request: BatchValidatorsRequest):
            """
            Check delegation status for multiple validators.
            
            This endpoint accepts a list of validator public keys and returns
            delegation status for each, along with summary statistics.
            """
            try:
                delegation_service = self._get_delegation_service()
                batch_result = delegation_service.check_validators_batch(request.validator_keys)
                return BatchValidatorsResponse.from_batch_result(batch_result)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error in batch validator check: {e}")
                raise HTTPException(status_code=500, detail="Failed to process batch request")

        @app.get("/list-validators", response_model=ValidatorListResponse)
        async def list_validators():
            """
            List all validators with delegation data in Redis.
            
            This endpoint scans Redis for all validators that have delegation
            messages stored and returns their public keys.
            """
            try:
                delegation_service = self._get_delegation_service()
                validators = delegation_service.list_validators_with_delegations()
                return ValidatorListResponse.from_validator_list(validators)
            except Exception as e:
                logger.error(f"Error listing validators: {e}")
                raise HTTPException(status_code=500, detail="Failed to list validators")

        @app.get("/validator-info/{validator_key}", response_model=ValidatorInfoResponse)
        async def get_validator_info(
            validator_key: str = Path(..., description="Validator public key (hex with 0x prefix)")
        ):
            """
            Get validator registration information from PostgreSQL database.
            
            This endpoint queries the PostgreSQL database to check if a validator
            is registered in the Helix MEV relay system.
            """
            info_service = None
            try:
                info_service = self._get_validator_info_service()
                info = info_service.get_validator_info(validator_key)
                return ValidatorInfoResponse.from_validator_info(info)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting validator info for {validator_key}: {e}")
                raise HTTPException(status_code=500, detail="Failed to query validator information")
            finally:
                # Clean up database connection
                if info_service:
                    try:
                        info_service.disconnect()
                    except:
                        pass

        @app.get("/operator/{operator_address}", response_model=OperatorValidatorsResponse)
        async def get_operator_validators(
            operator_address: str = Path(..., description="Operator Ethereum address (hex with 0x prefix)")
        ):
            """
            Get validators registered to a specific operator.
            
            This endpoint queries Redis for validator mappings stored by the
            operator_monitor system based on OperatorRegistered events.
            """
            operator_service = None
            try:
                operator_service = self._get_operator_service()
                validators = operator_service.get_operator_validators(operator_address)
                return OperatorValidatorsResponse.from_validator_list(operator_address, validators)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except ConnectionError as e:
                logger.error(f"Redis connection error for operator {operator_address}: {e}")
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
            except Exception as e:
                logger.error(f"Error getting validators for operator {operator_address}: {e}")
                raise HTTPException(status_code=500, detail="Failed to query operator validators")
            finally:
                # Clean up Redis connection
                if operator_service:
                    try:
                        operator_service.disconnect()
                    except:
                        pass

        @app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "service": "Helix Validator Delegation API",
                "version": "1.0.0",
                "description": "REST API for checking validator delegation submission rights in Helix MEV relay",
                "endpoints": {
                    "health": "/health",
                    "validator_delegation": "/validator-delegation/{validator_key}",
                    "batch_check": "/batch",
                    "list_validators": "/list-validators",
                    "validator_info": "/validator-info/{validator_key}",
                    "operator_validators": "/operator/{operator_address}",
                    "documentation": "/docs",
                    "redoc": "/redoc"
                }
            }


# Global API instance for Uvicorn (will be created with default config)
api_instance = HelixValidatorAPI()
app = api_instance.app


# Application factory for production deployment
def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """
    Create FastAPI application with configuration.
    
    Args:
        config: Server configuration
        
    Returns:
        Configured FastAPI application
    """
    api = HelixValidatorAPI(config)
    return api.app


if __name__ == "__main__":
    # This block is for development only
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )