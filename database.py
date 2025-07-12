import os, stat
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_PATH, DB_KEY

if os.path.exists(DB_PATH):
    os.chmod(DB_PATH, stat.S_IRUSR|stat.S_IWUSR)

engine = create_engine(
    f"sqlite+pysqlcipher://:{DB_KEY}@/{DB_PATH}?cipher=aes-256-cfb&kdf_iter=64000"
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    eth_address = Column(String)
    sol_address = Column(String)
    trx_address = Column(String)
    xrp_address = Column(String)
    xrp_memo = Column(String)
    bnb_address = Column(String)

class Deposit(Base):
    __tablename__ = 'deposits'
    id        = Column(Integer, primary_key=True)
    user_id   = Column(String)
    chain     = Column(String)
    token     = Column(String)
    amount    = Column(Float)
    tx_hash   = Column(String)
    timestamp = Column(DateTime)

Base.metadata.create_all(engine)
