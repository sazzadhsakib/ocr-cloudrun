from typing import List
from pydantic import BaseModel

class Metadata(BaseModel):
    width: int
    height: int
    format: str

class OCRResult(BaseModel):
    filename: str
    success: bool
    text: str
    confidence: float
    metadata: Metadata
    processing_time_ms: int

class SingleOCRResponse(BaseModel):
    success: bool
    text: str
    confidence: float
    metadata: Metadata
    processing_time_ms: int

class BatchOCRResponse(BaseModel):
    success: bool
    total_images: int
    total_processing_time_ms: int
    results: List[OCRResult]
