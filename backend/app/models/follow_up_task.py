from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    idoc_number = Column(String(100), ForeignKey("transactions.idoc_number"), nullable=False)
    task_type = Column(String(10), nullable=False)   # 2D | 2W | 2M
    task_basis = Column(String(20), nullable=False, default="posting_date")  # posting_date | manual_override
    due_date = Column(Date, nullable=False)
    calculated_from = Column(Date, nullable=False)   # the posting_date used
    status = Column(String(20), nullable=False, default="Pending")  # Pending | Done | Superseded
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    transaction = relationship("Transaction", back_populates="follow_up_tasks")
    evidence_logs = relationship("EvidenceLog", back_populates="follow_up_task")
