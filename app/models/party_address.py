from sqlalchemy import Column, Integer, ForeignKey
from app.db.session import Base

class PartyAddress(Base):
    __tablename__ = "party_addresses"

    party_id = Column(Integer, ForeignKey("parties.party_id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), primary_key=True)