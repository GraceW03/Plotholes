"""
Computer Vision Analyzer for infrastructure issue detection and risk assessment
"""

import cv2
import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO
import os
from typing import Dict, List, Any, Tuple

class CVAnalyzer:
    """Computer Vision analyzer for infrastructure issues"""
    
    def __init__(self):
        """Initialize the CV analyzer with YOLO model"""
        self.model = None
        self.load_model()
        
        # Infrastructure issue classes and their risk levels
        self.issue_classes = {
            'pothole': {'risk_base': 0.7, 'description': 'Road surface damage'},
            'crack': {'risk_base': 0.5, 'description': 'Surface crack'},
            'debris': {'risk_base': 0.4, 'description': 'Road debris'},
            'flooding': {'risk_base': 0.9, 'description': 'Water accumulation'},
            'broken_light': {'risk_base': 0.6, 'description': 'Street light damage'},
            'sign_damage': {'risk_base': 0.5, 'description': 'Traffic sign damage'},
            'construction': {'risk_base': 0.3, 'description': 'Construction zone'},
            'vehicle': {'risk_base': 0.1, 'description': 'Vehicle present'},
            'person': {'risk_base': 0.1, 'description': 'Person present'}
        }
        
        # Risk level thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 1.0
        }
    
    def load_model(self):
        """Load YOLO model for object detection"""
        try:
            # Use YOLOv8 nano model for demo (faster inference)
            # In production, you might want to use a larger model or custom trained model
            self.model = YOLO('yolov8n.pt')
            print("YOLO model loaded successfully")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image for infrastructure issues
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            # Get basic image properties
            height, width = image.shape[:2]
            image_size = os.path.getsize(image_path)
            
            # Run object detection if model is available
            detected_objects = []
            if self.model is not None:
                detected_objects = self._detect_objects(image)
            
            # Analyze image quality and properties
            quality_metrics = self._analyze_image_quality(image)
            
            # Calculate risk assessment
            risk_assessment = self._calculate_risk(detected_objects, quality_metrics)
            
            # Detect specific infrastructure issues
            infrastructure_analysis = self._analyze_infrastructure_issues(image, detected_objects)
            
            results = {
                'analysis_timestamp': self._get_timestamp(),
                'image_properties': {
                    'width': width,
                    'height': height,
                    'file_size': image_size,
                    'aspect_ratio': round(width / height, 2)
                },
                'detected_objects': detected_objects,
                'quality_metrics': quality_metrics,
                'infrastructure_analysis': infrastructure_analysis,
                'risk_level': risk_assessment['level'],
                'confidence': risk_assessment['confidence'],
                'risk_factors': risk_assessment['factors'],
                'recommendations': self._generate_recommendations(risk_assessment, detected_objects)
            }
            
            return results
            
        except Exception as e:
            return {
                'error': str(e),
                'analysis_timestamp': self._get_timestamp(),
                'risk_level': 'unknown',
                'confidence': 0.0
            }
    
    def _detect_objects(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in the image using YOLO"""
        try:
            results = self.model(image)
            detected_objects = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name and confidence
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        confidence = float(box.conf[0])
                        
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        detected_objects.append({
                            'class': class_name,
                            'confidence': round(confidence, 3),
                            'bbox': {
                                'x1': int(x1), 'y1': int(y1),
                                'x2': int(x2), 'y2': int(y2),
                                'width': int(x2 - x1),
                                'height': int(y2 - y1)
                            },
                            'area_percentage': round(((x2 - x1) * (y2 - y1)) / (image.shape[0] * image.shape[1]) * 100, 2)
                        })
            
            return detected_objects
            
        except Exception as e:
            print(f"Object detection error: {e}")
            return []
    
    def _analyze_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image quality metrics"""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate blur (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast (standard deviation)
        contrast = np.std(gray)
        
        # Determine quality ratings
        blur_quality = 'good' if blur_score > 100 else 'poor' if blur_score < 50 else 'fair'
        brightness_quality = 'good' if 50 < brightness < 200 else 'poor'
        contrast_quality = 'good' if contrast > 30 else 'poor' if contrast < 15 else 'fair'
        
        return {
            'blur_score': round(blur_score, 2),
            'blur_quality': blur_quality,
            'brightness': round(brightness, 2),
            'brightness_quality': brightness_quality,
            'contrast': round(contrast, 2),
            'contrast_quality': contrast_quality,
            'overall_quality': self._calculate_overall_quality(blur_quality, brightness_quality, contrast_quality)
        }
    
    def _calculate_overall_quality(self, blur: str, brightness: str, contrast: str) -> str:
        """Calculate overall image quality"""
        qualities = [blur, brightness, contrast]
        good_count = qualities.count('good')
        poor_count = qualities.count('poor')
        
        if good_count >= 2:
            return 'good'
        elif poor_count >= 2:
            return 'poor'
        else:
            return 'fair'
    
    def _analyze_infrastructure_issues(self, image: np.ndarray, detected_objects: List[Dict]) -> Dict[str, Any]:
        """Analyze specific infrastructure issues in the image"""
        # Edge detection for cracks and surface damage
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Color analysis for different types of issues
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Detect water/flooding (blue tones)
        blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
        water_percentage = np.sum(blue_mask > 0) / blue_mask.size * 100
        
        # Detect asphalt/road surface (dark tones)
        road_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 80))
        road_percentage = np.sum(road_mask > 0) / road_mask.size * 100
        
        # Count relevant detected objects
        infrastructure_objects = [obj for obj in detected_objects 
                                if obj['class'] in self.issue_classes.keys()]
        
        return {
            'edge_density': round(edge_density, 4),
            'surface_analysis': {
                'road_surface_percentage': round(road_percentage, 2),
                'water_detection_percentage': round(water_percentage, 2),
                'potential_flooding': water_percentage > 5.0
            },
            'infrastructure_objects_count': len(infrastructure_objects),
            'infrastructure_objects': infrastructure_objects,
            'estimated_issue_severity': self._estimate_severity(edge_density, water_percentage, infrastructure_objects)
        }
    
    def _estimate_severity(self, edge_density: float, water_percentage: float, infrastructure_objects: List) -> str:
        """Estimate issue severity based on analysis"""
        severity_score = 0
        
        # Edge density contribution (potential cracks/damage)
        if edge_density > 0.1:
            severity_score += 0.3
        elif edge_density > 0.05:
            severity_score += 0.1
        
        # Water detection contribution
        if water_percentage > 10:
            severity_score += 0.4
        elif water_percentage > 5:
            severity_score += 0.2
        
        # Object detection contribution
        for obj in infrastructure_objects:
            if obj['class'] in self.issue_classes:
                issue_risk = self.issue_classes[obj['class']]['risk_base']
                severity_score += issue_risk * obj['confidence'] * 0.5
        
        # Convert to severity level
        if severity_score > 0.7:
            return 'high'
        elif severity_score > 0.4:
            return 'medium'
        elif severity_score > 0.1:
            return 'low'
        else:
            return 'minimal'
    
    def _calculate_risk(self, detected_objects: List[Dict], quality_metrics: Dict) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        risk_score = 0.0
        risk_factors = []
        
        # Quality impact on confidence
        quality_modifier = 1.0
        if quality_metrics['overall_quality'] == 'poor':
            quality_modifier = 0.7
            risk_factors.append('Poor image quality reduces confidence')
        elif quality_metrics['overall_quality'] == 'fair':
            quality_modifier = 0.85
        
        # Calculate risk from detected infrastructure issues
        for obj in detected_objects:
            if obj['class'] in self.issue_classes:
                issue_data = self.issue_classes[obj['class']]
                object_risk = issue_data['risk_base'] * obj['confidence']
                
                # Size factor - larger objects are riskier
                size_factor = min(obj['area_percentage'] / 10.0, 1.0)
                object_risk *= (0.5 + size_factor * 0.5)
                
                risk_score += object_risk
                risk_factors.append(f"{issue_data['description']} detected (confidence: {obj['confidence']:.2f})")
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        confidence = risk_score * quality_modifier
        
        # Determine risk level
        risk_level = 'low'
        for level, threshold in sorted(self.risk_thresholds.items(), key=lambda x: x[1]):
            if risk_score >= threshold:
                risk_level = level
        
        return {
            'level': risk_level,
            'confidence': round(confidence, 3),
            'raw_score': round(risk_score, 3),
            'factors': risk_factors
        }
    
    def _generate_recommendations(self, risk_assessment: Dict, detected_objects: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        risk_level = risk_assessment['level']
        
        if risk_level == 'critical':
            recommendations.append("Immediate attention required - potential safety hazard")
            recommendations.append("Consider blocking access until resolved")
        elif risk_level == 'high':
            recommendations.append("High priority repair needed")
            recommendations.append("Monitor closely for deterioration")
        elif risk_level == 'medium':
            recommendations.append("Schedule repair within reasonable timeframe")
            recommendations.append("Add to maintenance queue")
        else:
            recommendations.append("Monitor during regular inspections")
        
        # Specific recommendations based on detected objects
        for obj in detected_objects:
            if obj['class'] == 'pothole' and obj['confidence'] > 0.7:
                recommendations.append("Fill pothole to prevent vehicle damage")
            elif obj['class'] == 'flooding' and obj['confidence'] > 0.6:
                recommendations.append("Improve drainage to prevent water accumulation")
            elif obj['class'] == 'broken_light':
                recommendations.append("Replace street light for safety")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()