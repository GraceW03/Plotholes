"""
Configuration settings for different environments
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Computer Vision settings
    CV_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    YOLO_MODEL = 'yolov8n.pt'  # You can upgrade to larger models
    
    # Geospatial settings
    DEFAULT_SRID = 4326  # WGS84
    NYC_BOUNDS = {
        'min_lat': 40.477399,
        'max_lat': 40.917577,
        'min_lng': -74.259090,
        'max_lng': -73.700272
    }
    
    # API Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    
    @staticmethod
    def init_app(app):
        pass

class ProductionConfig(Config):
    """Production configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/plotholes_prod'
    
    # Production security settings
    SSL_DISABLE = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}