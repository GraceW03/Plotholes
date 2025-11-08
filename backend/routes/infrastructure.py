"""
Infrastructure issues API routes
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_
from app import db
from models.infrastructure import InfrastructureIssue, IssuePhoto, RiskAssessment
from models.user import User
import uuid
from datetime import datetime

infrastructure_bp = Blueprint('infrastructure', __name__)

@infrastructure_bp.route('/issues', methods=['GET'])
def get_issues():
    """Get infrastructure issues with filtering and pagination"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Filters
        status = request.args.get('status')
        topic = request.args.get('topic')
        neighborhood = request.args.get('neighborhood')
        risk_level = request.args.get('risk_level')
        priority = request.args.get('priority')
        
        # Geographic bounds
        min_lat = request.args.get('min_lat', type=float)
        max_lat = request.args.get('max_lat', type=float)
        min_lng = request.args.get('min_lng', type=float)
        max_lng = request.args.get('max_lng', type=float)
        
        # Build query
        query = InfrastructureIssue.query
        
        # Apply filters
        if status:
            query = query.filter(InfrastructureIssue.case_status == status)
        if topic:
            query = query.filter(InfrastructureIssue.case_topic.ilike(f'%{topic}%'))
        if neighborhood:
            query = query.filter(InfrastructureIssue.neighborhood.ilike(f'%{neighborhood}%'))
        if risk_level:
            query = query.filter(InfrastructureIssue.risk_level == risk_level)
        if priority:
            query = query.filter(InfrastructureIssue.priority == priority)
            
        # Geographic filtering
        if all([min_lat, max_lat, min_lng, max_lng]):
            query = query.filter(and_(
                InfrastructureIssue.latitude >= min_lat,
                InfrastructureIssue.latitude <= max_lat,
                InfrastructureIssue.longitude >= min_lng,
                InfrastructureIssue.longitude <= max_lng
            ))
        
        # Order by creation date (newest first)
        query = query.order_by(InfrastructureIssue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        issues = pagination.items
        
        return jsonify({
            'issues': [issue.to_dict() for issue in issues],
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
            service_name=data['service_name'],
            description=data.get('description'),
            full_address=data.get('full_address'),
            street_number=data.get('street_number'),
            street_name=data.get('street_name'),
            zip_code=data.get('zip_code'),
            neighborhood=data.get('neighborhood'),
            longitude=data.get('longitude'),
            latitude=data.get('latitude'),
            priority=data.get('priority', 'medium')
        )
        
        # Set location point if coordinates provided
        if issue.longitude and issue.latitude:
            from geoalchemy2 import WKTElement
            issue.location = WKTElement(f'POINT({issue.longitude} {issue.latitude})', srid=4326)
        
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
            'case_topic', 'service_name', 'description', 'case_status',
            'priority', 'full_address', 'street_number', 'street_name',
            'zip_code', 'neighborhood', 'longitude', 'latitude',
            'risk_level', 'confidence_score'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(issue, field, data[field])
        
        # Update location point if coordinates changed
        if 'longitude' in data or 'latitude' in data:
            if issue.longitude and issue.latitude:
                from geoalchemy2 import WKTElement
                issue.location = WKTElement(f'POINT({issue.longitude} {issue.latitude})', srid=4326)
        
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
        
        # Search in multiple fields
        search_filter = or_(
            InfrastructureIssue.case_topic.ilike(f'%{query_text}%'),
            InfrastructureIssue.service_name.ilike(f'%{query_text}%'),
            InfrastructureIssue.description.ilike(f'%{query_text}%'),
            InfrastructureIssue.full_address.ilike(f'%{query_text}%'),
            InfrastructureIssue.neighborhood.ilike(f'%{query_text}%'),
            InfrastructureIssue.street_name.ilike(f'%{query_text}%')
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
        
        return jsonify({
            'total_issues': total_issues,
            'open_issues': open_issues,
            'closed_issues': total_issues - open_issues,
            'priority_breakdown': {priority: count for priority, count in priority_stats},
            'risk_breakdown': {risk: count for risk, count in risk_stats},
            'top_neighborhoods': [
                {'neighborhood': neighborhood, 'count': count}
                for neighborhood, count in neighborhood_stats
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500