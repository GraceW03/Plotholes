"""
API routes for the Plotholes platform
"""

# Import all route modules to ensure they're registered
from . import infrastructure
from . import photos
from . import analysis
from . import reporting

__all__ = [
    'infrastructure',
    'photos'
]