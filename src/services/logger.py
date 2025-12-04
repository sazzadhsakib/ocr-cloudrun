import logging
import os
import json

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("ocr_service")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/ocr_service.log")
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
