from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)  # PII — never log
    email = Column(String(255), nullable=True)  # PII — never log
    line_id = Column(String(100), nullable=True)
    language = Column(String(5), nullable=False, default="th")  # th | en
    language_source = Column(
        String(20), nullable=False, default="auto_detected"
    )  # auto_detected | manual_override
    do_not_contact = Column(Boolean, nullable=False, default=False)
    source = Column(
        String(30), nullable=False, default="crm_import"
    )  # crm_import | manual_registration | sap_only
    staff_id = Column(ForeignKey("staff.id"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    staff = relationship("Staff")
    messages = relationship("Message", back_populates="customer")
