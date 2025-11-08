"""
Infrastructure issues API routes
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_
from database import db
from models.infrastructure import InfrastructureIssue, IssuePhoto, RiskAssessment
from models.user import User
import uuid
from datetime import datetime

infrastructure_bp = Blueprint('infrastructure', __name__)

@infrastructure_bp.route('/issues', methods=['GET'])
def get_issues():
    """Get all open infrastructure issues with pagination"""
    try:
        # Query parameters for pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Build query - only open issues (no closed_date)
        query = InfrastructureIssue.query.filter(
            or_(
                InfrastructureIssue.close_date.is_(None)
            )
        ).order_by(InfrastructureIssue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'issues': [issue.to_dict() for issue in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/issues/<issue_id>', methods=['GET'])
def get_issue(issue_id):
    """Get a specific infrastructure issue with photos"""
    try:
        issue = InfrastructureIssue.query.get_or_404(issue_id)
        return jsonify(issue.to_dict(include_photos=True))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/issues', methods=['POST'])
def create_issue():
    """Create a new infrastructure issue"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['case_topic', 'service_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new issue
        issue = InfrastructureIssue(
            case_topic=data['case_topic'],
            service_name=data.get('service_name'),
            complaint_type=data.get('complaint_type'),
            descriptor=data.get('descriptor'),
            description=data.get('description'),
            agency=data.get('agency'),
            agency_name=data.get('agency_name'),
            resolution_description=data.get('resolution_description'),
            full_address=data.get('full_address'),
            incident_address=data.get('incident_address'),
            street_number=data.get('street_number'),
            street_name=data.get('street_name'),
            cross_street_1=data.get('cross_street_1'),
            cross_street_2=data.get('cross_street_2'),
            intersection_street_1=data.get('intersection_street_1'),
            intersection_street_2=data.get('intersection_street_2'),
            zip_code=data.get('zip_code'),
            incident_zip=data.get('incident_zip'),
            neighborhood=data.get('neighborhood'),
            city=data.get('city'),
            borough=data.get('borough'),
            community_board=data.get('community_board'),
            address_type=data.get('address_type'),
            location_type=data.get('location_type'),
            landmark=data.get('landmark'),
            facility_type=data.get('facility_type'),
            longitude=data.get('longitude'),
            latitude=data.get('latitude'),
            x_coordinate_state_plane=data.get('x_coordinate_state_plane'),
            y_coordinate_state_plane=data.get('y_coordinate_state_plane'),
            bbl=data.get('bbl'),
            priority=data.get('priority', 'medium')
        )
        
        # Set location point if coordinates provided (disabled until PostGIS is enabled)
        # if issue.longitude and issue.latitude:
        #     from geoalchemy2 import WKTElement
        #     issue.location = WKTElement(f'POINT({issue.longitude} {issue.latitude})', srid=4326)
        
        db.session.add(issue)
        db.session.commit()
        
        return jsonify(issue.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/issues/<issue_id>', methods=['PUT'])
def update_issue(issue_id):
    """Update an infrastructure issue"""
    try:
        issue = InfrastructureIssue.query.get_or_404(issue_id)
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = [
            'case_topic', 'service_name', 'complaint_type', 'descriptor',
            'description', 'case_status', 'priority', 'agency', 'agency_name',
            'resolution_description', 'full_address', 'incident_address',
            'street_number', 'street_name', 'cross_street_1', 'cross_street_2',
            'intersection_street_1', 'intersection_street_2', 'zip_code',
            'incident_zip', 'neighborhood', 'city', 'borough', 'community_board',
            'address_type', 'location_type', 'landmark', 'facility_type',
            'longitude', 'latitude', 'x_coordinate_state_plane', 'y_coordinate_state_plane',
            'bbl', 'risk_level', 'confidence_score'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(issue, field, data[field])
        
        # Update location point if coordinates changed (disabled until PostGIS is enabled)
        # if 'longitude' in data or 'latitude' in data:
        #     if issue.longitude and issue.latitude:
        #         from geoalchemy2 import WKTElement
        #         issue.location = WKTElement(f'POINT({issue.longitude} {issue.latitude})', srid=4326)
        
        # Set close date if status changed to closed
        if data.get('case_status') == 'Closed' and not issue.close_date:
            issue.close_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(issue.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/issues/<issue_id>', methods=['DELETE'])
def delete_issue(issue_id):
    """Delete an infrastructure issue"""
    try:
        issue = InfrastructureIssue.query.get_or_404(issue_id)
        db.session.delete(issue)
        db.session.commit()
        
        return jsonify({'message': 'Issue deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/issues/search', methods=['GET'])
def search_issues():
    """Search issues by text query"""
    try:
        query_text = request.args.get('q', '').strip()
        if not query_text:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Search in multiple fields including NYC DOT fields
        search_filter = or_(
            InfrastructureIssue.case_topic.ilike(f'%{query_text}%'),
            InfrastructureIssue.service_name.ilike(f'%{query_text}%'),
            InfrastructureIssue.complaint_type.ilike(f'%{query_text}%'),
            InfrastructureIssue.descriptor.ilike(f'%{query_text}%'),
            InfrastructureIssue.description.ilike(f'%{query_text}%'),
            InfrastructureIssue.resolution_description.ilike(f'%{query_text}%'),
            InfrastructureIssue.full_address.ilike(f'%{query_text}%'),
            InfrastructureIssue.incident_address.ilike(f'%{query_text}%'),
            InfrastructureIssue.neighborhood.ilike(f'%{query_text}%'),
            InfrastructureIssue.street_name.ilike(f'%{query_text}%'),
            InfrastructureIssue.cross_street_1.ilike(f'%{query_text}%'),
            InfrastructureIssue.cross_street_2.ilike(f'%{query_text}%'),
            InfrastructureIssue.city.ilike(f'%{query_text}%'),
            InfrastructureIssue.borough.ilike(f'%{query_text}%'),
            InfrastructureIssue.community_board.ilike(f'%{query_text}%'),
            InfrastructureIssue.landmark.ilike(f'%{query_text}%'),
            InfrastructureIssue.agency_name.ilike(f'%{query_text}%')
        )
        
        pagination = InfrastructureIssue.query.filter(search_filter)\
            .order_by(InfrastructureIssue.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        issues = pagination.items
        
        return jsonify({
            'issues': [issue.to_dict() for issue in issues],
            'query': query_text,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get infrastructure statistics"""
    try:
        total_issues = InfrastructureIssue.query.count()
        open_issues = InfrastructureIssue.query.filter(
            InfrastructureIssue.case_status != 'Closed'
        ).count()
        
        # Issues by priority
        priority_stats = db.session.query(
            InfrastructureIssue.priority,
            db.func.count(InfrastructureIssue.id)
        ).group_by(InfrastructureIssue.priority).all()
        
        # Issues by risk level
        risk_stats = db.session.query(
            InfrastructureIssue.risk_level,
            db.func.count(InfrastructureIssue.id)
        ).group_by(InfrastructureIssue.risk_level).all()
        
        # Issues by neighborhood (top 10)
        neighborhood_stats = db.session.query(
            InfrastructureIssue.neighborhood,
            db.func.count(InfrastructureIssue.id)
        ).filter(InfrastructureIssue.neighborhood.isnot(None))\
         .group_by(InfrastructureIssue.neighborhood)\
         .order_by(db.func.count(InfrastructureIssue.id).desc())\
         .limit(10).all()
        
        # Issues by borough (NYC DOT specific)
        borough_stats = db.session.query(
            InfrastructureIssue.borough,
            db.func.count(InfrastructureIssue.id)
        ).filter(InfrastructureIssue.borough.isnot(None))\
         .group_by(InfrastructureIssue.borough)\
         .order_by(db.func.count(InfrastructureIssue.id).desc())\
         .all()
        
        # Issues by complaint type (NYC DOT specific)
        complaint_type_stats = db.session.query(
            InfrastructureIssue.complaint_type,
            db.func.count(InfrastructureIssue.id)
        ).filter(InfrastructureIssue.complaint_type.isnot(None))\
         .group_by(InfrastructureIssue.complaint_type)\
         .order_by(db.func.count(InfrastructureIssue.id).desc())\
         .limit(5).all()
        
        # Issues by agency (NYC DOT specific)
        agency_stats = db.session.query(
            InfrastructureIssue.agency,
            db.func.count(InfrastructureIssue.id)
        ).filter(InfrastructureIssue.agency.isnot(None))\
         .group_by(InfrastructureIssue.agency)\
         .order_by(db.func.count(InfrastructureIssue.id).desc())\
         .all()
        
        return jsonify({
            'total_issues': total_issues,
            'open_issues': open_issues,
            'closed_issues': total_issues - open_issues,
            'priority_breakdown': {priority: count for priority, count in priority_stats},
            'risk_breakdown': {risk: count for risk, count in risk_stats},
            'top_neighborhoods': [
                {'neighborhood': neighborhood, 'count': count}
                for neighborhood, count in neighborhood_stats
            ],
            'borough_breakdown': {borough: count for borough, count in borough_stats},
            'top_complaint_types': [
                {'complaint_type': complaint_type, 'count': count}
                for complaint_type, count in complaint_type_stats
            ],
            'agency_breakdown': {agency: count for agency, count in agency_stats}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/import/nyc-dot', methods=['POST'])
def import_nyc_dot_data():
    """Import NYC DOT data from JSON payload"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Expect data as a list of records
        if not isinstance(data, list):
            return jsonify({'error': 'Data must be a list of records'}), 400
        
        # Import the data
        from services.data_importer import DataImporter
        importer = DataImporter()
        stats = importer.import_nyc_dot_data(data)
        
        return jsonify({
            'success': True,
            'message': 'NYC DOT data import completed',
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@infrastructure_bp.route('/import/test-nyc-dot', methods=['POST'])
def test_import_nyc_dot():
    """Test import with the provided sample NYC DOT data"""
    try:
        # Sample data from user
        test_data = [
            {
                "idx": 0,
                "Unique Key": 63575321,
                "Created Date": "01/01/2025 02:27:33 AM",
                "Closed Date": "01/02/2025 12:40:00 PM",
                "Agency": "DOT",
                "Agency Name": "Department of Transportation",
                "Complaint Type": "Street Condition",
                "Descriptor": "Pothole",
                "Location Type": "",
                "Incident Zip": "11219",
                "Incident Address": "60 STREET",
                "Street Name": "60 STREET",
                "Cross Street 1": "9 AVENUE",
                "Cross Street 2": "FT HAMILTON PARKWAY",
                "Intersection Street 1": "",
                "Intersection Street 2": "",
                "Address Type": "BLOCKFACE",
                "City": "BROOKLYN",
                "Landmark": "",
                "Facility Type": "N/A",
                "Status": "Closed",
                "Due Date": "",
                "Resolution Description": "The Department of Transportation inspected this complaint and repaired the problem.",
                "Resolution Action Updated Date": "01/02/2025 12:40:00 PM",
                "Community Board": "12 BROOKLYN",
                "BBL": "",
                "Borough": "BROOKLYN",
                "X Coordinate (State Plane)": "",
                "Y Coordinate (State Plane)": "",
                "Open Data Channel Type": "UNKNOWN",
                "Park Facility Name": "Unspecified",
                "Park Borough": "BROOKLYN",
                "Vehicle Type": "",
                "Taxi Company Borough": "",
                "Taxi Pick Up Location": "",
                "Bridge Highway Name": "",
                "Bridge Highway Direction": "",
                "Road Ramp": "",
                "Bridge Highway Segment": "",
                "Latitude": "",
                "Longitude": "",
                "Location": ""
            },
            {
                "idx": 1,
                "Unique Key": 63580421,
                "Created Date": "01/01/2025 02:55:52 AM",
                "Closed Date": "01/06/2025 11:00:00 AM",
                "Agency": "DOT",
                "Agency Name": "Department of Transportation",
                "Complaint Type": "Street Condition",
                "Descriptor": "Pothole",
                "Location Type": "",
                "Incident Zip": "11414",
                "Incident Address": "151 AVENUE",
                "Street Name": "151 AVENUE",
                "Cross Street 1": "85 STREET",
                "Cross Street 2": "88 STREET",
                "Intersection Street 1": "",
                "Intersection Street 2": "",
                "Address Type": "BLOCKFACE",
                "City": "QUEENS",
                "Landmark": "",
                "Facility Type": "N/A",
                "Status": "Closed",
                "Due Date": "",
                "Resolution Description": "The Department of Transportation inspected this complaint and repaired the problem.",
                "Resolution Action Updated Date": "01/06/2025 11:00:00 AM",
                "Community Board": "10 QUEENS",
                "BBL": "",
                "Borough": "QUEENS",
                "X Coordinate (State Plane)": "",
                "Y Coordinate (State Plane)": "",
                "Open Data Channel Type": "UNKNOWN",
                "Park Facility Name": "Unspecified",
                "Park Borough": "QUEENS",
                "Vehicle Type": "",
                "Taxi Company Borough": "",
                "Taxi Pick Up Location": "",
                "Bridge Highway Name": "",
                "Bridge Highway Direction": "",
                "Road Ramp": "",
                "Bridge Highway Segment": "",
                "Latitude": "",
                "Longitude": "",
                "Location": ""
            },
            {
                "idx": 2,
                "Unique Key": 63585580,
                "Created Date": "01/01/2025 02:31:08 AM",
                "Closed Date": "01/06/2025 10:20:00 AM",
                "Agency": "DOT",
                "Agency Name": "Department of Transportation",
                "Complaint Type": "Street Condition",
                "Descriptor": "Pothole",
                "Location Type": "",
                "Incident Zip": "11417",
                "Incident Address": "",
                "Street Name": "",
                "Cross Street 1": "",
                "Cross Street 2": "",
                "Intersection Street 1": "96 STREET",
                "Intersection Street 2": "PLATTWOOD AVENUE",
                "Address Type": "INTERSECTION",
                "City": "QUEENS",
                "Landmark": "",
                "Facility Type": "N/A",
                "Status": "Closed",
                "Due Date": "",
                "Resolution Description": "The Department of Transportation inspected this complaint and repaired the problem.",
                "Resolution Action Updated Date": "01/06/2025 10:20:00 AM",
                "Community Board": "10 QUEENS",
                "BBL": "",
                "Borough": "QUEENS",
                "X Coordinate (State Plane)": "1,028,295",
                "Y Coordinate (State Plane)": "185,833",
                "Open Data Channel Type": "UNKNOWN",
                "Park Facility Name": "Unspecified",
                "Park Borough": "QUEENS",
                "Vehicle Type": "",
                "Taxi Company Borough": "",
                "Taxi Pick Up Location": "",
                "Bridge Highway Name": "",
                "Bridge Highway Direction": "",
                "Road Ramp": "",
                "Bridge Highway Segment": "",
                "Latitude": "40.67663584074",
                "Longitude": "-73.84120938334",
                "Location": "(40.67663584073802, -73.84120938333966)"
            }
        ]
        
        # Import the test data
        from services.data_importer import DataImporter
        importer = DataImporter()
        stats = importer.import_nyc_dot_data(test_data)
        
        return jsonify({
            'success': True,
            'message': 'NYC DOT test data import completed',
            'stats': stats,
            'sample_count': len(test_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500