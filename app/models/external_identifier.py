from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class ExternalIdentifier(Base):
    __tablename__ = "external_identifiers"

    external_identifier_id = Column(Integer, primary_key=True, index=True)

    party_id = Column(
        Integer,
        ForeignKey("parties.party_id", ondelete="CASCADE"),
        nullable=False,
    )

    system_name = Column(String(100), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('party_id', 'system_name', name='uq_party_system'),
    )

    party = relationship("Party", back_populates="external_identifiers")