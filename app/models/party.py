from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Party(Base):
    __tablename__ = "parties"

    party_id = Column(Integer, primary_key=True, index=True)
    party_type = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person = relationship("Person", uselist=False, back_populates="party")
    organisation = relationship("Organisation", uselist=False, back_populates="party")
    addresses = relationship(
        "Address",
        secondary="party_addresses",
        back_populates="parties"
    )
    external_identifiers = relationship(
          "ExternalIdentifier",
          cascade="all, delete-orphan",
          passive_deletes=True,
    )
    relationships_from = relationship(
        "PartyRelationship",
        foreign_keys="[PartyRelationship.from_party_id]",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="from_party"
    )
    relationships_to = relationship(
        "PartyRelationship",
        foreign_keys="[PartyRelationship.to_party_id]",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="to_party"
    )