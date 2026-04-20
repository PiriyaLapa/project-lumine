from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("follow_up_tasks.id"), nullable=False, index=True)
    notes = Column(String(2000), nullable=True)
    image_uri = Column(String(500), nullable=True)   # null if Drive upload failed
    image_size_kb = Column(Integer, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)

    follow_up_task = relationship("FollowUpTask", back_populates="evidence_logs")
    staff = relationship("Staff", back_populates="evidence_logs")
