from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Organisation(Base):
    __tablename__ = "organisations"

    party_id = Column(Integer, ForeignKey("parties.party_id"), primary_key=True)
    organisation_name = Column(String(100), nullable=False)
    organisation_type = Column(String(50), nullable=False)
    registration_number = Column(String(50), nullable=True)
    email = Column(String(100), nullable=False)
    phone_primary = Column(String(20), nullable=False)
    phone_secondary = Column(String(20), nullable=True)

    party = relationship("Party", back_populates="organisation")