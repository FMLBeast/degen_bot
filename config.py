import os, keyring

MNEMONIC = keyring.get_password(*os.getenv('MNEMONIC_KEY').split(':'))
DB_KEY   = keyring.get_password(*os.getenv('DB_KEY').split(':'))
HOUSE_WALLET = keyring.get_password(*os.getenv('HOUSE_WALLET_KEY').split(':'))

ETH_RPC_URL = os.getenv('ETH_RPC_URL')
SOL_RPC_URL = os.getenv('SOL_RPC_URL')
TRX_RPC_URL = os.getenv('TRX_RPC_URL')
XRP_RPC_URL = os.getenv('XRP_RPC_URL')
BNB_RPC_URL = os.getenv('BNB_RPC_URL')

USDC_CONTRACT_ADDRESS = os.getenv('USDC_CONTRACT_ADDRESS')
XRP_SHARED_ADDRESS = os.getenv('XRP_SHARED_ADDRESS')

HOUSE_FEE = float(os.getenv('HOUSE_FEE_PERCENT', '5'))/100

DB_PATH  = os.getenv('DB_PATH')
LOG_PATH = os.getenv('LOG_PATH')
LOG_LEVEL= os.getenv('LOG_LEVEL','INFO')
