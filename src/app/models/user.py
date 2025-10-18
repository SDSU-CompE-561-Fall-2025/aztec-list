from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # need to update to use UUID or some hash of user id (but integer works for now)
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column()
    is_verified = Column(Boolean, default=False)

    profiles = relationship("Profile", back_populates="user")
    listings = relationship("Listing", back_populates="user")
