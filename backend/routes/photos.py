"""
Photo upload and processing API routes
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
import cv2
import numpy as np
from database import db
from models.infrastructure import InfrastructureIssue, IssuePhoto
from services.cv_analyzer import CVAnalyzer
from datetime import datetime

photos_bp = Blueprint('photos', __name__)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def mock_file_analysis(filename: str) -> dict:
    """Mock file analysis for demo purposes"""
    # Mock analysis based on filename keywords
    filename_lower = filename.lower()
    
    if 'pothole' in filename_lower:
        return {
            'risk_level': 'high',
            'confidence': 0.87,
            'detected_objects': [
                {'class': 'pothole', 'confidence': 0.87, 'severity': 'medium', 'depth_cm': 8}
            ],
            'severity_analysis': 'Medium-depth pothole detected with high confidence'
        }
    elif 'crack' in filename_lower:
        return {
            'risk_level': 'medium',
            'confidence': 0.72,
            'detected_objects': [
                {'class': 'crack', 'confidence': 0.72, 'length_m': 2.3}
            ],
            'severity_analysis': 'Surface crack detected, monitor for expansion'
        }
    elif 'flood' in filename_lower or 'water' in filename_lower:
        return {
            'risk_level': 'critical',
            'confidence': 0.94,
            'detected_objects': [
                {'class': 'flooding', 'confidence': 0.94, 'depth_cm': 15}
            ],
            'severity_analysis': 'Standing water detected - immediate attention required'
        }
    else:
        return {
            'risk_level': 'medium',
            'confidence': 0.65,
            'detected_objects': [
                {'class': 'general_issue', 'confidence': 0.65}
            ],
            'severity_analysis': 'General infrastructure issue detected'
        }

@photos_bp.route('/upload', methods=['POST'])
def upload_photo():
    """Mock photo upload for demo purposes"""
    try:
        # Check if file is in request or use mock data
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get issue ID (optional)
        issue_id = request.form.get('issue_id')
        
        # Mock file processing (don't actually save file)
        unique_filename = f"mock_{uuid.uuid4()}.jpg"
        mock_file_size = 1024 * 200  # Mock 200KB file
        mock_width, mock_height = 1920, 1080  # Mock dimensions
        
        # Create photo record with mock data
        photo = IssuePhoto(
            issue_id=issue_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=f"/mock/uploads/{unique_filename}",  # Mock path
            file_size=mock_file_size,
            mime_type=file.mimetype,
            width=mock_width,
            height=mock_height
        )
        
        db.session.add(photo)
        db.session.flush()  # Get the photo ID
        
        # Mock CV analysis based on filename
        analysis_results = mock_file_analysis(file.filename)
        
        # Update photo with mock analysis results
        photo.analysis_results = analysis_results
        photo.processed = True
        photo.processed_at = datetime.utcnow()
        
        # If associated with an issue, update issue risk assessment
        if issue_id and analysis_results:
            issue = InfrastructureIssue.query.get(issue_id)
            if issue:
                issue.risk_level = analysis_results.get('risk_level', 'medium')
                issue.confidence_score = analysis_results.get('confidence', 0.5)
                issue.detected_objects = analysis_results.get('detected_objects', [])
        
        db.session.commit()
        
        return jsonify({
            'photo': photo.to_dict(),
            'analysis_results': analysis_results,
            'message': 'Photo uploaded and analyzed successfully (demo mode)',
            'demo_note': 'This is a mock upload for demonstration purposes'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<photo_id>', methods=['GET'])
def get_photo(photo_id):
    """Get photo metadata"""
    try:
        photo = IssuePhoto.query.get_or_404(photo_id)
        return jsonify(photo.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<photo_id>/file', methods=['GET'])
def serve_photo(photo_id):
    """Serve mock photo file for demo"""
    try:
        photo = IssuePhoto.query.get_or_404(photo_id)
        
        # Return mock photo data for demo
        return jsonify({
            'demo_mode': True,
            'message': 'Photo file would be served here in production',
            'photo_info': {
                'filename': photo.filename,
                'original_filename': photo.original_filename,
                'file_size': photo.file_size,
                'dimensions': f"{photo.width}x{photo.height}" if photo.width else "Unknown"
            },
            'mock_image_url': f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300'><rect width='100%25' height='100%25' fill='%23ddd'/><text x='50%25' y='50%25' text-anchor='middle' dy='.3em'>Mock Photo: {photo.original_filename}</text></svg>"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<photo_id>/thumbnail', methods=['GET'])
def get_thumbnail(photo_id):
    """Get mock thumbnail for demo"""
    try:
        photo = IssuePhoto.query.get_or_404(photo_id)
        
        # Return mock thumbnail data
        return jsonify({
            'demo_mode': True,
            'message': 'Thumbnail would be served here in production',
            'photo_info': {
                'filename': photo.filename,
                'original_filename': photo.original_filename
            },
            'mock_thumbnail_url': f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='150'><rect width='100%25' height='100%25' fill='%23f0f0f0'/><text x='50%25' y='50%25' text-anchor='middle' dy='.3em' font-size='12'>Thumbnail: {photo.original_filename[:20]}...</text></svg>"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<photo_id>/analyze', methods=['POST'])
def reanalyze_photo(photo_id):
    """Re-run mock CV analysis on a photo"""
    try:
        photo = IssuePhoto.query.get_or_404(photo_id)
        
        # Mock re-analysis with slightly different results
        analysis_results = mock_file_analysis(photo.original_filename)
        
        # Add some variation for re-analysis
        if 'confidence' in analysis_results:
            analysis_results['confidence'] = min(0.95, analysis_results['confidence'] + 0.05)
        
        analysis_results['reanalysis'] = True
        analysis_results['analysis_version'] = '2.0'
        
        # Update photo with new results
        photo.analysis_results = analysis_results
        photo.processed = True
        photo.processed_at = datetime.utcnow()
        
        # Update associated issue if exists
        if photo.issue_id and analysis_results:
            issue = InfrastructureIssue.query.get(photo.issue_id)
            if issue:
                issue.risk_level = analysis_results.get('risk_level', 'medium')
                issue.confidence_score = analysis_results.get('confidence', 0.5)
                issue.detected_objects = analysis_results.get('detected_objects', [])
        
        db.session.commit()
        
        return jsonify({
            'photo': photo.to_dict(),
            'analysis_results': analysis_results,
            'demo_note': 'Mock re-analysis completed with enhanced confidence'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a photo and its file"""
    try:
        photo = IssuePhoto.query.get_or_404(photo_id)
        
        # Delete file if exists
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        # Delete thumbnail if exists
        upload_dir = os.path.dirname(photo.file_path)
        thumb_filename = f"thumb_{photo.filename}"
        thumb_path = os.path.join(upload_dir, thumb_filename)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        
        # Delete database record
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({'message': 'Photo deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/batch-upload', methods=['POST'])
def batch_upload():
    """Upload multiple photos at once"""
    try:
        if 'photos' not in request.files:
            return jsonify({'error': 'No photos provided'}), 400
        
        files = request.files.getlist('photos')
        issue_id = request.form.get('issue_id')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        upload_dir = ensure_upload_dir()
        uploaded_photos = []
        errors = []
        
        for file in files:
            try:
                if not allowed_file(file.filename):
                    errors.append(f"File {file.filename} has invalid type")
                    continue
                
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Save file
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                
                # Get image dimensions
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                except Exception:
                    width, height = None, None
                
                # Create photo record
                photo = IssuePhoto(
                    issue_id=issue_id,
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=file.mimetype,
                    width=width,
                    height=height
                )
                
                db.session.add(photo)
                uploaded_photos.append(photo)
                
            except Exception as e:
                errors.append(f"Error uploading {file.filename}: {str(e)}")
        
        db.session.commit()
        
        # Start async CV analysis for uploaded photos
        for photo in uploaded_photos:
            try:
                cv_analyzer = CVAnalyzer()
                analysis_results = cv_analyzer.analyze_image(photo.file_path)
                
                photo.analysis_results = analysis_results
                photo.processed = True
                photo.processed_at = datetime.utcnow()
                
            except Exception as cv_error:
                print(f"CV Analysis error for {photo.filename}: {cv_error}")
        
        db.session.commit()
        
        return jsonify({
            'uploaded_photos': [photo.to_dict() for photo in uploaded_photos],
            'errors': errors,
            'total_uploaded': len(uploaded_photos),
            'total_errors': len(errors)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500