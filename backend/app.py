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