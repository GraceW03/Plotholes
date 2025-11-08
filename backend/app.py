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
# from data import *
from shapely.geometry import Point, Polygon as ShapelyPolygon
import json

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
    

    @app.route('/issues', methods=['GET'])
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
                    'severity': calculate_severity(row.descriptor),
                    'incident_address': row.incident_address
                })
            
            return success_response({
                'issues': issues,
                'count': len(issues)
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        
    @app.route('/api/neighborhood-boundaries', methods=['GET'])
    def get_neighborhood_boundaries():
        """Get NYC neighborhood boundaries with issue counts"""
        try:
            
            # Load the GeoJSON file
            geojson_path = os.path.join(os.path.dirname(__file__), 'data', 'nyc_neighborhoods.geojson')
            print(geojson_path)
            with open(geojson_path, 'r') as f:
                neighborhoods_geojson = json.load(f)
            
            # Get all open issues with coordinates
            issues_query = text("""
                SELECT
                    "Latitude" as latitude,
                    "Longitude" as longitude,
                    "Descriptor" as descriptor
                FROM nyc_street_data
                WHERE ("Closed Date" = '' OR "Closed Date" IS NULL)
                AND "Latitude" != ''
                AND "Longitude" != ''
            """)
            
            result = db.session.execute(issues_query)
            issues = []
            for row in result:
                try:
                    lat = float(row.latitude)
                    lng = float(row.longitude)
                    severity = calculate_severity(row.descriptor)
                    issues.append({'lat': lat, 'lng': lng, 'severity': severity})
                except (ValueError, TypeError):
                    continue
            
            # Process each neighborhood
            enriched_neighborhoods = []
            
            for feature in neighborhoods_geojson['features']:
                neighborhood_name = feature['properties']['neighborhood']
                borough = feature['properties']['borough']
                coordinates = feature['geometry']['coordinates']
                
                # Create shapely polygon for point-in-polygon testing
                if feature['geometry']['type'] == 'Polygon':
                    # Handle simple polygon
                    polygon_coords = coordinates[0]  # First ring (exterior)
                    shapely_polygon = ShapelyPolygon([(coord[0], coord[1]) for coord in polygon_coords])
                else:
                    # Skip multipolygons for now (could be enhanced later)
                    continue
                
                # Count issues within this neighborhood
                issues_in_neighborhood = []
                for issue in issues:
                    point = Point(issue['lng'], issue['lat'])
                    if shapely_polygon.contains(point):
                        issues_in_neighborhood.append(issue)
                
                # Calculate neighborhood statistics
                issue_count = len(issues_in_neighborhood)
                if issue_count > 0:
                    severities = [issue['severity'] for issue in issues_in_neighborhood]
                    avg_severity = sum(severities) / len(severities)
                    max_severity = max(severities)
                    
                    # Calculate risk score similar to grid zones
                    risk_score = (issue_count * avg_severity) / 10
                    
                    # Determine risk level and color
                    if risk_score >= 20 or (issue_count >= 15 and avg_severity >= 4):
                        risk_level = 'critical'
                        color = '#990000'
                        opacity = 0.6
                    elif risk_score >= 10 or (issue_count >= 10 and avg_severity >= 3):
                        risk_level = 'high'
                        color = '#ff0000'
                        opacity = 0.5
                    elif risk_score >= 5 or issue_count >= 5:
                        risk_level = 'medium'
                        color = '#ff9900'
                        opacity = 0.4
                    elif issue_count >= 2:
                        risk_level = 'low'
                        color = '#ffff00'
                        opacity = 0.3
                    else:
                        risk_level = 'very_low'
                        color = '#00ff00'
                        opacity = 0.2
                else:
                    avg_severity = 0
                    max_severity = 0
                    risk_score = 0
                    risk_level = 'none'
                    color = '#cccccc'
                    opacity = 0.1
                
                # Create enriched feature
                enriched_feature = {
                    'type': 'Feature',
                    'properties': {
                        'neighborhood': neighborhood_name,
                        'borough': borough,
                        'issue_count': issue_count,
                        'avg_severity': round(avg_severity, 2),
                        'max_severity': max_severity,
                        'risk_score': round(risk_score, 2),
                        'risk_level': risk_level,
                        'color': color,
                        'opacity': opacity
                    },
                    'geometry': feature['geometry']
                }
                
                enriched_neighborhoods.append(enriched_feature)
            
            # Sort by risk score (highest first)
            enriched_neighborhoods.sort(key=lambda x: x['properties']['risk_score'], reverse=True)
            
            return jsonify({
                'type': 'FeatureCollection',
                'features': enriched_neighborhoods,
                'count': len(enriched_neighborhoods)
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
    app.run(debug=True, host='0.0.0.0', port=5000)