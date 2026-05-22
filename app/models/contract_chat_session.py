from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ContractChatSession(Base):
    __tablename__ = "contract_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String, default="collecting_info", nullable=False)

    detected_contract_type = Column(String, nullable=True)

    conversation = Column(JSON, default=list, nullable=False)

    collected_data = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user = relationship("User")
