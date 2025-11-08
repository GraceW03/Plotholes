"""
Data importer for NYC 311 and other infrastructure data sources
"""

import pandas as pd
import csv
from datetime import datetime
from app import db
from models.infrastructure import InfrastructureIssue
from models.user import User
from geoalchemy2 import WKTElement
import uuid

class DataImporter:
    """Import infrastructure data from various sources"""
    
    def __init__(self):
        self.risk_level_mapping = {
            'Street Light Outage': 'medium',
            'Street Light Knockdown': 'high',
            'Pothole': 'high',
            'Fallen Tree or Branches': 'high',
            'Pruning Request': 'low',
            'Planting Request': 'low',
            'Tree or Stump Removal': 'medium',
            'Wild Animal Issue': 'low',
            'Domestic Animal Issue': 'low',
            'Lost Pet': 'low',
            'Lane Divider': 'medium'
        }
    
    def import_nyc_311_csv(self, csv_file_path: str) -> dict:
        """
        Import NYC 311 data from CSV file
        
        Args:
            csv_file_path: Path to the filtered_data.csv file
            
        Returns:
            Dictionary with import statistics
        """
        stats = {
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            stats['total_rows'] = len(df)
            
            print(f"Starting import of {stats['total_rows']} records...")
            
            # Create a default user for imported data
            default_user = self._get_or_create_default_user()
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip if essential data is missing
                    if pd.isna(row.get('case_topic')) or pd.isna(row.get('service_name')):
                        stats['skipped'] += 1
                        continue
                    
                    # Check if issue already exists
                    existing_issue = None
                    if not pd.isna(row.get('case_id')):
                        existing_issue = InfrastructureIssue.query.filter_by(
                            case_id=str(row['case_id'])
                        ).first()
                    
                    if existing_issue:
                        stats['skipped'] += 1
                        continue
                    
                    # Parse dates
                    open_date = self._parse_date(row.get('open_date'))
                    close_date = self._parse_date(row.get('close_date'))
                    
                    # Determine risk level based on case topic
                    risk_level = self._determine_risk_level(row.get('case_topic'))
                    
                    # Create issue record
                    issue = InfrastructureIssue(
                        case_id=str(row['case_id']) if not pd.isna(row.get('case_id')) else None,
                        case_topic=str(row['case_topic']),
                        service_name=str(row['service_name']),
                        case_status=str(row.get('case_status', 'Open')),
                        full_address=str(row['full_address']) if not pd.isna(row.get('full_address')) else None,
                        street_number=str(row['street_number']) if not pd.isna(row.get('street_number')) else None,
                        street_name=str(row['street_name']) if not pd.isna(row.get('street_name')) else None,
                        zip_code=str(row['zip_code']) if not pd.isna(row.get('zip_code')) else None,
                        neighborhood=str(row['neighborhood']) if not pd.isna(row.get('neighborhood')) else None,
                        longitude=float(row['longitude']) if not pd.isna(row.get('longitude')) else None,
                        latitude=float(row['latitude']) if not pd.isna(row.get('latitude')) else None,
                        open_date=open_date,
                        close_date=close_date,
                        risk_level=risk_level,
                        confidence_score=0.7,  # Default confidence for imported data
                        reporter_id=default_user.id,
                        created_at=open_date or datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    # Set geometry if coordinates are available
                    if issue.longitude and issue.latitude:
                        issue.location = WKTElement(f'POINT({issue.longitude} {issue.latitude})', srid=4326)
                    
                    db.session.add(issue)
                    stats['imported'] += 1
                    
                    # Commit in batches of 100
                    if stats['imported'] % 100 == 0:
                        db.session.commit()
                        print(f"Imported {stats['imported']} records...")
                
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {index}: {str(e)}")
                    print(f"Error importing row {index}: {str(e)}")
                    continue
            
            # Final commit
            db.session.commit()
            print(f"Import completed! Imported: {stats['imported']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
            
        except Exception as e:
            db.session.rollback()
            stats['errors'] += 1
            stats['error_details'].append(f"File processing error: {str(e)}")
            print(f"Error processing file: {str(e)}")
        
        return stats
    
    def _get_or_create_default_user(self) -> User:
        """Get or create default user for imported data"""
        default_user = User.query.filter_by(username='nyc_311_import').first()
        
        if not default_user:
            default_user = User(
                username='nyc_311_import',
                email='import@nyc311.gov',
                first_name='NYC',
                last_name='311 System'
            )
            db.session.add(default_user)
            db.session.commit()
        
        return default_user
    
    def _parse_date(self, date_str) -> datetime:
        """Parse date string to datetime object"""
        if pd.isna(date_str):
            return None
        
        try:
            # Try different date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S.%f%z',
                '%Y-%m-%d %H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            date_str = str(date_str).strip()
            
            for fmt in date_formats:
                try:
                    # Remove timezone info if present for simpler parsing
                    if '+' in date_str:
                        date_str = date_str.split('+')[0]
                    
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format works, return None
            return None
            
        except Exception:
            return None
    
    def _determine_risk_level(self, case_topic: str) -> str:
        """Determine risk level based on case topic"""
        if not case_topic:
            return 'unknown'
        
        case_topic_lower = case_topic.lower()
        
        # Check for specific keywords
        if any(keyword in case_topic_lower for keyword in ['knockdown', 'fallen', 'flooding', 'emergency']):
            return 'high'
        elif any(keyword in case_topic_lower for keyword in ['outage', 'pothole', 'broken', 'damage']):
            return 'medium'
        elif any(keyword in case_topic_lower for keyword in ['pruning', 'planting', 'animal', 'pet']):
            return 'low'
        else:
            return 'medium'  # Default for unknown types
    
    def get_import_stats(self) -> dict:
        """Get statistics about imported data"""
        try:
            total_issues = InfrastructureIssue.query.count()
            
            # Issues by source
            imported_issues = InfrastructureIssue.query.filter(
                InfrastructureIssue.case_id.isnot(None)
            ).count()
            
            user_reported = total_issues - imported_issues
            
            # Risk level distribution
            risk_stats = db.session.query(
                InfrastructureIssue.risk_level,
                db.func.count(InfrastructureIssue.id)
            ).group_by(InfrastructureIssue.risk_level).all()
            
            # Geographic distribution
            geo_stats = db.session.query(
                InfrastructureIssue.neighborhood,
                db.func.count(InfrastructureIssue.id)
            ).filter(
                InfrastructureIssue.neighborhood.isnot(None)
            ).group_by(
                InfrastructureIssue.neighborhood
            ).order_by(db.func.count(InfrastructureIssue.id).desc()).limit(10).all()
            
            return {
                'total_issues': total_issues,
                'imported_issues': imported_issues,
                'user_reported_issues': user_reported,
                'risk_distribution': {risk: count for risk, count in risk_stats},
                'top_neighborhoods': [
                    {'neighborhood': neighborhood, 'count': count}
                    for neighborhood, count in geo_stats
                ],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def clear_imported_data(self) -> dict:
        """Clear all imported data (use with caution!)"""
        try:
            # Delete issues with case_id (imported from 311)
            deleted_count = InfrastructureIssue.query.filter(
                InfrastructureIssue.case_id.isnot(None)
            ).delete()
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'Cleared {deleted_count} imported issues'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }