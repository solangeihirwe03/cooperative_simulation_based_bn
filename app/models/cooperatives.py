from sqlalchemy import Column, Integer, String
from app.db.database import Base
from sqlalchemy.orm import relationship

class Cooperative(Base):
    __tablename__ = "cooperatives"

    cooperative_id = Column(Integer, primary_key=True, index=True)
    cooperative_name = Column(String(256), unique=True, nullable=False)

    members = relationship("Member", back_populates="cooperative")