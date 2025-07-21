from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class Address(Base):
    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    address_line_1 = Column(String(100), nullable=False)
    address_line_2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    region = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    address_type = Column(String(20), nullable=False)

    parties = relationship(
        "Party",
        secondary="party_addresses",
        back_populates="addresses"
    )