from sqlalchemy import Column, Integer, Float, String, DateTime, Enum
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class Scenario(Base):
    __tablename__ = "scenarios"

    scenario_id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, nullable=False)
    scenario_name = Column(String(255), nullable=False)
    scenario_description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    policy = relationship("Policy", back_populates="scenarios")