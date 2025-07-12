import hashlib, time, threading
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from solana.keypair import Keypair
from solana.rpc.api import Client as SolanaClient
from tronpy import Tron
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx
from config import *
from database import Session, User, Deposit
from logger import logger

# RPC clients
w3_eth = Web3(Web3.HTTPProvider(ETH_RPC_URL, request_kwargs={'timeout':10,'verify':True}))
w3_bnb = Web3(Web3.HTTPProvider(BNB_RPC_URL, request_kwargs={'timeout':10,'verify':True}))
sol_client = SolanaClient(SOL_RPC_URL)
xrp_client = JsonRpcClient(XRP_RPC_URL)
tron_client = Tron(full_node=TRX_RPC_URL)

# ERC-20 ABI
erc20_abi = [
  {"anonymous":False,"inputs":[{"indexed":True,"name":"from","type":"address"},
  {"indexed":True,"name":"to","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],
  "name":"Transfer","type":"event"},
  {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],
  "name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
  {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],
  "stateMutability":"view","type":"function"}
]
usdc_contract = w3_eth.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS), abi=erc20_abi)

def user_index(uid): return int.from_bytes(hashlib.sha256(uid.encode()).digest()[:4],'big')

def derive_eth_account(uid):
    return Account.from_mnemonic(MNEMONIC, account_path=f"m/44'/60'/0'/0/{user_index(uid)}")

def get_xrp_deposit_address(uid):
    return f"{XRP_SHARED_ADDRESS}?memo={user_index(uid)}"

def get_deposit_address(uid, chain):
    session=Session(); user=session.query(User).get(uid) or User(user_id=uid)
    if chain=='eth':
        user.eth_address = derive_eth_account(uid).address
    elif chain=='bnb':
        user.bnb_address = derive_eth_account(uid).address
    elif chain=='sol':
        user.sol_address = str(Keypair.from_seed(hashlib.sha256(uid.encode()).digest()[:32]).public_key)
    elif chain=='trx':
        pass  # implement TRX derivation
    elif chain=='xrp':
        addr=user.xrp_address, user.xrp_memo = get_xrp_deposit_address(uid).split('?memo=')
        session.add(user); session.commit(); return f"{addr[0]}?memo={addr[1]}"
    session.add(user); session.commit()
    return getattr(user, f"{chain}_address")
