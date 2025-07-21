from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class PartyRelationship(Base):
    __tablename__ = "party_relationships"

    relationship_id = Column(Integer, primary_key=True, index=True)
    from_party_id = Column(Integer, ForeignKey("parties.party_id"), nullable=False)
    to_party_id = Column(Integer, ForeignKey("parties.party_id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(String(250), nullable=True)

    from_party = relationship("Party", foreign_keys=[from_party_id], back_populates="relationships_from")
    to_party = relationship("Party", foreign_keys=[to_party_id], back_populates="relationships_to")