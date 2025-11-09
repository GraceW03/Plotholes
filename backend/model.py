import torch
import torch.serialization

# ✅ allow YOLO model class for PyTorch 2.6+ safe load
try:
    torch.serialization.add_safe_globals([__import__('ultralytics').nn.tasks.DetectionModel])
except Exception as e:
    print("[INFO] Safe globals patch not required or already applied:", e)

from ultralyticsplus import YOLO
import requests
import os
from io import BytesIO
from PIL import Image
import numpy as np

print("Loading pothole detection model...")
model = YOLO("keremberke/yolov8m-pothole-segmentation")

# Enhanced model parameters for better detection
model.overrides["conf"] = 0.15  # Lower confidence threshold to detect more objects
model.overrides["iou"] = 0.30    # Lower IoU threshold for better detection of overlapping objects
model.overrides["agnostic_nms"] = False
model.overrides["max_det"] = 1000
model.overrides["imgsz"] = 1280  # Higher resolution for better detection
model.overrides["device"] = '0' if torch.cuda.is_available() else 'cpu'  # Use GPU if available

def analyze_image(image_path: str, is_url: bool = True):
    try:
        # Load image
        if is_url:
            print(f"[MODEL] Fetching image from URL: {image_path}")
            response = requests.get(image_path, stream=True, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            print(f"[MODEL] Loading local image: {image_path}")
            if not os.path.exists(image_path):
                print(f"[ERROR] File not found: {image_path}")
                return {"pothole": False, "severity": "error", "confidence": 0.0, "error": f"File not found: {image_path}"}
            img = Image.open(image_path).convert("RGB")
            
        # Save a debug copy of the loaded image
        debug_img_path = "debug_loaded_image.jpg"
        img.save(debug_img_path)
        print(f"[DEBUG] Loaded image saved to {debug_img_path}")
        print(f"[DEBUG] Image size: {img.size}, mode: {img.mode}")
        
        # Convert to numpy array for model input
        import numpy as np
        img_np = np.array(img)
        print(f"[DEBUG] Numpy array shape: {img_np.shape}, dtype: {img_np.dtype}")
        
        if img_np.size == 0:
            print("[ERROR] Loaded image is empty")
            return {"pothole": False, "severity": "error", "confidence": 0.0, "error": "Loaded image is empty"}
            
        print(f"[MODEL] Image loaded. Size: {img.size}, Mode: {img.mode}")
        
        # Save original image for debugging
        debug_img_path = "debug_image.jpg"
        img.save(debug_img_path)
        print(f"[DEBUG] Original image saved to {debug_img_path}")
        
        # Preprocess image - enhance contrast
        from PIL import ImageEnhance
        
        # Convert to grayscale for better edge detection
        gray_img = img.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray_img)
        enhanced_img = enhancer.enhance(2.0)  # Increase contrast
        
        # Convert back to RGB for the model
        processed_img = enhanced_img.convert('RGB')
        
        # Save processed image for debugging
        processed_img_path = "processed_image.jpg"
        processed_img.save(processed_img_path)
        print(f"[DEBUG] Processed image saved to {processed_img_path}")
        
        # Run prediction with minimal parameters first
        print("[MODEL] Running prediction...")
        try:
            # First try with minimal parameters
            results = model.predict(
                img_np,  # Use the numpy array directly
                conf=0.1,      # Very low confidence threshold
                iou=0.3,       # Lower IoU threshold
                imgsz=640,     # Try smaller size first
                augment=False,  # Disable augmentation for now
                verbose=True    # More detailed output
            )
            
            # If no results, try with different parameters
            if results is None or len(results) == 0:
                print("[WARNING] No results with initial parameters, trying with different settings...")
                results = model.predict(
                    img_np,
                    conf=0.05,     # Even lower confidence
                    iou=0.25,      # Lower IoU
                    imgsz=1280,    # Higher resolution
                    augment=True,  # Try with augmentation
                    verbose=True
                )
                
            # If still no results, try with the original image
            if results is None or len(results) == 0:
                print("[WARNING] Still no results, trying with original image...")
                results = model.predict(
                    img,  # Try with PIL Image
                    conf=0.05,
                    iou=0.25,
                    imgsz=1280,
                    augment=True,
                    verbose=True
                )
                
            if results is None or len(results) == 0:
                print("[WARNING] No potholes detected with any parameters")
                return {
                    "pothole": False,
                    "severity": "none",
                    "confidence": 0.0,
                    "message": "No potholes detected with current model settings"
                }
            
            print(f"[MODEL] Prediction complete. Results type: {type(results)}")
            
            if results is None or len(results) == 0:
                print("[WARNING] No results returned from model prediction")
                # Try with a simpler prediction
                results = model.predict(processed_img, conf=0.1, verbose=True)
                
                if results is None or len(results) == 0:
                    return {
                        "pothole": False, 
                        "severity": "none", 
                        "confidence": 0.0, 
                        "message": "Model returned no results"
                    }
            
            # Check if we have any detections
            if not hasattr(results[0], 'boxes') or results[0].boxes is None:
                print("[WARNING] No boxes in results")
                return {
                    "pothole": False, 
                    "severity": "none", 
                    "confidence": 0.0, 
                    "message": "No detections in the image"
                }
                
            # Get detections
            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                print("[INFO] No potholes detected in the image")
                return {
                    "pothole": False, 
                    "severity": "none", 
                    "confidence": 0.0, 
                    "message": "No potholes detected"
                }
                
            # Convert boxes to numpy array
            boxes_np = boxes.xyxy.cpu().numpy()  # Get boxes in xyxy format
            confs = boxes.conf.cpu().numpy()     # Get confidence scores
            
            if len(confs) == 0:
                print("[INFO] No potholes detected after filtering")
                return {
                    "pothole": False, 
                    "severity": "none", 
                    "confidence": 0.0, 
                    "message": "No potholes detected after filtering"
                }
                
            avg_conf = float(np.mean(confs))
            num_detections = len(confs)
            
            print(f"[MODEL] Found {num_detections} potholes, average confidence: {avg_conf:.2f}")
            print(f"[MODEL] Confidence scores: {[round(c, 2) for c in confs]}")
            
            # Calculate severity
            if num_detections < 2 or avg_conf < 0.2:
                severity = "minor"
            elif num_detections < 5 or avg_conf < 0.4:
                severity = "moderate"
            else:
                severity = "severe"
                
            return {
                "pothole": True,
                "severity": severity,
                "confidence": round(avg_conf, 2),
                "detections": num_detections,
                "boxes": boxes_np.tolist()
            }
            
        except Exception as e:
            print(f"[ERROR] Error during prediction: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "pothole": False, 
                "severity": "error", 
                "confidence": 0.0, 
                "error": f"Prediction error: {str(e)}"
            }
            
    except Exception as e:
        print(f"[ERROR] analyze_image failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "pothole": False, 
            "severity": "error", 
            "confidence": 0.0, 
            "error": str(e)
        }
