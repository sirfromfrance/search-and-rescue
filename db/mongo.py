# db/mongo.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = os.getenv("MONGO_URI", "")
collection = None

try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')
    logger.info("Успішно підключено до MongoDB!")
    db = client["search_and_rescue"]
    collection = db["detections"]
    
except Exception as e:
    logger.error(f"Не вдалося підключитися до MongoDB: {e}")


__all__ = ['collection']

def save_detection(data):
    if collection is None:
        logger.error("MongoDB not connected, cannot save detection")
        raise ValueError("MongoDB not connected")
    collection.insert_one(data)
