"""
Plotholes Backend - Geospatial AI Platform
Main Flask application entry point
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from database import db, migrate
from sqlalchemy import text
from services.heatmap import *
import math

# Load environment variables
load_dotenv()

# generalized response formats
def success_response(data, code=200):
    return jsonify(data), code


def failure_response(message, code=404):
    return jsonify({"error": message}), code

######## CREATE APP 
def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    from config import config
    app.config.from_object(config['production'])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS
    CORS(app, origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000"
    ])
    
    
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
    

    @app.route('/api/analyze', methods=['POST'])
    def analyze():
        try:
            data = request.get_json()
            if not data or 'image_path' not in data:
                return failure_response("Missing image_path", 400)
                
            from model import analyze_image
            
            # Check if this is a test image
            is_test = data.get('is_test', False)
            if is_test:
                # Use the local test image
                import os
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                image_path = os.path.join(base_dir, 'data', 'test_photos', data['image_path'])
                result = analyze_image(image_path, is_url=False)
            else:
                # Use the provided URL
                result = analyze_image(data['image_path'], is_url=True)
                
            return success_response(result)
                
        except Exception as e:
            app.logger.error(f"Error in /api/analyze: {str(e)}")
            return failure_response(str(e), 500)

    @app.route('/api/issues', methods=['GET'])
    def get_issues():
        """Get open issues for heatmap - raw SQL, no models needed"""
        try:
            # Simple SQL query to get open issues with coordinates
            query = text("""
                SELECT 
                    "Unique Key" as unique_key,
                    "Complaint Type" as complaint_type,
                    "Descriptor" as descriptor,
                    "Status" as status,
                    "Borough" as borough,
                    "Latitude" as latitude,
                    "Longitude" as longitude,
                    "Created Date" as created_date,
                    "Incident Address" as incident_address
                FROM nyc_street_data
                WHERE ("Closed Date" = '' OR "Closed Date" IS NULL)
                AND "Latitude" != '' 
                AND "Longitude" != ''
                LIMIT 5000
            """)
            
            result = db.session.execute(query)
            
            # Convert to list of dictionaries
            issues = []
            for row in result:
                issues.append({
                    'unique_key': row.unique_key,
                    'complaint_type': row.complaint_type,
                    'descriptor': row.descriptor,
                    'status': row.status,
                    'borough': row.borough,
                    'latitude': float(row.latitude) if row.latitude else None,
                    'longitude': float(row.longitude) if row.longitude else None,
                    'created_date': row.created_date,
                    'incident_address': row.incident_address
                })
            
            return success_response({
                'issues': issues,
                'count': len(issues)
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    

        
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return failure_response("not found")
    
    @app.errorhandler(500)
    def internal_error(error):
        return failure_response('Internal server error', 500)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=3001)