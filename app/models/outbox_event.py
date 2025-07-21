# app/models/outbox_event.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from app.db.session import Base

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)