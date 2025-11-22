from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .config import Base

# Table des villes/localisations
class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Une ville est unique par combinaison ville+pays
    __table_args__ = (UniqueConstraint('city', 'country', name='unique_city_country'),)
    
    # Relation : une ville a plusieurs mesures
    measurements = relationship("Measurement", back_populates="location")

# Table des mesures de pollution
class Measurement(Base):
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    parameter = Column(String, nullable=False)  # pm25, pm10, no2, etc.
    value = Column(Float, nullable=False)
    unit = Column(String)
    measurement_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation inverse : chaque mesure appartient à une ville
    location = relationship("Location", back_populates="measurements")
