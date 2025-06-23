"""Registry contract ABI definitions"""

REGISTRY_CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": False, "name": "collateralWei", "type": "uint256"},
            {"indexed": False, "name": "owner", "type": "address"}
        ],
        "name": "OperatorRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "slashingType", "type": "uint8"},
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": False, "name": "owner", "type": "address"},
            {"indexed": False, "name": "challenger", "type": "address"},
            {"indexed": True, "name": "slasher", "type": "address"},
            {"indexed": False, "name": "slashAmountWei", "type": "uint256"}
        ],
        "name": "OperatorSlashed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"}
        ],
        "name": "OperatorUnregistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": False, "name": "collateralWei", "type": "uint256"}
        ],
        "name": "CollateralClaimed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": False, "name": "collateralWei", "type": "uint256"}
        ],
        "name": "CollateralAdded",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": True, "name": "slasher", "type": "address"},
            {"indexed": True, "name": "committer", "type": "address"}
        ],
        "name": "OperatorOptedIn",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": True, "name": "slasher", "type": "address"}
        ],
        "name": "OperatorOptedOut",
        "type": "event"
    }
]

# TaiyiRegistryCoordinator ABI
TAIYI_REGISTRY_COORDINATOR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "operatorId", "type": "bytes32"},
            {"indexed": False, "name": "linglongSubsetIds", "type": "uint32[]"}
        ],
        "name": "OperatorRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "operatorId", "type": "bytes32"},
            {"indexed": False, "name": "linglongSubsetIds", "type": "uint32[]"}
        ],
        "name": "OperatorDeregistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": False, "name": "previousStatus", "type": "uint8"},
            {"indexed": False, "name": "newStatus", "type": "uint8"}
        ],
        "name": "OperatorStatusChanged",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "linglongSubsetId", "type": "uint32"},
            {"indexed": False, "name": "minStake", "type": "uint256"}
        ],
        "name": "LinglongSubsetCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "linglongSubsetId", "type": "uint32"}
        ],
        "name": "OperatorAddedToSubset",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "linglongSubsetId", "type": "uint32"}
        ],
        "name": "OperatorRemovedFromSubset",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "oldRegistry", "type": "address"},
            {"indexed": True, "name": "newRegistry", "type": "address"}
        ],
        "name": "SocketRegistryUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "oldRegistry", "type": "address"},
            {"indexed": True, "name": "newRegistry", "type": "address"}
        ],
        "name": "PubkeyRegistryUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operatorId", "type": "bytes32"},
            {"indexed": False, "name": "socket", "type": "string"}
        ],
        "name": "OperatorSocketUpdate",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "restakingProtocol", "type": "uint8"},
            {"indexed": False, "name": "newMiddleware", "type": "address"}
        ],
        "name": "RestakingMiddlewareUpdated",
        "type": "event"
    }
]

# TaiyiEscrow ABI
TAIYI_ESCROW_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "Deposited",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "Withdrawn",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "isAfterExec", "type": "bool"}
        ],
        "name": "PaymentMade",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "RequestedWithdraw",
        "type": "event"
    }
]

# TaiyiCore ABI
TAIYI_CORE_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "preconfer", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "Exhausted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "preconfRequestHash", "type": "bytes32"}
        ],
        "name": "TipCollected",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "preconfRequestHash", "type": "bytes32"},
            {"indexed": False, "name": "tipAmount", "type": "uint256"}
        ],
        "name": "PreconfRequestExecuted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "preconfRequestHash", "type": "bytes32"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "TipReceived",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "recipient", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "EthSponsored",
        "type": "event"
    }
]

# EigenLayerMiddleware ABI
EIGENLAYER_MIDDLEWARE_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "rewardsHandler", "type": "address"}
        ],
        "name": "RewardsHandlerSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "oldInitiator", "type": "address"},
            {"indexed": True, "name": "newInitiator", "type": "address"}
        ],
        "name": "RewardsInitiatorSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"}
        ],
        "name": "ValidatorsRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"}
        ],
        "name": "ValidatorsUnregistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": False, "name": "count", "type": "uint256"}
        ],
        "name": "DelegationsBatchSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
            {"indexed": True, "name": "delegatee", "type": "address"}
        ],
        "name": "SlasherOptedIn",
        "type": "event"
    }
] 