# backend/model.py
from ultralyticsplus import YOLO
import requests
from io import BytesIO
from PIL import Image
import numpy as np

print("Loading pothole detection model...")
model = YOLO("keremberke/yolov8m-pothole-segmentation")

model.overrides["conf"] = 0.25
model.overrides["iou"] = 0.45
model.overrides["agnostic_nms"] = False
model.overrides["max_det"] = 1000

def analyze_image(image_url: str):
    """
    Downloads an image and returns pothole detection info.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")

        results = model.predict(img)

        if not results or len(results[0].boxes) == 0:
            return {"pothole": False, "severity": "none", "confidence": 0.0}

        boxes = results[0].boxes.data.cpu().numpy()
        confs = boxes[:, 4]
        avg_conf = float(np.mean(confs))
        num_detections = len(confs)

        if num_detections < 3:
            severity = "minor"
        elif num_detections < 8:
            severity = "moderate"
        else:
            severity = "severe"

        return {
            "pothole": True,
            "severity": severity,
            "confidence": round(avg_conf, 2),
            "detections": int(num_detections),
        }

    except Exception as e:
        print(f"[ERROR] analyze_image failed: {e}")
        return {"pothole": False, "severity": "unknown", "confidence": 0.0}
