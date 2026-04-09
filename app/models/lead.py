from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class PendingLead(Base):
    __tablename__ = "pending_leads"

    id = Column(Integer, primary_key=True, index=True)
    name_encrypted = Column(String, nullable=False)
    phone_encrypted = Column(String, nullable=False)
    comment_encrypted = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    attempts = Column(Integer, default=0)
    max_sent = Column(Boolean, default=False)
    amocrm_sent = Column(Boolean, default=False)
    next_retry_at = Column(DateTime, default=datetime.utcnow)
