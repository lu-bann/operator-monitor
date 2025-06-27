"""Network configuration definitions"""

NETWORK_CONFIGS = {
    'mainnet': {
        'name': 'Ethereum Mainnet',
        'chain_id': 1,
        'default_rpc': 'https://eth.llamarpc.com',
        'block_explorer': 'https://etherscan.io'
    },
    'holesky': {
        'name': 'Holesky Testnet',
        'chain_id': 17000,
        'default_rpc': 'https://ethereum-holesky.publicnode.com',
        'block_explorer': 'https://holesky.etherscan.io'
    },
    'hoodi': {
        'name': 'Hoodi Testnet',
        'chain_id': 560048,
        'default_rpc': 'https://ethereum-hoodi-rpc.publicnode.com',
        'block_explorer': 'https://hoodi.etherscan.io'
    },
    'devnet': {
        'name': 'Local Devnet',
        'chain_id': 1337,
        'default_rpc': 'http://localhost:8545',
        'block_explorer': 'https://localhost:8545'
    }
} 