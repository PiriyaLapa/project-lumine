from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    employee_code = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False)  # sales_associate | store_manager
    store_id = Column(Integer, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)  # soft-delete (PDPA)

    transactions = relationship("Transaction", back_populates="staff")
    evidence_logs = relationship("EvidenceLog", back_populates="staff")
