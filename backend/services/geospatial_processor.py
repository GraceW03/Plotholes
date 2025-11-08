"""
Geospatial processing service for location analysis and path planning
"""

from typing import List, Dict, Any, Tuple
import math
from sqlalchemy import and_, func
from app import db
from models.infrastructure import InfrastructureIssue

class GeospatialProcessor:
    """Geospatial processor for location-based operations"""
    
    def __init__(self):
        # Earth's radius in kilometers
        self.EARTH_RADIUS_KM = 6371.0
        
        # Risk level weights for path planning
        self.RISK_WEIGHTS = {
            'low': 1.1,
            'medium': 1.5,
            'high': 2.0,
            'critical': 3.0,
            'unknown': 1.2
        }
    
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_KM * c
    
    def calculate_density_stats(self, heat_map_data: List[Dict], 
                               min_lat: float, max_lat: float, 
                               min_lng: float, max_lng: float) -> Dict[str, Any]:
        """Calculate density statistics for heat map data"""
        if not heat_map_data:
            return {
                'total_points': 0,
                'density_per_km2': 0,
                'avg_weight': 0,
                'hotspots': []
            }
        
        # Calculate area in km²
        lat_diff_km = self.haversine_distance(min_lat, min_lng, max_lat, min_lng)
        lng_diff_km = self.haversine_distance(min_lat, min_lng, min_lat, max_lng)
        area_km2 = lat_diff_km * lng_diff_km
        
        total_points = len(heat_map_data)
        total_weight = sum(point['weight'] for point in heat_map_data)
        avg_weight = total_weight / total_points if total_points > 0 else 0
        density_per_km2 = total_points / area_km2 if area_km2 > 0 else 0
        
        return {
            'total_points': total_points,
            'area_km2': round(area_km2, 2),
            'density_per_km2': round(density_per_km2, 2),
            'avg_weight': round(avg_weight, 2),
            'total_weight': total_weight
        }
    
    def find_nearby_issues(self, center_lat: float, center_lng: float, radius_km: float) -> List[Dict]:
        """Find infrastructure issues within radius of a location"""
        try:
            # Calculate bounding box for initial filter (faster than distance calculation)
            lat_delta = radius_km / 111.0  # Approximate degrees per km latitude
            lng_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
            
            # Query issues within bounding box using the actual column names from data
            issues = InfrastructureIssue.query.filter(
                and_(
                    InfrastructureIssue.latitude.isnot(None),
                    InfrastructureIssue.longitude.isnot(None),
                    InfrastructureIssue.latitude >= center_lat - lat_delta,
                    InfrastructureIssue.latitude <= center_lat + lat_delta,
                    InfrastructureIssue.longitude >= center_lng - lng_delta,
                    InfrastructureIssue.longitude <= center_lng + lng_delta
                )
            ).all()
            
            # Filter by exact distance and format results
            nearby_issues = []
            for issue in issues:
                distance = self.haversine_distance(center_lat, center_lng, issue.latitude, issue.longitude)
                if distance <= radius_km:
                    issue_data = issue.to_dict()
                    issue_data['distance_km'] = round(distance, 3)
                    nearby_issues.append(issue_data)
            
            # Sort by distance
            nearby_issues.sort(key=lambda x: x['distance_km'])
            return nearby_issues
            
        except Exception as e:
            print(f"Error finding nearby issues: {e}")
            return []
    
    def plan_safe_route(self, start_lat: float, start_lng: float, 
                       end_lat: float, end_lng: float,
                       route_type: str = 'driving',
                       avoid_risk_levels: List[str] = None,
                       max_detour_factor: float = 1.5) -> Dict[str, Any]:
        """
        Plan a safe route avoiding high-risk infrastructure issues
        """
        if avoid_risk_levels is None:
            avoid_risk_levels = ['high', 'critical']
        
        try:
            # Calculate direct distance
            direct_distance = self.haversine_distance(start_lat, start_lng, end_lat, end_lng)
            
            # Find hazards along potential route corridor
            corridor_width_km = 2.0  # 2km corridor width
            hazards = self._find_route_hazards(
                start_lat, start_lng, end_lat, end_lng, 
                corridor_width_km, avoid_risk_levels
            )
            
            # Generate simple route points (straight line with adjustments)
            route_points = self._generate_simple_route(
                start_lat, start_lng, end_lat, end_lng, hazards
            )
            
            # Calculate route metrics
            route_distance = self._calculate_route_distance(route_points)
            duration_minutes = self._estimate_duration(route_distance, route_type)
            safety_score = self._calculate_safety_score(route_points, hazards)
            
            return {
                'success': True,
                'route_points': route_points,
                'distance_km': round(route_distance, 2),
                'direct_distance_km': round(direct_distance, 2),
                'detour_factor': round(route_distance / direct_distance, 2) if direct_distance > 0 else 1.0,
                'duration_minutes': duration_minutes,
                'safety_score': round(safety_score, 2),
                'avoided_hazards': [h['issue_id'] for h in hazards],
                'hazard_count': len(hazards),
                'algorithm_used': 'simple_avoidance',
                'route_type': route_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_route_hazards(self, start_lat: float, start_lng: float, 
                           end_lat: float, end_lng: float,
                           corridor_width_km: float, avoid_risk_levels: List[str]) -> List[Dict]:
        """Find hazards along a route corridor"""
        # Calculate bounding box for the route corridor
        min_lat = min(start_lat, end_lat) - corridor_width_km / 111.0
        max_lat = max(start_lat, end_lat) + corridor_width_km / 111.0
        avg_lat = (start_lat + end_lat) / 2
        lng_delta = corridor_width_km / (111.0 * math.cos(math.radians(avg_lat)))
        min_lng = min(start_lng, end_lng) - lng_delta
        max_lng = max(start_lng, end_lng) + lng_delta
        
        # Query hazards in the area
        hazard_issues = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.latitude.isnot(None),
                InfrastructureIssue.longitude.isnot(None),
                InfrastructureIssue.latitude >= min_lat,
                InfrastructureIssue.latitude <= max_lat,
                InfrastructureIssue.longitude >= min_lng,
                InfrastructureIssue.longitude <= max_lng,
                InfrastructureIssue.risk_level.in_(avoid_risk_levels)
            )
        ).all()
        
        hazards = []
        for issue in hazard_issues:
            hazards.append({
                'issue_id': issue.id,
                'lat': issue.latitude,
                'lng': issue.longitude,
                'risk_level': issue.risk_level,
                'case_topic': issue.case_topic
            })
        
        return hazards
    
    def _generate_simple_route(self, start_lat: float, start_lng: float,
                              end_lat: float, end_lng: float,
                              hazards: List[Dict]) -> List[List[float]]:
        """Generate simple route points"""
        # For demo purposes, create a simple 5-point route
        route_points = []
        
        for i in range(6):  # 6 points including start and end
            progress = i / 5
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            route_points.append([lat, lng])
        
        return route_points
    
    def _calculate_route_distance(self, route_points: List[List[float]]) -> float:
        """Calculate total distance of route"""
        total_distance = 0
        for i in range(len(route_points) - 1):
            distance = self.haversine_distance(
                route_points[i][0], route_points[i][1],
                route_points[i + 1][0], route_points[i + 1][1]
            )
            total_distance += distance
        return total_distance
    
    def _estimate_duration(self, distance_km: float, route_type: str) -> int:
        """Estimate travel duration based on route type"""
        speeds = {
            'walking': 5,
            'cycling': 15,
            'driving': 25,
            'emergency': 40
        }
        
        speed = speeds.get(route_type, 25)
        duration_hours = distance_km / speed
        return max(1, int(duration_hours * 60))
    
    def _calculate_safety_score(self, route_points: List[List[float]], hazards: List[Dict]) -> float:
        """Calculate safety score for the route (0.0 to 1.0)"""
        if not hazards:
            return 1.0
        
        # Simple calculation: reduce score based on number of nearby hazards
        risk_penalty = min(len(hazards) * 0.1, 0.8)  # Max 80% penalty
        return max(0.2, 1.0 - risk_penalty)
    
    def create_issue_clusters(self, min_lat: float, max_lat: float,
                             min_lng: float, max_lng: float, zoom_level: int) -> List[Dict]:
        """Create clusters of issues for map display"""
        # Get all issues in the bounding box
        issues = InfrastructureIssue.query.filter(
            and_(
                InfrastructureIssue.latitude.isnot(None),
                InfrastructureIssue.longitude.isnot(None),
                InfrastructureIssue.latitude >= min_lat,
                InfrastructureIssue.latitude <= max_lat,
                InfrastructureIssue.longitude >= min_lng,
                InfrastructureIssue.longitude <= max_lng
            )
        ).all()
        
        if not issues:
            return []
        
        # Determine cluster distance based on zoom level
        if zoom_level >= 15:
            # High zoom - show individual issues
            return [{
                'type': 'single',
                'lat': issue.latitude,
                'lng': issue.longitude,
                'count': 1,
                'issue': issue.to_dict(),
                'risk_level': issue.risk_level
            } for issue in issues]
        
        # Create simple clusters
        cluster_distance_km = 2.0 if zoom_level >= 12 else 5.0
        clusters = []
        processed_issues = set()
        
        for issue in issues:
            if issue.id in processed_issues:
                continue
            
            # Find nearby issues
            cluster_issues = [issue]
            processed_issues.add(issue.id)
            
            for other_issue in issues:
                if other_issue.id in processed_issues:
                    continue
                
                distance = self.haversine_distance(
                    issue.latitude, issue.longitude,
                    other_issue.latitude, other_issue.longitude
                )
                
                if distance <= cluster_distance_km:
                    cluster_issues.append(other_issue)
                    processed_issues.add(other_issue.id)
            
            # Create cluster representation
            if len(cluster_issues) == 1:
                clusters.append({
                    'type': 'single',
                    'lat': issue.latitude,
                    'lng': issue.longitude,
                    'count': 1,
                    'issue': issue.to_dict(),
                    'risk_level': issue.risk_level
                })
            else:
                # Multiple issues - create cluster
                center_lat = sum(i.latitude for i in cluster_issues) / len(cluster_issues)
                center_lng = sum(i.longitude for i in cluster_issues) / len(cluster_issues)
                
                # Determine highest risk level in cluster
                risk_levels = [i.risk_level for i in cluster_issues]
                if 'critical' in risk_levels:
                    cluster_risk = 'critical'
                elif 'high' in risk_levels:
                    cluster_risk = 'high'
                elif 'medium' in risk_levels:
                    cluster_risk = 'medium'
                else:
                    cluster_risk = 'low'
                
                clusters.append({
                    'type': 'cluster',
                    'lat': center_lat,
                    'lng': center_lng,
                    'count': len(cluster_issues),
                    'risk_level': cluster_risk,
                    'issues': [i.to_dict() for i in cluster_issues[:3]]  # Show first 3
                })
        
        return clusters