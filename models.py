"""
Database models for the Minyan Finder API.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

Base = declarative_base()


class Broadcast(Base):
    """Model representing a minyan broadcast."""
    
    __tablename__ = 'broadcasts'
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    minyan_type = Column(String(20), nullable=False)
    earliest_time = Column(DateTime, nullable=False)
    latest_time = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert broadcast to dictionary format."""
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'minyanType': self.minyan_type,
            'earliestTime': self.earliest_time.isoformat() + 'Z' if self.earliest_time else None,
            'latestTime': self.latest_time.isoformat() + 'Z' if self.latest_time else None,
            'active': self.active,
            'createdAt': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


# Database initialization is now handled in app.py

