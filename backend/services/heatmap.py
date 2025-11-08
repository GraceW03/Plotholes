def calculate_severity(complaint_type, descriptor):
    """Calculate severity score (1-5) based on issue type"""
    # High severity issues (5)
    high_severity = [
        'dangerous condition', 'cave-in', 'sinkhole', 
        'structural', 'hazardous'
    ]
    
    # Medium-high severity (4)
    medium_high = [
        'pothole', 'broken', 'cracked', 'damaged pavement',
        'missing', 'roadway'
    ]
    
    # Medium severity (3)
    medium = [
        'street condition', 'sidewalk', 'curb',
        'catch basin', 'manhole'
    ]
    
    # Check complaint type and descriptor
    text = f"{complaint_type or ''} {descriptor or ''}".lower()
    
    for term in high_severity:
        if term in text:
            return 5
    
    for term in medium_high:
        if term in text:
            return 4
    
    for term in medium:
        if term in text:
            return 3
    
    return 2 

def create_heatmap():
  '''
  Input: list of open issues
    'unique_key': row.unique_key,
    'complaint_type': row.complaint_type,
    'descriptor': row.descriptor,
    'status': row.status,
    'borough': row.borough,
    'latitude': float(row.latitude) if row.latitude else None,
    'longitude': float(row.longitude) if row.longitude else None,
    'created_date': row.created_date,
    'incident_address': row.incident_address

  '''

