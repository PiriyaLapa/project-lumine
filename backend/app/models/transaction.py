from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    idoc_number = Column(String(100), primary_key=True, index=True)
    posting_date = Column(Date, nullable=False, index=True)
    ean = Column(String(50), nullable=True)
    material_desc = Column(String(500), nullable=True)
    customer_id = Column(String(100), nullable=False, index=True)  # SAP code — no name stored (PDPA)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    staff = relationship("Staff", back_populates="transactions")
    follow_up_tasks = relationship("FollowUpTask", back_populates="transaction")
