from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    row_count = Column(Integer, nullable=False)
    tasks_created = Column(Integer, nullable=False)
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # success | error

    store = relationship("Store")
    staff = relationship("Staff")
