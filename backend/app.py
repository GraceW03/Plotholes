"""
Plotholes Backend - Geospatial AI Platform
Main Flask application entry point
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from database import db, migrate

# Load environment variables
load_dotenv()

def create_app(config_name):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS
    CORS(app, origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000"
    ])
    
    # Register blueprints
    from routes.infrastructure import infrastructure_bp
    from routes.photos import photos_bp
    
    app.register_blueprint(infrastructure_bp, url_prefix='/api/infrastructure')
    app.register_blueprint(photos_bp, url_prefix='/api/photos')
    
    # Base route
    @app.route('/')
    def on_start():
        return jsonify({
            'message': 'hi'
        })

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Plotholes Backend API is running',
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app('production')
    app.run(debug=True, host='0.0.0.0', port=5000)