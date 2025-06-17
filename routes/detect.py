# # from fastapi import APIRouter
# # from db.mongo import collection
# # from models.detection import PersonDetection, Coordinates
# # from datetime import datetime
# # from typing import List


# # router = APIRouter(prefix="/detections", tags=["Detections"])

# # @router.post("/") 
# # def add_detection(data: PersonDetection):
# #     doc = data.dict()
# #     if not doc.get("timestamp"):
# #         doc["timestamp"] = datetime.now()
# #     collection.insert_one(doc)
# #     return {"message": "Detection added", "data": doc}

# # # @router.get("/") # Цей маршрут буде GET /detections/
# # # def get_all_simple(): # Це функція, яка повертає ВСІ детекції, як вони є в БД
    

# # #     return list(collection.find({}, {"_id": 0}))

# # @router.get("/with_coords") # Цей маршрут буде GET /detections/with_coords
# # async def get_all_detections_with_coords():
 
# #     results = collection.find({"photo_coordinates": {"$ne": None}})
# #     detections = []

# #     for doc in results:
# #         coords = doc.get("photo_coordinates")
# #         detections.append({
# #             "photo_coordinates": {
# #             "lat": coords.get("latitude"),
# #             "lon": coords.get("longitude"),
# #         },
# #             "photo_url": doc.get("photo_url", ""),
# #             "confidence": doc.get("confidence", 0),
# #             "timestamp": doc.get("timestamp", "")
# #         })

# #     return detections

# # services/detector.py
# from ultralytics import YOLO
# import cv2
# from datetime import datetime
# from pathlib import Path
# import uuid
# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Завантаження моделі
# try:
#     model = YOLO(r"C:\Users\Valeriia\Desktop\sar\best.pt")
#     logger.info("Модель YOLO успішно завантажена")
# except Exception as e:
#     logger.error(f"Помилка завантаження моделі: {e}")
#     raise

# def detect_person(image_path: str, save_dir: Path) -> tuple:
#     """
#     Детекція осіб на зображенні
#     Повертає: (список_детекцій, ім'я_файлу_результату)
#     """
#     try:
#         logger.info(f"Обробка зображення: {image_path}")
        
#         # Перевірка існування файлу
#         if not Path(image_path).exists():
#             logger.error(f"Файл не знайдено: {image_path}")
#             return [], None
        
#         # Запуск детекції
#         results = model(image_path)[0]
#         detections = []
        
#         # Завантаження зображення
#         image = cv2.imread(image_path)
#         if image is None:
#             logger.error(f"Не вдалося завантажити зображення: {image_path}")
#             return [], None
        
#         logger.info(f"Розмір зображення: {image.shape}")
        
#         # Обробка результатів детекції
#         if results.boxes is not None:
#             for box in results.boxes:
#                 cls = int(box.cls[0])
#                 conf = float(box.conf[0])
#                 class_name = model.names[cls]
                
#                 logger.info(f"Виявлено: клас={class_name}, впевненість={conf:.3f}")
                
#                 # Фільтр для класу "person" (клас 0) з впевненістю > 0.5
#                 if cls == 0 and conf > 0.5:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
#                     # Малювання прямокутника
#                     cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
#                     # Додавання тексту з впевненістю
#                     label = f"Person: {conf:.2f}"
#                     cv2.putText(image, label, (x1, y1-10), 
#                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
#                     detections.append({
#                         "confidence": conf,
#                         "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
#                     })
                    
#                     logger.info(f"Додано детекцію: bbox=({x1},{y1},{x2},{y2}), conf={conf:.3f}")
#         else:
#             logger.info("Не знайдено жодних об'єктів")
        
#         # Збереження результату
#         result_id = uuid.uuid4().hex
#         result_filename = f"{result_id}.jpg"
#         result_path = save_dir / result_filename
        
#         # Створення директорії якщо не існує
#         result_path.parent.mkdir(parents=True, exist_ok=True)
        
#         success = cv2.imwrite(str(result_path), image)
#         if not success:
#             logger.error(f"Не вдалося зберегти зображення: {result_path}")
#             return detections, None
        
#         logger.info(f"Результат збережено: {result_path}")
#         logger.info(f"Знайдено {len(detections)} осіб")
        
#         return detections, result_filename
        
#     except Exception as e:
#         logger.error(f"Помилка в detect_person: {e}")
#         return [], None

from fastapi import APIRouter, HTTPException
from db.mongo import collection
from models.detection import PersonDetection, Coordinates
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detections", tags=["Detections"])

@router.post("/") 
def add_detection(data: PersonDetection):
    """Add a new detection to database"""
    try:
        doc = data.dict()
        if not doc.get("timestamp"):
            doc["timestamp"] = datetime.now()
        collection.insert_one(doc)
        return {"message": "Detection added", "data": doc}
    except Exception as e:
        logger.error(f"Error adding detection: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not add detection")

# @router.get("/")
# async def get_all_detections():
#     """Get all person detections from database"""
#     try:
#         detections = list(collection.find({}, {"_id": 0}))
#         return {
#             "status": "ok",
#             "count": len(detections),
#             "detections": detections
#         }
#     except Exception as e:
#         logger.error(f"Error getting detections: {str(e)}")
#         raise HTTPException(status_code=500, detail="Could not retrieve detections")

@router.get("/with_coords")
async def get_all_detections_with_coords():
    try:
        results = collection.find({"photo_coordinates": {"$ne": None}})
        detections = []

        for doc in results:
            coords = doc.get("photo_coordinates")
            if coords:
                detections.append({
                    "lat": coords.get("lat"),
                    "lon": coords.get("lng"),

                    "photo_url": doc.get("photo_url", ""),
                    "confidence": doc.get("confidence", 0),
                    "timestamp": doc.get("timestamp", ""),
                    "bbox": doc.get("bbox", {})
                })

        return {
            "status": "ok",
            "count": len(detections),
            "detections": detections
        }
    except Exception as e:
        logger.error(f"Error getting detections with coordinates: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve detections with coordinates")

@router.get("/recent")
async def get_recent_detections(limit: int = 10):
    try:
        detections = list(
            collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return {
            "status": "ok",
            "count": len(detections),
            "detections": detections
        }
    except Exception as e:
        logger.error(f"Error getting recent detections: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve recent detections")

@router.delete("/")
async def clear_all_detections():
    """Clear all detections from database"""
    try:
        result = collection.delete_many({})
        return {
            "status": "ok",
            "message": f"Deleted {result.deleted_count} detections"
        }
    except Exception as e:
        logger.error(f"Error clearing detections: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not clear detections")

@router.get("/stats")
async def get_detection_stats():
    try:
        total_detections = collection.count_documents({})
        detections_with_coords = collection.count_documents({"photo_coordinates": {"$ne": None}})
        
        # Get average confidence
        pipeline = [
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
        ]
        avg_result = list(collection.aggregate(pipeline))
        avg_confidence = avg_result[0]["avg_confidence"] if avg_result else 0
        
        return {
            "status": "ok",
            "stats": {
                "total_detections": total_detections,
                "detections_with_coordinates": detections_with_coords,
                "detections_without_coordinates": total_detections - detections_with_coords,
                "average_confidence": round(avg_confidence, 3) if avg_confidence else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting detection stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve detection statistics")