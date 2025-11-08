# Plotholes Backend API Documentation

## Base URL
```
http://localhost:5000/api
```

## Demo Workflow Endpoints

### 1. Photo Upload → AI Analysis
```http
POST /photos/upload
Content-Type: multipart/form-data

Form Data:
- photo: (file) Image file
- issue_id: (optional) Associate with existing issue

Response:
{
  "photo": { ... },
  "analysis_results": {
    "risk_level": "high",
    "confidence": 0.87,
    "detected_objects": [
      {
        "class": "pothole",
        "confidence": 0.87,
        "severity": "medium",
        "depth_cm": 8
      }
    ],
    "severity_analysis": "Medium-depth pothole detected with high confidence"
  },
  "demo_note": "Mock analysis for demonstration"
}
```

### 2. Live Map Updates
```http
GET /reporting/real-time-updates?hours_back=1

Response:
{
  "updates": [
    {
      "type": "new_issue",
      "timestamp": "2025-11-08T04:30:00Z",
      "issue_id": "uuid",
      "case_topic": "Pothole",
      "location": "123 Main St, Boston",
      "risk_level": "high",
      "coordinates": { "lat": 42.3601, "lng": -71.0589 }
    }
  ]
}
```

### 3. Heat Map Data
```http
GET /geospatial/heat-map?risk_level=high&days_back=30

Response:
{
  "heat_map_data": [
    {
      "lat": 42.3601,
      "lng": -71.0589,
      "weight": 3,
      "issue_id": "uuid",
      "case_topic": "Pothole",
      "risk_level": "high",
      "neighborhood": "Manhattan"
    }
  ],
  "total_points": 150,
  "density_stats": { ... }
}
```

### 4. Predictive Mode
```http
GET /analysis/predictive-maintenance

Response:
{
  "alerts": [
    {
      "type": "area_degradation",
      "severity": "high",
      "location": "Back Bay",
      "message": "Critical infrastructure degradation detected",
      "recent_issues": 12,
      "high_risk_issues": 5,
      "recommendation": "Schedule preventive maintenance inspection"
    }
  ]
}
```

### 5. Safe Path Planning
```http
POST /geospatial/path-planning
Content-Type: application/json

{
  "start_lat": 42.3601,
  "start_lng": -71.0589,
  "end_lat": 42.3501,
  "end_lng": -71.0489,
  "route_type": "driving",
  "avoid_risk_levels": ["high", "critical"]
}

Response:
{
  "success": true,
  "route_points": [[lat, lng], ...],
  "distance_km": 2.5,
  "duration_minutes": 8,
  "safety_score": 0.85,
  "avoided_hazards": ["issue-uuid-1", "issue-uuid-2"],
  "hazard_count": 2
}
```

## Core Infrastructure Endpoints

### Issues Management
- `GET /infrastructure/issues` - List issues with filtering
- `POST /infrastructure/issues` - Create new issue
- `GET /infrastructure/issues/{id}` - Get specific issue
- `PUT /infrastructure/issues/{id}` - Update issue
- `DELETE /infrastructure/issues/{id}` - Delete issue
- `GET /infrastructure/search?q=pothole` - Search issues
- `GET /infrastructure/stats` - Infrastructure statistics

### Geospatial Operations
- `GET /geospatial/nearby-issues?lat=42.36&lng=-71.06&radius_km=1` - Find nearby issues
- `GET /geospatial/clusters?zoom=12&min_lat=42.3&max_lat=42.4&min_lng=-71.1&max_lng=-71.0` - Issue clusters
- `GET /geospatial/neighborhood-stats` - Statistics by neighborhood
- `GET /geospatial/bounds` - Geographic bounds of data

### Analytics & Risk Assessment
- `POST /analysis/risk-assessment` - Create risk assessment for issue
- `POST /analysis/batch-risk-assessment` - Batch risk assessment
- `POST /analysis/cv-analysis/{issue_id}` - Run CV analysis on issue photos
- `GET /analysis/trends?days_back=90` - Trend analysis
- `GET /analysis/risk-distribution` - Risk level distribution

### Reporting & Dashboard
- `GET /reporting/dashboard-stats` - Key dashboard statistics
- `GET /reporting/predictive-alerts` - Predictive maintenance alerts
- `POST /reporting/export-data` - Export data (JSON, GeoJSON)
- `GET /reporting/analytics/summary?days_back=30` - Analytics summary

## Common Query Parameters

### Filtering Issues
- `status` - Filter by case status (Open, Closed, In Progress)
- `risk_level` - Filter by risk level (low, medium, high, critical)
- `neighborhood` - Filter by neighborhood name
- `topic` - Filter by case topic
- `priority` - Filter by priority level
- `min_lat`, `max_lat`, `min_lng`, `max_lng` - Geographic bounds

### Pagination
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 50, max: 100)

### Time Ranges
- `days_back` - Number of days to look back (default varies by endpoint)
- `hours_back` - Number of hours to look back

## Error Responses

```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## Demo Data

The API includes Boston 311 infrastructure data with:
- 500+ real infrastructure issues
- Geographic data for Boston area
- Risk assessments and priorities
- Mock photo analysis capabilities

## Health Check

```http
GET /health

Response:
{
  "status": "healthy",
  "message": "Plotholes Backend API is running",
  "version": "1.0.0"
}
```

## Notes for Demo

- Photo uploads are mocked - files aren't permanently stored
- CV analysis provides realistic mock results based on filename
- All endpoints return demo-friendly data
- Real-time updates simulate live infrastructure monitoring
- Predictive alerts showcase AI-driven maintenance planning