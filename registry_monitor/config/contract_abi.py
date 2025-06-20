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