"""
AI Analysis and risk assessment API routes
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_, func, desc
from app import db
from models.infrastructure import InfrastructureIssue, RiskAssessment
from services.cv_analyzer import CVAnalyzer
from services.risk_assessor import RiskAssessor
from datetime import datetime, timedelta

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/risk-assessment', methods=['POST'])
def create_risk_assessment():
    """Create a new risk assessment for an issue"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'issue_id' not in data:
            return jsonify({'error': 'issue_id is required'}), 400
        
        issue = InfrastructureIssue.query.get_or_404(data['issue_id'])
        
        # Use risk assessor service
        risk_assessor = RiskAssessor()
        assessment_result = risk_assessor.assess_issue(issue)
        
        # Create risk assessment record
        risk_assessment = RiskAssessment(
            issue_id=issue.id,
            risk_level=assessment_result['risk_level'],
            confidence_score=assessment_result['confidence_score'],
            assessment_type=assessment_result['assessment_type'],
            severity_factors=assessment_result['severity_factors'],
            impact_radius=assessment_result.get('impact_radius'),
            estimated_repair_cost=assessment_result.get('estimated_repair_cost'),
            priority_score=assessment_result.get('priority_score'),
            model_version=assessment_result.get('model_version'),
            model_confidence=assessment_result.get('model_confidence')
        )
        
        db.session.add(risk_assessment)
        
        # Update the issue with new risk level
        issue.risk_level = assessment_result['risk_level']
        issue.confidence_score = assessment_result['confidence_score']
        
        db.session.commit()
        
        return jsonify({
            'risk_assessment': risk_assessment.to_dict(),
            'updated_issue': issue.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/batch-risk-assessment', methods=['POST'])
def batch_risk_assessment():
    """Run risk assessment on multiple issues"""
    try:
        data = request.get_json()
        issue_ids = data.get('issue_ids', [])
        
        if not issue_ids:
            return jsonify({'error': 'issue_ids array is required'}), 400
        
        # Limit batch size
        if len(issue_ids) > 100:
            return jsonify({'error': 'Maximum 100 issues per batch'}), 400
        
        risk_assessor = RiskAssessor()
        results = []
        errors = []
        
        for issue_id in issue_ids:
            try:
                issue = InfrastructureIssue.query.get(issue_id)
                if not issue:
                    errors.append(f"Issue {issue_id} not found")
                    continue
                
                # Run assessment
                assessment_result = risk_assessor.assess_issue(issue)
                
                # Create risk assessment record
                risk_assessment = RiskAssessment(
                    issue_id=issue.id,
                    risk_level=assessment_result['risk_level'],
                    confidence_score=assessment_result['confidence_score'],
                    assessment_type=assessment_result['assessment_type'],
                    severity_factors=assessment_result['severity_factors'],
                    impact_radius=assessment_result.get('impact_radius'),
                    priority_score=assessment_result.get('priority_score')
                )
                
                db.session.add(risk_assessment)
                
                # Update issue
                issue.risk_level = assessment_result['risk_level']
                issue.confidence_score = assessment_result['confidence_score']
                
                results.append({
                    'issue_id': issue_id,
                    'risk_level': assessment_result['risk_level'],
                    'confidence_score': assessment_result['confidence_score']
                })
                
            except Exception as e:
                errors.append(f"Error processing issue {issue_id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'processed_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/cv-analysis/<issue_id>', methods=['POST'])
def run_cv_analysis(issue_id):
    """Run computer vision analysis on issue photos"""
    try:
        issue = InfrastructureIssue.query.get_or_404(issue_id)
        
        if not issue.photos.count():
            return jsonify({'error': 'No photos found for this issue'}), 400
        
        cv_analyzer = CVAnalyzer()
        analysis_results = []
        
        for photo in issue.photos:
            try:
                result = cv_analyzer.analyze_image(photo.file_path)
                
                # Update photo with analysis results
                photo.analysis_results = result
                photo.processed = True
                photo.processed_at = datetime.utcnow()
                
                analysis_results.append({
                    'photo_id': photo.id,
                    'analysis': result
                })
                
            except Exception as e:
                analysis_results.append({
                    'photo_id': photo.id,
                    'error': str(e)
                })
        
        # Update issue risk level based on CV analysis
        if analysis_results:
            # Take the highest risk level from all photos
            risk_levels = []
            confidences = []
            
            for result in analysis_results:
                if 'analysis' in result:
                    risk_levels.append(result['analysis'].get('risk_level', 'unknown'))
                    confidences.append(result['analysis'].get('confidence', 0.0))
            
            if risk_levels:
                # Determine highest risk
                risk_hierarchy = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
                max_risk = max(risk_levels, key=lambda x: risk_hierarchy.get(x, 0))
                avg_confidence = sum(confidences) / len(confidences)
                
                issue.risk_level = max_risk
                issue.confidence_score = avg_confidence
        
        db.session.commit()
        
        return jsonify({
            'issue_id': issue_id,
            'photos_analyzed': len(analysis_results),
            'analysis_results': analysis_results,
            'updated_issue_risk': issue.risk_level,
            'updated_confidence': issue.confidence_score
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/trends', methods=['GET'])
def get_trends():
    """Get trend analysis of infrastructure issues"""
    try:
        # Get time range
        days_back = request.args.get('days_back', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Issues created over time
        daily_issues = db.session.query(
            func.date(InfrastructureIssue.created_at).label('date'),
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.created_at >= start_date
        ).group_by(
            func.date(InfrastructureIssue.created_at)
        ).order_by('date').all()
        
        # Issues by risk level over time
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
        
        # Issue types trending
        type_trends = db.session.query(
            InfrastructureIssue.case_topic,
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.created_at >= start_date
        ).group_by(
            InfrastructureIssue.case_topic
        ).order_by(desc('count')).limit(10).all()
        
        # Resolution rate
        total_issues = InfrastructureIssue.query.filter(
            InfrastructureIssue.created_at >= start_date
        ).count()
        
        closed_issues = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.created_at >= start_date,
                InfrastructureIssue.case_status == 'Closed'
            )
        ).count()
        
        resolution_rate = (closed_issues / total_issues * 100) if total_issues > 0 else 0
        
        return jsonify({
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days_back
            },
            'daily_issues': [
                {'date': str(row.date), 'count': row.count}
                for row in daily_issues
            ],
            'risk_level_trends': [
                {'date': str(row.date), 'risk_level': row.risk_level, 'count': row.count}
                for row in risk_trends
            ],
            'top_issue_types': [
                {'case_topic': row.case_topic, 'count': row.count}
                for row in type_trends
            ],
            'summary': {
                'total_issues': total_issues,
                'closed_issues': closed_issues,
                'resolution_rate_percent': round(resolution_rate, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/predictive-maintenance', methods=['GET'])
def predictive_maintenance():
    """Get predictive maintenance recommendations"""
    try:
        # Get areas with high issue density
        high_risk_areas = db.session.query(
            InfrastructureIssue.neighborhood,
            func.count(InfrastructureIssue.id).label('issue_count'),
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
            and_(
                InfrastructureIssue.neighborhood.isnot(None),
                InfrastructureIssue.case_status != 'Closed'
            )
        ).group_by(
            InfrastructureIssue.neighborhood
        ).having(
            func.count(InfrastructureIssue.id) >= 3
        ).order_by(
            desc('avg_risk_score')
        ).limit(10).all()
        
        # Get issue types that need attention
        priority_types = db.session.query(
            InfrastructureIssue.case_topic,
            func.count(InfrastructureIssue.id).label('open_count'),
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
            InfrastructureIssue.case_status != 'Closed'
        ).group_by(
            InfrastructureIssue.case_topic
        ).order_by(
            desc('avg_risk_score')
        ).limit(10).all()
        
        # Generate recommendations
        recommendations = []
        
        for area in high_risk_areas:
            if area.avg_risk_score >= 3:
                urgency = 'high'
            elif area.avg_risk_score >= 2:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            recommendations.append({
                'type': 'area_maintenance',
                'location': area.neighborhood,
                'urgency': urgency,
                'issue_count': area.issue_count,
                'avg_risk_score': round(area.avg_risk_score, 2),
                'recommendation': f"Schedule comprehensive maintenance in {area.neighborhood} - {area.issue_count} open issues with average risk score {area.avg_risk_score:.1f}"
            })
        
        for issue_type in priority_types:
            if issue_type.avg_risk_score >= 3:
                recommendations.append({
                    'type': 'issue_type_focus',
                    'issue_type': issue_type.case_topic,
                    'urgency': 'high',
                    'open_count': issue_type.open_count,
                    'avg_risk_score': round(issue_type.avg_risk_score, 2),
                    'recommendation': f"Prioritize {issue_type.case_topic} repairs - {issue_type.open_count} open cases with high risk"
                })
        
        return jsonify({
            'high_risk_areas': [
                {
                    'neighborhood': area.neighborhood,
                    'issue_count': area.issue_count,
                    'avg_risk_score': round(area.avg_risk_score, 2)
                }
                for area in high_risk_areas
            ],
            'priority_issue_types': [
                {
                    'case_topic': pt.case_topic,
                    'open_count': pt.open_count,
                    'avg_risk_score': round(pt.avg_risk_score, 2)
                }
                for pt in priority_types
            ],
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/risk-distribution', methods=['GET'])
def get_risk_distribution():
    """Get distribution of risk levels across the city"""
    try:
        # Overall risk distribution
        risk_distribution = db.session.query(
            InfrastructureIssue.risk_level,
            func.count(InfrastructureIssue.id).label('count')
        ).group_by(
            InfrastructureIssue.risk_level
        ).all()
        
        # Risk distribution by neighborhood
        neighborhood_risk = db.session.query(
            InfrastructureIssue.neighborhood,
            InfrastructureIssue.risk_level,
            func.count(InfrastructureIssue.id).label('count')
        ).filter(
            InfrastructureIssue.neighborhood.isnot(None)
        ).group_by(
            InfrastructureIssue.neighborhood,
            InfrastructureIssue.risk_level
        ).all()
        
        # Risk distribution by issue type
        type_risk = db.session.query(
            InfrastructureIssue.case_topic,
            InfrastructureIssue.risk_level,
            func.count(InfrastructureIssue.id).label('count')
        ).group_by(
            InfrastructureIssue.case_topic,
            InfrastructureIssue.risk_level
        ).all()
        
        # Format results
        overall_risk = {risk: count for risk, count in risk_distribution}
        
        # Group neighborhood data
        neighborhood_data = {}
        for row in neighborhood_risk:
            if row.neighborhood not in neighborhood_data:
                neighborhood_data[row.neighborhood] = {}
            neighborhood_data[row.neighborhood][row.risk_level] = row.count
        
        # Group type data
        type_data = {}
        for row in type_risk:
            if row.case_topic not in type_data:
                type_data[row.case_topic] = {}
            type_data[row.case_topic][row.risk_level] = row.count
        
        return jsonify({
            'overall_distribution': overall_risk,
            'by_neighborhood': neighborhood_data,
            'by_issue_type': type_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500