"""
Geospatial models for location data and path planning
"""

from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

db = SQLAlchemy()

class GeoLocation(db.Model):
    """Geospatial location data for various entities"""
    __tablename__ = 'geo_locations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Location details
    name = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    location_type = db.Column(db.String(50), nullable=False)  # issue, landmark, hazard, safe_zone
    
    # Geospatial data
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    
    # Additional geospatial properties
    elevation = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)  # GPS accuracy in meters
    
    # Risk and safety data
    risk_level = db.Column(db.String(20), default='unknown')
    safety_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    traffic_density = db.Column(db.String(20), nullable=True)  # low, medium, high
    
    # Metadata
    source = db.Column(db.String(50), nullable=True)  # user_report, 311_data, scraped, calculated
    verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert location to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'location_type': self.location_type,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'elevation': self.elevation,
            'accuracy': self.accuracy,
            'risk_level': self.risk_level,
            'safety_score': self.safety_score,
            'traffic_density': self.traffic_density,
            'source': self.source,
            'verified': self.verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<GeoLocation {self.name} at ({self.latitude}, {self.longitude})>'

class PathPlan(db.Model):
    """Safe path planning routes avoiding infrastructure issues"""
    __tablename__ = 'path_plans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Route details
    name = db.Column(db.String(255), nullable=True)
    route_type = db.Column(db.String(50), nullable=False)  # driving, walking, cycling, emergency
    
    # Start and end points
    start_longitude = db.Column(db.Float, nullable=False)
    start_latitude = db.Column(db.Float, nullable=False)
    start_location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    start_address = db.Column(db.String(255), nullable=True)
    
    end_longitude = db.Column(db.Float, nullable=False)
    end_latitude = db.Column(db.Float, nullable=False)
    end_location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    end_address = db.Column(db.String(255), nullable=True)
    
    # Route geometry and metrics
    route_geometry = db.Column(Geometry('LINESTRING', srid=4326), nullable=True)
    route_points = db.Column(db.JSON, nullable=True)  # Array of [lat, lng] coordinates
    
    # Route metrics
    distance_km = db.Column(db.Float, nullable=True)
    estimated_duration_minutes = db.Column(db.Integer, nullable=True)
    safety_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    
    # Hazards and considerations
    avoided_hazards = db.Column(db.JSON, nullable=True)  # List of hazard IDs avoided
    risk_areas_count = db.Column(db.Integer, default=0)
    
    # Algorithm details
    algorithm_used = db.Column(db.String(50), nullable=True)  # dijkstra, a_star, custom
    weights_config = db.Column(db.JSON, nullable=True)  # Algorithm parameters
    
    # Status and usage
    status = db.Column(db.String(20), default='active')  # active, outdated, deprecated
    usage_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_geometry=False):
        """Convert path plan to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'route_type': self.route_type,
            'start_longitude': self.start_longitude,
            'start_latitude': self.start_latitude,
            'start_address': self.start_address,
            'end_longitude': self.end_longitude,
            'end_latitude': self.end_latitude,
            'end_address': self.end_address,
            'distance_km': self.distance_km,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'safety_score': self.safety_score,
            'avoided_hazards': self.avoided_hazards,
            'risk_areas_count': self.risk_areas_count,
            'algorithm_used': self.algorithm_used,
            'weights_config': self.weights_config,
            'status': self.status,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_geometry:
            data['route_points'] = self.route_points
            
        return data
    
    def __repr__(self):
        return f'<PathPlan {self.route_type} from ({self.start_latitude}, {self.start_longitude}) to ({self.end_latitude}, {self.end_longitude})>'