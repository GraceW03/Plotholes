"""
Geospatial processing and path planning API routes
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_, func
from app import db
from models.infrastructure import InfrastructureIssue
from models.geospatial import GeoLocation, PathPlan
from services.geospatial_processor import GeospatialProcessor
import json

geospatial_bp = Blueprint('geospatial', __name__)

@geospatial_bp.route('/heat-map', methods=['GET'])
def get_heat_map():
    """Generate heat map data for infrastructure issues"""
    try:
        # Get geographic bounds
        min_lat = request.args.get('min_lat', type=float)
        max_lat = request.args.get('max_lat', type=float)
        min_lng = request.args.get('min_lng', type=float)
        max_lng = request.args.get('max_lng', type=float)
        
        # Get filter parameters
        risk_level = request.args.get('risk_level')
        issue_type = request.args.get('issue_type')
        days_back = request.args.get('days_back', 30, type=int)
        
        # Use NYC bounds as default
        if not all([min_lat, max_lat, min_lng, max_lng]):
            min_lat, max_lat = 40.477399, 40.917577
            min_lng, max_lng = -74.259090, -73.700272
        
        # Build query
        query = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.latitude.isnot(None),
                InfrastructureIssue.longitude.isnot(None),
                InfrastructureIssue.latitude >= min_lat,
                InfrastructureIssue.latitude <= max_lat,
                InfrastructureIssue.longitude >= min_lng,
                InfrastructureIssue.longitude <= max_lng
            )
        )
        
        # Apply filters
        if risk_level:
            query = query.filter(InfrastructureIssue.risk_level == risk_level)
        if issue_type:
            query = query.filter(InfrastructureIssue.case_topic.ilike(f'%{issue_type}%'))
        
        # Get recent issues
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(InfrastructureIssue.created_at >= cutoff_date)
        
        issues = query.all()
        
        # Format heat map data
        heat_map_data = []
        for issue in issues:
            # Weight based on risk level
            weight_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4, 'unknown': 1}
            weight = weight_map.get(issue.risk_level, 1)
            
            heat_map_data.append({
                'lat': issue.latitude,
                'lng': issue.longitude,
                'weight': weight,
                'issue_id': issue.id,
                'case_topic': issue.case_topic,
                'risk_level': issue.risk_level,
                'neighborhood': issue.neighborhood
            })
        
        # Calculate density statistics
        processor = GeospatialProcessor()
        density_stats = processor.calculate_density_stats(heat_map_data, min_lat, max_lat, min_lng, max_lng)
        
        return jsonify({
            'heat_map_data': heat_map_data,
            'bounds': {
                'min_lat': min_lat, 'max_lat': max_lat,
                'min_lng': min_lng, 'max_lng': max_lng
            },
            'total_points': len(heat_map_data),
            'density_stats': density_stats,
            'filters_applied': {
                'risk_level': risk_level,
                'issue_type': issue_type,
                'days_back': days_back
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geospatial_bp.route('/path-planning', methods=['POST'])
def plan_safe_path():
    """Plan a safe route avoiding infrastructure issues"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['start_lat', 'start_lng', 'end_lat', 'end_lng']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        start_lat = data['start_lat']
        start_lng = data['start_lng']
        end_lat = data['end_lat']
        end_lng = data['end_lng']
        
        # Optional parameters
        route_type = data.get('route_type', 'driving')  # driving, walking, cycling
        avoid_risk_levels = data.get('avoid_risk_levels', ['high', 'critical'])
        max_detour_factor = data.get('max_detour_factor', 1.5)
        
        # Use geospatial processor to plan route
        processor = GeospatialProcessor()
        path_result = processor.plan_safe_route(
            start_lat, start_lng, end_lat, end_lng,
            route_type=route_type,
            avoid_risk_levels=avoid_risk_levels,
            max_detour_factor=max_detour_factor
        )
        
        if not path_result['success']:
            return jsonify({'error': path_result['error']}), 400
        
        # Save path plan to database
        path_plan = PathPlan(
            route_type=route_type,
            start_latitude=start_lat,
            start_longitude=start_lng,
            end_latitude=end_lat,
            end_longitude=end_lng,
            start_address=data.get('start_address'),
            end_address=data.get('end_address'),
            route_points=path_result['route_points'],
            distance_km=path_result['distance_km'],
            estimated_duration_minutes=path_result['duration_minutes'],
            safety_score=path_result['safety_score'],
            avoided_hazards=path_result['avoided_hazards'],
            risk_areas_count=len(path_result['avoided_hazards']),
            algorithm_used=path_result['algorithm_used'],
            weights_config=path_result.get('weights_config')
        )
        
        # Set geometry
        if path_result['route_points']:
            from geoalchemy2 import WKTElement
            # Create LINESTRING from route points
            points_str = ', '.join([f'{point[1]} {point[0]}' for point in path_result['route_points']])
            path_plan.route_geometry = WKTElement(f'LINESTRING({points_str})', srid=4326)
            path_plan.start_location = WKTElement(f'POINT({start_lng} {start_lat})', srid=4326)
            path_plan.end_location = WKTElement(f'POINT({end_lng} {end_lat})', srid=4326)
        
        db.session.add(path_plan)
        db.session.commit()
        
        return jsonify({
            'path_plan': path_plan.to_dict(include_geometry=True),
            'route_analysis': path_result
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@geospatial_bp.route('/nearby-issues', methods=['GET'])
def get_nearby_issues():
    """Get infrastructure issues near a location"""
    try:
        # Get location parameters
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius_km = request.args.get('radius_km', 1.0, type=float)
        
        if not lat or not lng:
            return jsonify({'error': 'lat and lng parameters required'}), 400
        
        # Limit radius to reasonable value
        radius_km = min(radius_km, 50.0)
        
        # Use geospatial processor to find nearby issues
        processor = GeospatialProcessor()
        nearby_issues = processor.find_nearby_issues(lat, lng, radius_km)
        
        return jsonify({
            'center': {'lat': lat, 'lng': lng},
            'radius_km': radius_km,
            'issues': nearby_issues,
            'total_count': len(nearby_issues)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geospatial_bp.route('/clusters', methods=['GET'])
def get_issue_clusters():
    """Get clustered infrastructure issues for map display"""
    try:
        # Get parameters
        zoom_level = request.args.get('zoom', 10, type=int)
        min_lat = request.args.get('min_lat', type=float)
        max_lat = request.args.get('max_lat', type=float)
        min_lng = request.args.get('min_lng', type=float)
        max_lng = request.args.get('max_lng', type=float)
        
        # Use NYC bounds as default
        if not all([min_lat, max_lat, min_lng, max_lng]):
            min_lat, max_lat = 40.477399, 40.917577
            min_lng, max_lng = -74.259090, -73.700272
        
        # Use geospatial processor to create clusters
        processor = GeospatialProcessor()
        clusters = processor.create_issue_clusters(
            min_lat, max_lat, min_lng, max_lng, zoom_level
        )
        
        return jsonify({
            'clusters': clusters,
            'zoom_level': zoom_level,
            'bounds': {
                'min_lat': min_lat, 'max_lat': max_lat,
                'min_lng': min_lng, 'max_lng': max_lng
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geospatial_bp.route('/neighborhood-stats', methods=['GET'])
def get_neighborhood_stats():
    """Get infrastructure statistics by neighborhood"""
    try:
        # Query issues grouped by neighborhood
        neighborhood_stats = db.session.query(
            InfrastructureIssue.neighborhood,
            func.count(InfrastructureIssue.id).label('total_issues'),
            func.count(func.nullif(InfrastructureIssue.case_status != 'Closed', False)).label('open_issues'),
            func.avg(
                func.case(
                    (InfrastructureIssue.risk_level == 'low', 1),
                    (InfrastructureIssue.risk_level == 'medium', 2),
                    (InfrastructureIssue.risk_level == 'high', 3),
                    (InfrastructureIssue.risk_level == 'critical', 4),
                    else_=1
                )
            ).label('avg_risk_score')
        ).filter(
            InfrastructureIssue.neighborhood.isnot(None)
        ).group_by(
            InfrastructureIssue.neighborhood
        ).order_by(
            func.count(InfrastructureIssue.id).desc()
        ).all()
        
        # Format results
        neighborhoods = []
        for stat in neighborhood_stats:
            # Convert avg risk score back to level
            avg_score = stat.avg_risk_score or 1
            if avg_score >= 3.5:
                avg_risk_level = 'critical'
            elif avg_score >= 2.5:
                avg_risk_level = 'high'
            elif avg_score >= 1.5:
                avg_risk_level = 'medium'
            else:
                avg_risk_level = 'low'
            
            neighborhoods.append({
                'neighborhood': stat.neighborhood,
                'total_issues': stat.total_issues,
                'open_issues': stat.open_issues,
                'closed_issues': stat.total_issues - stat.open_issues,
                'avg_risk_level': avg_risk_level,
                'avg_risk_score': round(avg_score, 2)
            })
        
        return jsonify({
            'neighborhoods': neighborhoods,
            'total_neighborhoods': len(neighborhoods)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geospatial_bp.route('/bounds', methods=['GET'])
def get_data_bounds():
    """Get geographic bounds of all infrastructure data"""
    try:
        bounds_query = db.session.query(
            func.min(InfrastructureIssue.latitude).label('min_lat'),
            func.max(InfrastructureIssue.latitude).label('max_lat'),
            func.min(InfrastructureIssue.longitude).label('min_lng'),
            func.max(InfrastructureIssue.longitude).label('max_lng')
        ).filter(
            and_(
                InfrastructureIssue.latitude.isnot(None),
                InfrastructureIssue.longitude.isnot(None)
            )
        ).first()
        
        if bounds_query and bounds_query.min_lat:
            return jsonify({
                'min_lat': bounds_query.min_lat,
                'max_lat': bounds_query.max_lat,
                'min_lng': bounds_query.min_lng,
                'max_lng': bounds_query.max_lng,
                'center': {
                    'lat': (bounds_query.min_lat + bounds_query.max_lat) / 2,
                    'lng': (bounds_query.min_lng + bounds_query.max_lng) / 2
                }
            })
        else:
            # Return NYC bounds as default
            return jsonify({
                'min_lat': 40.477399,
                'max_lat': 40.917577,
                'min_lng': -74.259090,
                'max_lng': -73.700272,
                'center': {'lat': 40.7589, 'lng': -73.9851}
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500