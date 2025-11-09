"""
Plotholes Backend - Geospatial AI Platform
Main Flask application entry point
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from .database import db, migrate
from sqlalchemy import text
from .services.heatmap import *
import math
import osmnx as ox
from .services.pathplanning import compute_final_route
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
    from .config import config
    app.config.from_object(config['production'])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS
    CORS(app, origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000"
    ])

    with app.app_context():
        # -------------------------------
        # Cache blocked edges at startup
        # -------------------------------
        from .models.BlockedEdges import BlockedEdges
        app.blocked_edges_set = set(
            (e.u, e.v, e.k) for e in BlockedEdges.query.all()
        )
        print(f"Cached {len(app.blocked_edges_set)} blocked edges")

        # -------------------------------
        # Cache NYC map at startup
        # -------------------------------
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        GRAPH_PATH = os.path.join(BASE_DIR, 'data', 'nyc_graphml.graphml')
        # Check if file exists (optional, helps debug)
        if not os.path.exists(GRAPH_PATH):
            raise FileNotFoundError(f"GraphML file not found at {GRAPH_PATH}")

        app.nyc_graph = ox.load_graphml(GRAPH_PATH)
        print(f"Loaded NYC graph from {GRAPH_PATH}")
    
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
                
            from .model import analyze_image
            
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
                    'severity': calculate_severity(row.descriptor),
                    'incident_address': row.incident_address
                })
            
            return success_response({
                'issues': issues,
                'count': len(issues)
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    @app.route('/api/route', methods=['POST'])
    def compute_route():
        """
        Expects JSON payload:
        {
            "origin": [lat, lon],
            "destination": [lat, lon]
        }
        """
        data = request.get_json()
        origin = data.get('origin')
        destination = data.get('destination')

        if not origin or not destination:
            return failure_response("Missing origin or destination")
        
        try:
            # Validate input types
            if not (isinstance(origin, list) and len(origin) == 2 and all(isinstance(x, (int, float)) for x in origin)):
                return failure_response(f"Invalid origin coordinates: {origin}")
            if not (isinstance(destination, list) and len(destination) == 2 and all(isinstance(x, (int, float)) for x in destination)):
                return failure_response(f"Invalid destination coordinates: {destination}")
            
            route_coords = compute_final_route(
                graph=app.nyc_graph, 
                origin=origin,
                destination=destination, 
                blocked_edges_set=app.blocked_edges_set)
            
            if not route_coords:
                return failure_response(
                    "No available path avoiding blocked streets",
                    404
                )
            
            return success_response({
                "route": route_coords,
                "length": len(route_coords)
            })
        except Exception as e:
            return failure_response(str(e), 500)
        
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
            
            # Get user-submitted reports
            reports_query = text("""
                SELECT
                    lat as latitude,
                    lng as longitude,
                    severity
                FROM reports
            """)
            
            # Process NYC street data issues
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
            
            # Process user reports
            reports_result = db.session.execute(reports_query)
            for row in reports_result:
                try:
                    lat = float(row.latitude)
                    lng = float(row.longitude)
                    
                    # Convert severity string to numeric value
                    severity_map = {
                        'none': 1,
                        'low': 2,
                        'medium': 3,
                        'high': 4,
                        'critical': 5
                    }
                    numeric_severity = severity_map.get(row.severity.lower() if row.severity else 'none', 1)
                    
                    issues.append({'lat': lat, 'lng': lng, 'severity': numeric_severity})
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

    @app.route('/api/reports', methods=['GET'])
    def get_reports():
        """Get user-submitted reports for heatmap"""
        try:
            # Query the reports table
            query = text("""
                SELECT
                    id,
                    image_url,
                    lat,
                    lng,
                    severity,
                    confidence,
                    created_at
                FROM reports
                ORDER BY created_at DESC
            """)
            
            result = db.session.execute(query)
            
            # Convert to list of dictionaries
            reports = []
            for row in result:
                # Map severity string to numeric value for heatmap
                severity_map = {
                    'none': 1,
                    'low': 2,
                    'medium': 3,
                    'high': 4,
                    'critical': 5
                }
                
                numeric_severity = severity_map.get(row.severity.lower() if row.severity else 'none', 1)
                
                reports.append({
                    'id': row.id,
                    'image_url': row.image_url,
                    'latitude': float(row.lat) if row.lat else None,
                    'longitude': float(row.lng) if row.lng else None,
                    'severity': numeric_severity,
                    'severity_text': row.severity,
                    'confidence': row.confidence,
                    'created_at': str(row.created_at)
                })
            
            return success_response({
                'reports': reports,
                'count': len(reports)
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

# Run using python -m backend.app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=3001)