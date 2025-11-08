"""
Infrastructure issue models based on Boston 311 data
"""

from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

db = SQLAlchemy()

class InfrastructureIssue(db.Model):
    """Infrastructure issue model based on Boston 311 data structure"""
    __tablename__ = 'infrastructure_issues'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(50), unique=True, nullable=True)  # Original BCS case ID if imported
    
    # Issue details
    case_topic = db.Column(db.String(100), nullable=False)  # e.g., "Street Light Outage", "Pothole"
    service_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    case_status = db.Column(db.String(50), default='Open')  # Open, In Progress, Closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Location data
    full_address = db.Column(db.String(255), nullable=True)
    street_number = db.Column(db.String(20), nullable=True)
    street_name = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    neighborhood = db.Column(db.String(100), nullable=True)
    
    # Geospatial data
    longitude = db.Column(db.Float, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    location = db.Column(Geometry('POINT', srid=4326), nullable=True)
    
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
            'case_topic': self.case_topic,
            'service_name': self.service_name,
            'description': self.description,
            'case_status': self.case_status,
            'priority': self.priority,
            'full_address': self.full_address,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'zip_code': self.zip_code,
            'neighborhood': self.neighborhood,
            'longitude': self.longitude,
            'latitude': self.latitude,
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