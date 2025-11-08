"""
Reporting and analytics models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Report(db.Model):
    """Generated reports and analytics"""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Report details
    title = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # heat_map, risk_analysis, summary, trend
    description = db.Column(db.Text, nullable=True)
    
    # Report parameters
    date_range_start = db.Column(db.DateTime, nullable=True)
    date_range_end = db.Column(db.DateTime, nullable=True)
    geographic_bounds = db.Column(db.JSON, nullable=True)  # Bounding box coordinates
    filters_applied = db.Column(db.JSON, nullable=True)  # Report filters
    
    # Report data
    data = db.Column(db.JSON, nullable=True)  # Report results/data
    summary_stats = db.Column(db.JSON, nullable=True)  # Key statistics
    visualization_config = db.Column(db.JSON, nullable=True)  # Chart/map configuration
    
    # File output
    output_format = db.Column(db.String(20), nullable=True)  # json, pdf, csv, png
    file_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    
    # Status and metadata
    status = db.Column(db.String(20), default='generating')  # generating, completed, failed
    progress = db.Column(db.Float, default=0.0)  # 0.0 to 100.0
    error_message = db.Column(db.Text, nullable=True)
    
    # Relationships
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self, include_data=False):
        """Convert report to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'report_type': self.report_type,
            'description': self.description,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'geographic_bounds': self.geographic_bounds,
            'filters_applied': self.filters_applied,
            'summary_stats': self.summary_stats,
            'visualization_config': self.visualization_config,
            'output_format': self.output_format,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_data:
            data['data'] = self.data
            
        return data
    
    def __repr__(self):
        return f'<Report {self.title} ({self.report_type})>'

class ReportAnalytics(db.Model):
    """Analytics and metrics for the platform"""
    __tablename__ = 'report_analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Analytics details
    metric_name = db.Column(db.String(100), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # count, average, sum, percentage
    category = db.Column(db.String(50), nullable=False)  # issues, safety, performance, usage
    
    # Time period
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    
    # Metric value and context
    value = db.Column(db.Float, nullable=False)
    previous_value = db.Column(db.Float, nullable=True)
    change_percentage = db.Column(db.Float, nullable=True)
    
    # Geographic context
    neighborhood = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    geographic_bounds = db.Column(db.JSON, nullable=True)
    
    # Additional metadata
    filters = db.Column(db.JSON, nullable=True)
    breakdown = db.Column(db.JSON, nullable=True)  # Detailed breakdown of the metric
    
    # Timestamps
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert analytics to dictionary"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'category': self.category,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'period_type': self.period_type,
            'value': self.value,
            'previous_value': self.previous_value,
            'change_percentage': self.change_percentage,
            'neighborhood': self.neighborhood,
            'zip_code': self.zip_code,
            'geographic_bounds': self.geographic_bounds,
            'filters': self.filters,
            'breakdown': self.breakdown,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }
    
    def __repr__(self):
        return f'<ReportAnalytics {self.metric_name}: {self.value}>'