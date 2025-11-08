"""
Infrastructure issue models based on Boston 311 data
"""

from database import db
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

class InfrastructureIssue(db.Model):
    """Infrastructure issue model based on Boston 311 data structure"""
    __tablename__ = 'infrastructure_issues'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(50), unique=True, nullable=True)  # Original case ID if imported
    unique_key = db.Column(db.String(50), unique=True, nullable=True)  # NYC DOT Unique Key
    
    # Issue details
    case_topic = db.Column(db.String(100), nullable=False)  # e.g., "Street Light Outage", "Pothole"
    service_name = db.Column(db.String(100), nullable=True)  # Made nullable for DOT data
    complaint_type = db.Column(db.String(100), nullable=True)  # NYC DOT Complaint Type
    descriptor = db.Column(db.String(100), nullable=True)  # NYC DOT Descriptor (e.g., "Pothole")
    description = db.Column(db.Text, nullable=True)
    case_status = db.Column(db.String(50), default='Open')  # Open, In Progress, Closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Agency information
    agency = db.Column(db.String(50), nullable=True)  # e.g., "DOT"
    agency_name = db.Column(db.String(100), nullable=True)  # e.g., "Department of Transportation"
    
    # Resolution information
    resolution_description = db.Column(db.Text, nullable=True)
    resolution_action_updated_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    
    # Location data
    full_address = db.Column(db.String(255), nullable=True)
    incident_address = db.Column(db.String(255), nullable=True)  # NYC DOT Incident Address
    street_number = db.Column(db.String(20), nullable=True)
    street_name = db.Column(db.String(100), nullable=True)
    cross_street_1 = db.Column(db.String(100), nullable=True)  # NYC DOT Cross Street 1
    cross_street_2 = db.Column(db.String(100), nullable=True)  # NYC DOT Cross Street 2
    intersection_street_1 = db.Column(db.String(100), nullable=True)  # NYC DOT Intersection Street 1
    intersection_street_2 = db.Column(db.String(100), nullable=True)  # NYC DOT Intersection Street 2
    zip_code = db.Column(db.String(10), nullable=True)
    incident_zip = db.Column(db.String(10), nullable=True)  # NYC DOT Incident Zip
    neighborhood = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)  # NYC DOT City
    borough = db.Column(db.String(50), nullable=True)  # NYC DOT Borough
    community_board = db.Column(db.String(50), nullable=True)  # NYC DOT Community Board
    address_type = db.Column(db.String(50), nullable=True)  # NYC DOT Address Type (BLOCKFACE, INTERSECTION, etc.)
    location_type = db.Column(db.String(50), nullable=True)  # NYC DOT Location Type
    landmark = db.Column(db.String(255), nullable=True)  # NYC DOT Landmark
    facility_type = db.Column(db.String(100), nullable=True)  # NYC DOT Facility Type
    
    # Geospatial data
    longitude = db.Column(db.Float, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    # location = db.Column(Geometry('POINT', srid=4326), nullable=True)  # Commented out until PostGIS is enabled
    x_coordinate_state_plane = db.Column(db.String(50), nullable=True)  # NYC DOT X Coordinate
    y_coordinate_state_plane = db.Column(db.String(50), nullable=True)  # NYC DOT Y Coordinate
    bbl = db.Column(db.String(50), nullable=True)  # NYC DOT BBL (Borough, Block, Lot)
    
    # AI Analysis results
    risk_level = db.Column(db.String(20), default='unknown')  # low, medium, high, critical
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    detected_objects = db.Column(db.JSON, nullable=True)  # CV detection results
    
    # Timestamps
    open_date = db.Column(db.DateTime, default=datetime.utcnow)
    close_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    photos = db.relationship('IssuePhoto', backref='issue', lazy='dynamic', cascade='all, delete-orphan')
    risk_assessments = db.relationship('RiskAssessment', backref='issue', lazy='dynamic')
    
    def to_dict(self, include_photos=False):
        """Convert issue to dictionary"""
        data = {
            'id': self.id,
            'case_id': self.case_id,
            'unique_key': self.unique_key,
            'case_topic': self.case_topic,
            'service_name': self.service_name,
            'complaint_type': self.complaint_type,
            'descriptor': self.descriptor,
            'description': self.description,
            'case_status': self.case_status,
            'priority': self.priority,
            'agency': self.agency,
            'agency_name': self.agency_name,
            'resolution_description': self.resolution_description,
            'resolution_action_updated_date': self.resolution_action_updated_date.isoformat() if self.resolution_action_updated_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'full_address': self.full_address,
            'incident_address': self.incident_address,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'cross_street_1': self.cross_street_1,
            'cross_street_2': self.cross_street_2,
            'intersection_street_1': self.intersection_street_1,
            'intersection_street_2': self.intersection_street_2,
            'zip_code': self.zip_code,
            'incident_zip': self.incident_zip,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'borough': self.borough,
            'community_board': self.community_board,
            'address_type': self.address_type,
            'location_type': self.location_type,
            'landmark': self.landmark,
            'facility_type': self.facility_type,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'x_coordinate_state_plane': self.x_coordinate_state_plane,
            'y_coordinate_state_plane': self.y_coordinate_state_plane,
            'bbl': self.bbl,
            'risk_level': self.risk_level,
            'confidence_score': self.confidence_score,
            'detected_objects': self.detected_objects,
            'open_date': self.open_date.isoformat() if self.open_date else None,
            'close_date': self.close_date.isoformat() if self.close_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_photos:
            data['photos'] = [photo.to_dict() for photo in self.photos]
            
        return data
    
    def __repr__(self):
        return f'<InfrastructureIssue {self.case_topic} at {self.full_address}>'

class IssuePhoto(db.Model):
    """Photos uploaded for infrastructure issues"""
    __tablename__ = 'issue_photos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('infrastructure_issues.id'), nullable=False)
    
    # File details
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Image metadata
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    
    # Analysis results
    processed = db.Column(db.Boolean, default=False)
    analysis_results = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert photo to dictionary"""
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'processed': self.processed,
            'analysis_results': self.analysis_results,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<IssuePhoto {self.filename}>'

class RiskAssessment(db.Model):
    """AI-generated risk assessments for infrastructure issues"""
    __tablename__ = 'risk_assessments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('infrastructure_issues.id'), nullable=False)
    
    # Assessment details
    risk_level = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    confidence_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    assessment_type = db.Column(db.String(50), nullable=False)  # cv_analysis, geospatial, manual
    
    # Risk factors
    severity_factors = db.Column(db.JSON, nullable=True)  # List of contributing factors
    impact_radius = db.Column(db.Float, nullable=True)  # Meters
    estimated_repair_cost = db.Column(db.Float, nullable=True)
    priority_score = db.Column(db.Float, nullable=True)  # 0.0 to 100.0
    
    # Model information
    model_version = db.Column(db.String(50), nullable=True)
    model_confidence = db.Column(db.Float, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'risk_level': self.risk_level,
            'confidence_score': self.confidence_score,
            'assessment_type': self.assessment_type,
            'severity_factors': self.severity_factors,
            'impact_radius': self.impact_radius,
            'estimated_repair_cost': self.estimated_repair_cost,
            'priority_score': self.priority_score,
            'model_version': self.model_version,
            'model_confidence': self.model_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<RiskAssessment {self.risk_level} for issue {self.issue_id}>'