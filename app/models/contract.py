from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    contract_type = Column(String(100), nullable=False)
    language = Column(String(50), default="English")
    content = Column(Text, nullable=False)

    user = relationship("User", back_populates="contracts")
