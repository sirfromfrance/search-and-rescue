from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class Coordinates(BaseModel):
    lat: float
    lng: float


class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class PersonDetection(BaseModel):
    photo_url: Optional[str] = None
    photo_coordinates: Optional[Coordinates] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    timestamp: datetime
