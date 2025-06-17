# services/detector.py
from ultralytics import YOLO
import cv2
from datetime import datetime
from pathlib import Path
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = YOLO(r"C:\Users\Valeriia\Desktop\sar\best.pt")

def detect_person(image_path: str, save_dir: Path) -> list:
    logger.info(f"Processing image: {image_path}")
    results = model(image_path)[0]
    detections = []
    image = cv2.imread(image_path)

    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls] 
        logger.info(f"Detected: class={class_name}, confidence={conf}")
        if cls == 0 and conf > 0.5:  
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            detections.append({
                "confidence": conf,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })
        else:
            logger.info(f"Skipped: class={class_name}, confidence={conf}")

    result_id = uuid.uuid4().hex
    result_subdir = save_dir / "results"
    result_subdir.mkdir(exist_ok=True)
    result_path = result_subdir / f"{result_id}.jpg"
    cv2.imwrite(str(result_path), image)

    return detections, result_path.name