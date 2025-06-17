from fastapi import APIRouter, File, UploadFile
from services.detector import detect_person
from services.gps_reader import get_exif_location
from db.mongo import save_detection
from models.detection import PersonDetection, Coordinates
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import os 

router = APIRouter()

UPLOAD_DIR = Path(r"C:\Users\Valeriia\Desktop\sar\test\images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"{file_id}_temp.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    detections, result_filename = detect_person(str(temp_path), UPLOAD_DIR)
    coords = get_exif_location(str(temp_path))
    photo_url = f"http://localhost:8000/static/results/{result_filename}"

    os.remove(temp_path)  

    final_docs = []
    for det in detections:
        doc = PersonDetection(
            photo_url=photo_url,
            photo_coordinates=Coordinates(**coords) if coords else None,
            confidence=det["confidence"],
            bbox=det["bbox"],
            timestamp=datetime.utcnow()
        )
        save_detection(doc.dict())
        final_docs.append(doc)

    return {"status": "ok", "detections": final_docs}
