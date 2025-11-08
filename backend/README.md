# Plotholes Backend - Geospatial AI Platform

A Flask-based backend for real-time infrastructure intelligence, safe path-planning, and predictive maintenance.

## Features

- **Photo Upload & AI Analysis**: Upload infrastructure photos for instant CV analysis
- **Risk Assessment**: Automated risk scoring using multiple factors
- **Geospatial Processing**: Heat maps, clustering, and path planning
- **Real-time Updates**: Live dashboard updates with new issues
- **Predictive Analytics**: Identify areas likely to develop issues
- **Reporting & Analytics**: Comprehensive reporting and trend analysis

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL with PostGIS extension
- pip (Python package manager)

### Installation

1. **Clone and setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Install PostgreSQL and PostGIS
   # Create database: plotholes_dev
   # Enable PostGIS extension
   sudo -u postgres psql plotholes_dev -c "CREATE EXTENSION postgis;"
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Update Configuration**
   ```python
   # Edit config.py - update database URLs with your credentials
   SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/plotholes_dev'
   ```

5. **Initialize Database**
   ```bash
   python init_db.py
   ```

6. **Run Application**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Core Infrastructure
- `GET /api/infrastructure/issues` - Get infrastructure issues with filtering
- `POST /api/infrastructure/issues` - Create new issue
- `GET /api/infrastructure/issues/{id}` - Get specific issue
- `PUT /api/infrastructure/issues/{id}` - Update issue
- `DELETE /api/infrastructure/issues/{id}` - Delete issue
- `GET /api/infrastructure/search` - Search issues by text
- `GET /api/infrastructure/stats` - Get infrastructure statistics

### Photo Upload & Analysis
- `POST /api/photos/upload` - Upload photo for analysis
- `GET /api/photos/{id}` - Get photo metadata
- `GET /api/photos/{id}/file` - Serve photo file
- `GET /api/photos/{id}/thumbnail` - Get photo thumbnail
- `POST /api/photos/{id}/analyze` - Re-run CV analysis
- `DELETE /api/photos/{id}` - Delete photo
- `POST /api/photos/batch-upload` - Upload multiple photos

### Geospatial & Mapping
- `GET /api/geospatial/heat-map` - Generate heat map data
- `POST /api/geospatial/path-planning` - Plan safe routes
- `GET /api/geospatial/nearby-issues` - Find nearby issues
- `GET /api/geospatial/clusters` - Get issue clusters for map
- `GET /api/geospatial/neighborhood-stats` - Neighborhood statistics
- `GET /api/geospatial/bounds` - Get geographic bounds of data

### AI Analysis & Risk Assessment
- `POST /api/analysis/risk-assessment` - Create risk assessment
- `POST /api/analysis/batch-risk-assessment` - Batch risk assessment
- `POST /api/analysis/cv-analysis/{id}` - Run CV analysis on issue
- `GET /api/analysis/trends` - Get trend analysis
- `GET /api/analysis/predictive-maintenance` - Get maintenance predictions
- `GET /api/analysis/risk-distribution` - Risk level distribution

### Reporting & Analytics
- `GET /api/reporting/dashboard-stats` - Dashboard statistics
- `GET /api/reporting/real-time-updates` - Recent updates
- `GET /api/reporting/predictive-alerts` - Predictive alerts
- `POST /api/reporting/export-data` - Export data in various formats
- `GET /api/reporting/analytics/summary` - Analytics summary

### System
- `GET /api/health` - Health check

## Demo Workflow

This backend supports the demo workflow:

1. **Upload Photo**: `POST /api/photos/upload` with road image
2. **AI Analysis**: Automatic CV analysis tags "pothole depth: medium, severity: 0.72"
3. **Live Updates**: `GET /api/reporting/real-time-updates` for dashboard updates
4. **Predictive Mode**: `GET /api/analysis/predictive-maintenance` for likely issue areas
5. **Priority Routing**: `POST /api/geospatial/path-planning` for safe routes

## Architecture

```
backend/
├── app.py                 # Flask application factory
├── config.py             # Configuration settings
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
├── models/               # Database models
│   ├── infrastructure.py # Issue and photo models
│   ├── geospatial.py     # Location and path models
│   ├── report.py         # Reporting models
│   └── user.py           # User model
├── routes/               # API route handlers
│   ├── infrastructure.py # Infrastructure endpoints
│   ├── photos.py         # Photo upload endpoints
│   ├── geospatial.py     # Mapping endpoints
│   ├── analysis.py       # AI analysis endpoints
│   └── reporting.py      # Reporting endpoints
└── services/             # Business logic services
    ├── cv_analyzer.py    # Computer vision analysis
    ├── risk_assessor.py  # Risk assessment algorithms
    ├── geospatial_processor.py # Spatial processing
    └── data_importer.py  # Data import utilities
```

## Computer Vision

The CV analyzer uses YOLOv8 for object detection and custom algorithms for:
- Pothole detection and severity assessment
- Infrastructure damage analysis
- Risk level calculation based on image content
- Quality metrics and confidence scoring

## Geospatial Features

- **Heat Maps**: Density visualization of infrastructure issues
- **Path Planning**: Safe routing avoiding high-risk areas
- **Clustering**: Dynamic issue grouping based on zoom level
- **Spatial Analysis**: Proximity searches and geographic statistics

## Risk Assessment

Multi-factor risk scoring considers:
- Issue type and severity
- Location and traffic density
- Time factors and urgency
- Historical patterns in the area
- Computer vision analysis results

## Data Import

Import NYC 311 data:
```python
from services.data_importer import DataImporter
importer = DataImporter()
stats = importer.import_nyc_311_csv('path/to/filtered_data.csv')
```

## Development

### Running Tests
```bash
pytest
```

### Database Reset
```bash
python init_db.py reset
```

### Adding New Endpoints
1. Create route in appropriate `routes/` file
2. Add business logic to `services/` if needed
3. Update this README with new endpoint

## Deployment

For production deployment:
1. Set `FLASK_ENV=production` in environment
2. Use proper PostgreSQL with PostGIS
3. Configure reverse proxy (nginx)
4. Use gunicorn for WSGI server
5. Set up SSL certificates
6. Configure monitoring and logging

## MLH Integration

The backend is designed to be hosted on MLH domains. Update the CORS settings in `app.py` with your MLH domain.

## Support

For questions or issues, check the API health endpoint or review the logs for detailed error information.