from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.database import Base


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True, nullable=False)
    contract_hash = Column(String, index=True, nullable=False)
    contract_id = Column(Integer, nullable=True)
    block_number = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # embed, verify-file, verify-hash
    status = Column(String, nullable=False)  # success, failed
    signers = Column(JSON, default=[])
    extra_metadata = Column(JSON, default={})  # ← fixed here!!!
    timestamp = Column(DateTime, default=datetime.utcnow)
