"""
Risk assessment service for infrastructure issues
"""

from typing import Dict, Any, List
import math
from datetime import datetime, timedelta
from models.infrastructure import InfrastructureIssue
from app import db
from sqlalchemy import and_, func

class RiskAssessor:
    """Risk assessor for infrastructure issues"""
    
    def __init__(self):
        # Risk scoring weights
        self.ISSUE_TYPE_WEIGHTS = {
            'pothole': 0.8,
            'street light outage': 0.6,
            'street light knockdown': 0.9,
            'fallen tree or branches': 0.7,
            'flooding': 0.9,
            'lane divider': 0.4,
            'pruning request': 0.3,
            'planting request': 0.2,
            'tree or stump removal': 0.5,
            'wild animal issue': 0.3,
            'domestic animal issue': 0.2,
            'lost pet': 0.1
        }
        
        # Neighborhood risk multipliers (based on traffic density, population)
        self.NEIGHBORHOOD_MULTIPLIERS = {
            'downtown': 1.3,
            'back bay': 1.2,
            'south end': 1.2,
            'north end': 1.1,
            'beacon hill': 1.1,
            'fenway': 1.2,
            'allston': 1.0,
            'brighton': 1.0,
            'cambridge': 1.2,
            'somerville': 1.1
        }
        
        # Time-based urgency factors
        self.URGENCY_FACTORS = {
            'overdue': 1.4,
            'ontime': 1.0,
            'early': 0.9
        }
    
    def assess_issue(self, issue: InfrastructureIssue) -> Dict[str, Any]:
        """
        Comprehensive risk assessment for an infrastructure issue
        
        Args:
            issue: InfrastructureIssue object
            
        Returns:
            Dictionary containing risk assessment results
        """
        try:
            # Base risk score from issue type
            base_risk = self._calculate_base_risk(issue)
            
            # Location-based risk factors
            location_risk = self._calculate_location_risk(issue)
            
            # Time-based urgency
            time_urgency = self._calculate_time_urgency(issue)
            
            # Severity from CV analysis if available
            cv_severity = self._extract_cv_severity(issue)
            
            # Historical context
            historical_context = self._calculate_historical_context(issue)
            
            # Combine all factors
            risk_components = {
                'base_risk': base_risk,
                'location_risk': location_risk,
                'time_urgency': time_urgency,
                'cv_severity': cv_severity,
                'historical_context': historical_context
            }
            
            # Calculate final risk score (0.0 to 1.0)
            final_score = self._combine_risk_factors(risk_components)
            
            # Determine risk level
            risk_level = self._score_to_risk_level(final_score)
            
            # Calculate confidence based on available data
            confidence = self._calculate_confidence(issue, risk_components)
            
            # Generate severity factors list
            severity_factors = self._generate_severity_factors(issue, risk_components)
            
            # Estimate impact and costs
            impact_radius = self._estimate_impact_radius(issue, final_score)
            repair_cost = self._estimate_repair_cost(issue, final_score)
            priority_score = self._calculate_priority_score(final_score, time_urgency)
            
            return {
                'risk_level': risk_level,
                'confidence_score': round(confidence, 3),
                'assessment_type': 'automated_ml',
                'severity_factors': severity_factors,
                'impact_radius': impact_radius,
                'estimated_repair_cost': repair_cost,
                'priority_score': round(priority_score, 2),
                'model_version': '1.0.0',
                'model_confidence': round(final_score, 3),
                'risk_components': {k: round(v, 3) for k, v in risk_components.items()},
                'assessment_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback assessment
            return {
                'risk_level': 'medium',
                'confidence_score': 0.3,
                'assessment_type': 'fallback',
                'severity_factors': [f'Assessment error: {str(e)}'],
                'error': str(e)
            }
    
    def _calculate_base_risk(self, issue: InfrastructureIssue) -> float:
        """Calculate base risk from issue type"""
        case_topic_lower = issue.case_topic.lower() if issue.case_topic else ''
        
        # Check for keyword matches
        for keyword, weight in self.ISSUE_TYPE_WEIGHTS.items():
            if keyword in case_topic_lower:
                return weight
        
        # Default risk for unknown types
        return 0.5
    
    def _calculate_location_risk(self, issue: InfrastructureIssue) -> float:
        """Calculate risk based on location factors"""
        location_risk = 0.5  # Base location risk
        
        # Neighborhood multiplier
        if issue.neighborhood:
            neighborhood_lower = issue.neighborhood.lower()
            multiplier = self.NEIGHBORHOOD_MULTIPLIERS.get(neighborhood_lower, 1.0)
            location_risk *= multiplier
        
        # High-traffic areas get higher risk
        if issue.full_address:
            address_lower = issue.full_address.lower()
            high_traffic_keywords = ['main', 'central', 'broadway', 'washington', 'commonwealth']
            if any(keyword in address_lower for keyword in high_traffic_keywords):
                location_risk += 0.2
        
        return min(location_risk, 1.0)
    
    def _calculate_time_urgency(self, issue: InfrastructureIssue) -> float:
        """Calculate urgency based on time factors"""
        if not issue.open_date:
            return 0.5
        
        # Calculate days since reported
        days_open = (datetime.utcnow() - issue.open_date).days
        
        # Urgency increases with time
        if days_open > 30:
            time_urgency = 1.0  # Very urgent
        elif days_open > 14:
            time_urgency = 0.8  # Urgent
        elif days_open > 7:
            time_urgency = 0.6  # Moderate urgency
        else:
            time_urgency = 0.4  # Low urgency
        
        return time_urgency
    
    def _extract_cv_severity(self, issue: InfrastructureIssue) -> float:
        """Extract severity from computer vision analysis"""
        if not issue.confidence_score:
            return 0.5
        
        # Use existing CV confidence as severity indicator
        return min(issue.confidence_score, 1.0)
    
    def _calculate_historical_context(self, issue: InfrastructureIssue) -> float:
        """Calculate risk based on historical issues in the area"""
        if not issue.latitude or not issue.longitude:
            return 0.5
        
        try:
            # Count nearby issues within 0.5km radius in the last 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            
            # Simple distance calculation (approximate)
            lat_delta = 0.5 / 111.0  # Rough km to degrees conversion
            lng_delta = 0.5 / (111.0 * math.cos(math.radians(issue.latitude)))
            
            nearby_count = InfrastructureIssue.query.filter(
                and_(
                    InfrastructureIssue.id != issue.id,
                    InfrastructureIssue.latitude.isnot(None),
                    InfrastructureIssue.longitude.isnot(None),
                    InfrastructureIssue.latitude >= issue.latitude - lat_delta,
                    InfrastructureIssue.latitude <= issue.latitude + lat_delta,
                    InfrastructureIssue.longitude >= issue.longitude - lng_delta,
                    InfrastructureIssue.longitude <= issue.longitude + lng_delta,
                    InfrastructureIssue.created_at >= six_months_ago
                )
            ).count()
            
            # More nearby issues = higher risk
            if nearby_count >= 10:
                return 0.9
            elif nearby_count >= 5:
                return 0.7
            elif nearby_count >= 2:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _combine_risk_factors(self, components: Dict[str, float]) -> float:
        """Combine risk factors into final score"""
        # Weighted combination
        weights = {
            'base_risk': 0.3,
            'location_risk': 0.2,
            'time_urgency': 0.2,
            'cv_severity': 0.2,
            'historical_context': 0.1
        }
        
        final_score = 0.0
        for factor, weight in weights.items():
            final_score += components.get(factor, 0.5) * weight
        
        return min(final_score, 1.0)
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, issue: InfrastructureIssue, components: Dict[str, float]) -> float:
        """Calculate confidence in the assessment"""
        confidence_factors = []
        
        # Photo analysis available
        if issue.photos.count() > 0:
            confidence_factors.append(0.3)
        
        # Location data available
        if issue.latitude and issue.longitude:
            confidence_factors.append(0.2)
        
        # Detailed description available
        if issue.description and len(issue.description) > 20:
            confidence_factors.append(0.2)
        
        # Known issue type
        if issue.case_topic and issue.case_topic.lower() in self.ISSUE_TYPE_WEIGHTS:
            confidence_factors.append(0.2)
        
        # Time factor
        if issue.open_date:
            confidence_factors.append(0.1)
        
        return min(sum(confidence_factors), 1.0)
    
    def _generate_severity_factors(self, issue: InfrastructureIssue, components: Dict[str, float]) -> List[str]:
        """Generate list of contributing severity factors"""
        factors = []
        
        # Issue type factor
        if components['base_risk'] > 0.7:
            factors.append(f"High-risk issue type: {issue.case_topic}")
        
        # Location factor
        if components['location_risk'] > 0.7:
            factors.append(f"High-traffic location: {issue.neighborhood or 'Unknown area'}")
        
        # Time urgency
        if components['time_urgency'] > 0.7:
            if issue.open_date:
                days_open = (datetime.utcnow() - issue.open_date).days
                factors.append(f"Long-standing issue: {days_open} days old")
            else:
                factors.append("Time urgency detected")
        
        # CV analysis
        if components['cv_severity'] > 0.7:
            factors.append("Computer vision analysis indicates high severity")
        
        # Historical context
        if components['historical_context'] > 0.7:
            factors.append("Multiple issues reported in this area recently")
        
        # Case status
        if issue.case_status == 'Overdue':
            factors.append("Overdue for resolution")
        
        return factors or ["Standard risk assessment"]
    
    def _estimate_impact_radius(self, issue: InfrastructureIssue, risk_score: float) -> float:
        """Estimate impact radius in meters"""
        base_radius = {
            'pothole': 50,
            'street light': 200,
            'flooding': 500,
            'fallen tree': 100,
            'default': 75
        }
        
        # Get base radius for issue type
        case_topic_lower = issue.case_topic.lower() if issue.case_topic else ''
        radius = base_radius['default']
        
        for keyword, base_r in base_radius.items():
            if keyword in case_topic_lower:
                radius = base_r
                break
        
        # Scale by risk score
        return radius * (0.5 + risk_score * 0.5)
    
    def _estimate_repair_cost(self, issue: InfrastructureIssue, risk_score: float) -> float:
        """Estimate repair cost in USD"""
        base_costs = {
            'pothole': 150,
            'street light': 300,
            'flooding': 1000,
            'fallen tree': 500,
            'pruning': 200,
            'default': 250
        }
        
        # Get base cost for issue type
        case_topic_lower = issue.case_topic.lower() if issue.case_topic else ''
        cost = base_costs['default']
        
        for keyword, base_c in base_costs.items():
            if keyword in case_topic_lower:
                cost = base_c
                break
        
        # Scale by risk score (higher risk = higher cost due to urgency/complexity)
        return cost * (0.8 + risk_score * 0.4)
    
    def _calculate_priority_score(self, risk_score: float, time_urgency: float) -> float:
        """Calculate priority score (0-100)"""
        # Combine risk and urgency for priority
        priority = (risk_score * 0.7 + time_urgency * 0.3) * 100
        return min(priority, 100)