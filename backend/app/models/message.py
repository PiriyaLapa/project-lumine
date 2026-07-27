from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(ForeignKey("customers.customer_id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("follow_up_tasks.id"), nullable=True, index=True)
    touchpoint_type = Column(String(5), nullable=True)  # 2D | 2W | 2M
    message_text = Column(Text, nullable=False)
    channel_line = Column(Boolean, nullable=False, default=False)
    channel_email = Column(Boolean, nullable=False, default=False)
    status_line = Column(String(20), nullable=True)  # sent | failed | not_available
    status_email = Column(String(20), nullable=True)  # sent | failed | not_available
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="messages")
    staff = relationship("Staff")
    follow_up_task = relationship("FollowUpTask")
