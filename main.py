from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil  
import os
from services.detector import detect_person
from services.gps_reader import get_exif_location
from db.mongo import save_detection, collection
from models.detection import PersonDetection, Coordinates
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from routes import detect, upload
from pathlib import Path
import uuid
import logging
import traceback
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(r"C:\Users\Valeriia\Desktop\sar\uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path(r"C:\Users\Valeriia\Desktop\sar\static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
app.include_router(detect.router)
#app.include_router(upload.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Search and Rescue API"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        file_id = str(uuid.uuid4())
        temp_path = UPLOAD_DIR / f"{file_id}_temp.jpg"

        logger.info(f"Saving temp file to: {temp_path}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
   
        logger.info("Calling detect_person")
        detections, result_filename = detect_person(str(temp_path), STATIC_DIR)
        logger.info("Calling get_exif_location")
        coords = get_exif_location(str(temp_path))
        photo_url = f"http://localhost:8000/static/results/{result_filename}"



        logger.info("Removing temp file")
        os.remove(temp_path)

        final_docs = []
        for det in detections:
            doc = PersonDetection(
                photo_url=photo_url,
                photo_coordinates=Coordinates(**coords) if coords else None,
                confidence=det["confidence"],
                bbox=det["bbox"],
                timestamp=datetime.now()
            )
            logger.info("Saving detection to MongoDB")
            save_detection(doc.dict())
            final_docs.append(doc)


        
        logger.info(f"Saved {len(final_docs)} detections")
        print("photo_url:", photo_url)

        return {
            "status": "ok",
            "detections": final_docs
        }
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "error": str(e)}
        )   

# from fastapi import FastAPI, File, UploadFile, HTTPException
# import shutil
# import os
# from services.detector import detect_person
# from services.gps_reader import get_exif_location
# from db.mongo import save_detection, collection
# from models.detection import PersonDetection, Coordinates
# from datetime import datetime
# from fastapi.staticfiles import StaticFiles
# from routes import detect
# from pathlib import Path
# import uuid
# import logging
# import traceback
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Для розробки, в продакшені вкажіть конкретні домени
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Створення директорій
# UPLOAD_DIR = Path(r"C:\Users\Valeriia\Desktop\sar\uploads")
# STATIC_DIR = Path(r"C:\Users\Valeriia\Desktop\sar\static")
# RESULTS_DIR = STATIC_DIR / "results"

# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# STATIC_DIR.mkdir(parents=True, exist_ok=True)
# RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# # Монтування статичних файлів
# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# # Підключення роутерів
# app.include_router(detect.router)


# @app.get("/")
# async def root():
#     return {"message": "Welcome to Search and Rescue API"}

# @app.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     try:
#         logger.info(f"Received file: {file.filename}")
        
#         # Перевірка формату файлу
#         if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
#             raise HTTPException(status_code=400, detail="Invalid image format")
        
#         # Створення тимчасового файлу
#         file_id = str(uuid.uuid4())
#         temp_path = UPLOAD_DIR / f"{file_id}_temp.jpg"
        
#         logger.info(f"Saving temp file to: {temp_path}")
#         with open(temp_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
        
#         # Детекція людей
#         logger.info("Calling detect_person")
#         detections, result_filename = detect_person(str(temp_path), RESULTS_DIR)
        
#         # Отримання GPS координат
#         logger.info("Calling get_exif_location")
#         coords = get_exif_location(str(temp_path))
        
#         # Створення URL для зображення
#         photo_url = f"http://localhost:8000/static/results/{result_filename}"        
#         # Видалення тимчасового файлу
#         logger.info("Removing temp file")
#         try:
#             os.remove(temp_path)
#         except Exception as e:
#             logger.warning(f"Could not remove temp file: {e}")
        
#         # Збереження детекцій в базу даних
#         final_docs = []
#         for det in detections:
#             doc = PersonDetection(
#                 photo_url=photo_url,
#                 photo_coordinates=Coordinates(**coords) if coords else None,
#                 confidence=det["confidence"],
#                 bbox=det["bbox"],
#                 timestamp=datetime.now()
#             )
#             logger.info("Saving detection to MongoDB")
#             save_detection(doc.dict())
#             final_docs.append(doc.dict())  # Конвертуємо в dict для JSON відповіді
        
#         logger.info(f"Saved {len(final_docs)} detections")
#         logger.info(f"Photo URL: {photo_url}")
        
#         # Повертаємо відповідь у форматі, який очікує фронтенд
#         return {
#             "status": "ok",
#             "detections": final_docs,
#             "photo_url": photo_url,
#             "coords": {"lat": coords["latitude"], "lon": coords["longitude"]} if coords else None,
#             "humans": len(detections),
#             "message": f"Знайдено {len(detections)} осіб"
#         }
        
#     except Exception as e:
#         logger.error(f"Error processing file: {str(e)}")
#         logger.error(traceback.format_exc())
#         return JSONResponse(
#             status_code=500,
#             content={"message": "Internal Server Error", "error": str(e)}
#         )

# if __name__ == "__main__":
    
#     uvicorn.run(app, host="0.0.0.0", port=8000)