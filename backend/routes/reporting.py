"""
Reporting and analytics API routes
"""

from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import and_, func, desc, text
from app import db
from models.infrastructure import InfrastructureIssue
from models.report import Report, ReportAnalytics
from models.geospatial import GeoLocation
from datetime import datetime, timedelta
import json
import os

reporting_bp = Blueprint('reporting', __name__)

@reporting_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get key statistics for the dashboard"""
    try:
        # Total issues
        total_issues = InfrastructureIssue.query.count()
        
        # Open vs closed
        open_issues = InfrastructureIssue.query.filter(
            InfrastructureIssue.case_status != 'Closed'
        ).count()
        
        closed_issues = total_issues - open_issues
        
        # Risk level breakdown
        risk_breakdown = db.session.query(
            InfrastructureIssue.risk_level,
            func.count(InfrastructureIssue.id).label('count')
        ).group_by(InfrastructureIssue.risk_level).all()
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_issues = InfrastructureIssue.query.filter(
            InfrastructureIssue.created_at >= seven_days_ago
        ).count()
        
        # High priority issues needing attention
        high_priority = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.case_status != 'Closed',
                InfrastructureIssue.risk_level.in_(['high', 'critical'])
            )
        ).count()
        
        # Top 5 neighborhoods by issue count
        top_neighborhoods = db.session.query(
            InfrastructureIssue.neighborhood,
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.neighborhood.isnot(None)
        ).group_by(
            InfrastructureIssue.neighborhood
        ).order_by(desc('count')).limit(5).all()
        
        # Average resolution time for closed issues
        closed_with_dates = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.case_status == 'Closed',
                InfrastructureIssue.open_date.isnot(None),
                InfrastructureIssue.close_date.isnot(None)
            )
        ).all()
        
        if closed_with_dates:
            resolution_times = [
                (issue.close_date - issue.open_date).days 
                for issue in closed_with_dates
            ]
            avg_resolution_days = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_days = 0
        
        # Format risk breakdown
        risk_counts = {level: 0 for level in ['low', 'medium', 'high', 'critical', 'unknown']}
        for risk, count in risk_breakdown:
            if risk in risk_counts:
                risk_counts[risk] = count
        
        return jsonify({
            'overview': {
                'total_issues': total_issues,
                'open_issues': open_issues,
                'closed_issues': closed_issues,
                'resolution_rate': round((closed_issues / total_issues * 100) if total_issues > 0 else 0, 1)
            },
            'risk_breakdown': risk_counts,
            'recent_activity': {
                'new_issues_7_days': recent_issues,
                'high_priority_open': high_priority,
                'avg_resolution_days': round(avg_resolution_days, 1)
            },
            'top_neighborhoods': [
                {'neighborhood': row.neighborhood, 'count': row.count}
                for row in top_neighborhoods
            ],
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reporting_bp.route('/real-time-updates', methods=['GET'])
def get_real_time_updates():
    """Get recent updates for real-time dashboard"""
    try:
        # Get time threshold (last hour by default)
        hours_back = request.args.get('hours_back', 1, type=int)
        threshold = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Recent issues
        recent_issues = InfrastructureIssue.query.filter(
            InfrastructureIssue.created_at >= threshold
        ).order_by(desc(InfrastructureIssue.created_at)).limit(20).all()
        
        # Recent status changes
        recent_updates = InfrastructureIssue.query.filter(
            InfrastructureIssue.updated_at >= threshold
        ).order_by(desc(InfrastructureIssue.updated_at)).limit(20).all()
        
        # Format updates
        updates = []
        
        for issue in recent_issues:
            updates.append({
                'type': 'new_issue',
                'timestamp': issue.created_at.isoformat(),
                'issue_id': issue.id,
                'case_topic': issue.case_topic,
                'location': issue.full_address or f"{issue.neighborhood or 'Unknown'}",
                'risk_level': issue.risk_level,
                'coordinates': {
                    'lat': issue.latitude,
                    'lng': issue.longitude
                } if issue.latitude and issue.longitude else None
            })
        
        for issue in recent_updates:
            if issue not in recent_issues:  # Avoid duplicates
                updates.append({
                    'type': 'status_update',
                    'timestamp': issue.updated_at.isoformat(),
                    'issue_id': issue.id,
                    'case_topic': issue.case_topic,
                    'status': issue.case_status,
                    'risk_level': issue.risk_level,
                    'location': issue.full_address or f"{issue.neighborhood or 'Unknown'}"
                })
        
        # Sort by timestamp
        updates.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'updates': updates[:30],  # Limit to 30 most recent
            'threshold': threshold.isoformat(),
            'count': len(updates)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reporting_bp.route('/predictive-alerts', methods=['GET'])
def get_predictive_alerts():
    """Get predictive maintenance alerts"""
    try:
        alerts = []
        
        # Find areas with increasing issue density
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Neighborhoods with multiple recent high-risk issues
        risk_areas = db.session.query(
            InfrastructureIssue.neighborhood,
            func.count(InfrastructureIssue.id).label('recent_count'),
            func.count(func.nullif(InfrastructureIssue.risk_level.in_(['high', 'critical']), False)).label('high_risk_count')
        ).filter(
            and_(
                InfrastructureIssue.created_at >= thirty_days_ago,
                InfrastructureIssue.neighborhood.isnot(None)
            )
        ).group_by(
            InfrastructureIssue.neighborhood
        ).having(
            func.count(InfrastructureIssue.id) >= 5
        ).order_by(desc('high_risk_count')).all()
        
        for area in risk_areas:
            if area.high_risk_count >= 3:
                severity = 'high'
                message = f"Critical infrastructure degradation detected in {area.neighborhood}"
            elif area.high_risk_count >= 2:
                severity = 'medium'
                message = f"Increasing infrastructure issues in {area.neighborhood}"
            else:
                severity = 'low'
                message = f"Monitor {area.neighborhood} for potential issues"
            
            alerts.append({
                'type': 'area_degradation',
                'severity': severity,
                'location': area.neighborhood,
                'message': message,
                'recent_issues': area.recent_count,
                'high_risk_issues': area.high_risk_count,
                'recommendation': f"Schedule preventive maintenance inspection in {area.neighborhood}"
            })
        
        # Issue types that are trending upward
        issue_trends = db.session.query(
            InfrastructureIssue.case_topic,
            func.count(InfrastructureIssue.id).label('recent_count')
        ).filter(
            InfrastructureIssue.created_at >= thirty_days_ago
        ).group_by(
            InfrastructureIssue.case_topic
        ).having(
            func.count(InfrastructureIssue.id) >= 8
        ).order_by(desc('recent_count')).limit(5).all()
        
        for trend in issue_trends:
            alerts.append({
                'type': 'trending_issue',
                'severity': 'medium',
                'issue_type': trend.case_topic,
                'message': f"Spike in {trend.case_topic} reports",
                'recent_count': trend.recent_count,
                'recommendation': f"Review and address root causes of {trend.case_topic} issues"
            })
        
        # Seasonal predictions (simplified)
        current_month = datetime.utcnow().month
        seasonal_alerts = self._get_seasonal_predictions(current_month)
        alerts.extend(seasonal_alerts)
        
        return jsonify({
            'alerts': alerts,
            'generated_at': datetime.utcnow().isoformat(),
            'prediction_horizon_days': 30
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_seasonal_predictions(month: int) -> list:
    """Get seasonal infrastructure predictions"""
    seasonal_alerts = []
    
    # Winter months - predict more pothole and road issues
    if month in [12, 1, 2, 3]:
        seasonal_alerts.append({
            'type': 'seasonal_prediction',
            'severity': 'medium',
            'message': 'Winter weather likely to increase road surface damage',
            'predicted_issues': ['Pothole formation', 'Road surface cracking'],
            'recommendation': 'Increase road surface monitoring and prepare rapid response teams'
        })
    
    # Spring - tree and vegetation issues
    elif month in [4, 5]:
        seasonal_alerts.append({
            'type': 'seasonal_prediction',
            'severity': 'low',
            'message': 'Spring growth may increase tree-related issues',
            'predicted_issues': ['Fallen branches', 'Root damage to sidewalks'],
            'recommendation': 'Schedule tree trimming and root inspection programs'
        })
    
    # Fall - leaf and drainage issues
    elif month in [10, 11]:
        seasonal_alerts.append({
            'type': 'seasonal_prediction',
            'severity': 'medium',
            'message': 'Fall season may increase drainage and flooding issues',
            'predicted_issues': ['Blocked storm drains', 'Flooding'],
            'recommendation': 'Clear storm drains and prepare for seasonal rainfall'
        })
    
    return seasonal_alerts

@reporting_bp.route('/export-data', methods=['POST'])
def export_data():
    """Export infrastructure data in various formats"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')  # json, csv, geojson
        filters = data.get('filters', {})
        
        # Build query based on filters
        query = InfrastructureIssue.query
        
        if filters.get('risk_level'):
            query = query.filter(InfrastructureIssue.risk_level == filters['risk_level'])
        
        if filters.get('neighborhood'):
            query = query.filter(InfrastructureIssue.neighborhood == filters['neighborhood'])
        
        if filters.get('case_topic'):
            query = query.filter(InfrastructureIssue.case_topic.ilike(f"%{filters['case_topic']}%"))
        
        if filters.get('date_range'):
            start_date = datetime.fromisoformat(filters['date_range']['start'])
            end_date = datetime.fromisoformat(filters['date_range']['end'])
            query = query.filter(
                and_(
                    InfrastructureIssue.created_at >= start_date,
                    InfrastructureIssue.created_at <= end_date
                )
            )
        
        issues = query.all()
        
        # Generate export data
        if export_format == 'geojson':
            export_data = {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [issue.longitude, issue.latitude]
                        } if issue.longitude and issue.latitude else None,
                        'properties': issue.to_dict()
                    }
                    for issue in issues if issue.longitude and issue.latitude
                ]
            }
        else:
            # JSON format
            export_data = {
                'export_info': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'total_records': len(issues),
                    'filters_applied': filters,
                    'format': export_format
                },
                'issues': [issue.to_dict() for issue in issues]
            }
        
        # Create temporary file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"infrastructure_export_{timestamp}.{export_format}"
        
        # For demo purposes, return the data directly
        # In production, you'd save to file and return download link
        return jsonify({
            'success': True,
            'filename': filename,
            'record_count': len(issues),
            'data': export_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reporting_bp.route('/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get comprehensive analytics summary"""
    try:
        # Time range
        days_back = request.args.get('days_back', 90, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Issue creation trends
        daily_creation = db.session.query(
            func.date(InfrastructureIssue.created_at).label('date'),
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.created_at >= start_date
        ).group_by(
            func.date(InfrastructureIssue.created_at)
        ).order_by('date').all()
        
        # Resolution trends
        daily_resolution = db.session.query(
            func.date(InfrastructureIssue.close_date).label('date'),
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            and_(
                InfrastructureIssue.close_date >= start_date,
                InfrastructureIssue.case_status == 'Closed'
            )
        ).group_by(
            func.date(InfrastructureIssue.close_date)
        ).order_by('date').all()
        
        # Risk level distribution over time
        risk_trends = db.session.query(
            func.date(InfrastructureIssue.created_at).label('date'),
            InfrastructureIssue.risk_level,
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.created_at >= start_date
        ).group_by(
            func.date(InfrastructureIssue.created_at),
            InfrastructureIssue.risk_level
        ).order_by('date').all()
        
        # Performance metrics
        total_in_period = InfrastructureIssue.query.filter(
            InfrastructureIssue.created_at >= start_date
        ).count()
        
        resolved_in_period = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.created_at >= start_date,
                InfrastructureIssue.case_status == 'Closed'
            )
        ).count()
        
        # Calculate trends
        mid_date = start_date + timedelta(days=days_back//2)
        first_half = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.created_at >= start_date,
                InfrastructureIssue.created_at < mid_date
            )
        ).count()
        
        second_half = InfrastructureIssue.query.filter(
            InfrastructureIssue.created_at >= mid_date
        ).count()
        
        trend_direction = 'increasing' if second_half > first_half else 'decreasing'
        trend_percentage = abs((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        return jsonify({
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days_back
            },
            'trends': {
                'daily_creation': [
                    {'date': str(row.date), 'count': row.count}
                    for row in daily_creation
                ],
                'daily_resolution': [
                    {'date': str(row.date), 'count': row.count}
                    for row in daily_resolution
                ],
                'risk_level_trends': [
                    {'date': str(row.date), 'risk_level': row.risk_level, 'count': row.count}
                    for row in risk_trends
                ]
            },
            'performance': {
                'total_issues': total_in_period,
                'resolved_issues': resolved_in_period,
                'resolution_rate': round((resolved_in_period / total_in_period * 100) if total_in_period > 0 else 0, 1),
                'trend_direction': trend_direction,
                'trend_percentage': round(trend_percentage, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500