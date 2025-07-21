from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Person(Base):
    __tablename__ = "persons"

    party_id = Column(Integer, ForeignKey("parties.party_id"), primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    phone_primary = Column(String(20), nullable=False)
    phone_secondary = Column(String(20), nullable=True)

    party = relationship("Party", back_populates="person")