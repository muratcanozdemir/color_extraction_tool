from celery import shared_task, Celery
from app.color_extraction import get_dominant_colors, preprocess_image, format_color_info
import cv2
import io
import numpy as np
import json
import hashlib
import requests
from configs.cache import cache
import logging.config
from configs.logging_config import LOGGING_CONFIG
from configs.cache import minio_client, BUCKET_NAME

WEBHOOK_URL = "http://web:8000/webhook/"

celery_app = Celery('tasks')

# Load the configuration file
celery_app.config_from_object('configs.celery_config')

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@shared_task
def process_image(image_data, n_colors):
    image_hash = hashlib.md5(image_data).hexdigest()
    cached_result = cache.get(image_hash)
    if cached_result:
        logger.info(msg=f"cache found {cached_result}")
        requests.post(WEBHOOK_URL, json=cached_result)
        return json.loads(cached_result)
    
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    preprocessed_image = preprocess_image(image)
    dominant_colors = get_dominant_colors(preprocessed_image, n_colors)
    color_info = format_color_info(dominant_colors)

    result = json.dumps(
        {
            "dominant_colors": color_info, 
            "status": "ok", 
            "image_id": image_hash
        })
    try:
        results_pack = result.encode()
        logger.info(msg=results_pack)
        minio_client.put_object(
            BUCKET_NAME,
            f'results/{image_hash}.json',
            data=io.BytesIO(results_pack),
            length=len(results_pack)
        )
        logger.info(f"Object {image_hash} is saved")
    except Exception as e:
        logger.error(f"Failed to save the result to Minio: {e}")
    
    cache[image_hash] = result
    logger.info(msg=result)
    requests.post(WEBHOOK_URL, json=result)
    return result
