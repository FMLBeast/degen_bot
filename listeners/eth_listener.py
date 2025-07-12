import time
from crypto_wallet import w3_eth, record_deposit
from database import Session, User
from logger import logger

def run(poll_interval=10):
    session=Session()
    last_block=w3_eth.eth.block_number
    while True:
        try:
            users=session.query(User).filter(User.eth_address!=None).all()
            addrs={u.eth_address:u.user_id for u in users}
            latest=w3_eth.eth.block_number
            for blk in range(last_block+1, latest+1):
                block=w3_eth.eth.get_block(blk, full_transactions=True)
                for tx in block.transactions:
                    if tx.to in addrs:
                        amt=w3_eth.from_wei(tx.value,'ether')
                        record_deposit(addds[tx.to],'eth','eth',float(amt),tx.hash.hex())
            last_block=latest
        except Exception as e:
            logger.error(f"ETH listener error: {e}")
        time.sleep(poll_interval)
