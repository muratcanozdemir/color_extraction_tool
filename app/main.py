from fastapi import FastAPI, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
import hashlib
import io
import re
from tasks.tasks import process_image
import base64
from pathlib import Path
import json
from configs.cache import cache
import logging.config
from configs.logging_config import LOGGING_CONFIG
from configs.cache import minio_client, BUCKET_NAME

app = FastAPI()

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(BASE_PATH / ".." / "templates" / "index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/health/")
async def health_check():
    try:
        # dummy method, normally we'd have some proper health checks
        return {"status": "healthy"}
    except:
        raise HTTPException(status_code=500, detail="Service not healthy")

@app.post("/webhook/")
async def webhook(request: Request):
    data = await request
    logger.info(msg=data)
    status = data.get('status')
    image_id = data.get('image_id')
    if status == "ok" and image_id:
        url = app.url_path_for('display_results', image_id=image_id)
        logger.info(msg=url)
        result = requests.get(url=f"http://web:8000{url}", data=data)
        return result
    return {"status": "error", "message": "Processing not completed"}

@app.get("/display/{image_id}/", response_class=HTMLResponse)
async def display_results(request: Request):
    try:
        data = await request
        image_id = data.get('image_id')
        result_data = data.get("dominant_colors")
        image_obj = minio_client.get_object(BUCKET_NAME, f'images/{image_id}.jpg')
        logger.info(image_obj)
        image_data = base64.b64encode(image_obj.read()).decode()
    except Exception as e:
        logger.error(f"Error: {e}, {e.__traceback__}")
        logger.error("Something is obviously wrong")
        raise HTTPException(status_code=404, detail="Results not found")

    color_boxes = "".join([f'<div class="color-box" style="background-color: {rgb_string_to_hex(color["color"])}"></div>' for color in result_data['color_info']])
    logger.info(msg=color_boxes)
    return templates.TemplateResponse("results.html", {"image_data": image_data, "color_boxes": color_boxes})

@app.post("/extract-colors/")
async def extract_colors(file: UploadFile, n_colors: int = 3):
    image_data = await file.read()
    image_hash = hashlib.md5(image_data).hexdigest()
    if image_hash in cache:
        return RedirectResponse(url=f'/display/{image_hash}/')
    
    try:
        # Check if bucket exists, if not create it
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)

        minio_client.put_object(
            BUCKET_NAME,
            f'images/{image_hash}.jpg',
            data=io.BytesIO(image_data),
            length=len(image_data),
            content_type="image/jpeg",
        )
        logger.info(msg=f"Object {image_hash} is stored in MinIO")
    except Exception as e:
        logger.error(f"Failed to save image to Minio: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image")
    
    task = process_image.apply_async(args=[image_data, n_colors])
    return {"task_id": task.id, "status": "Processing"}

def rgb_string_to_hex(rgb_string):
    rgb_values = re.findall(r'\d+', rgb_string)
    rgb_integers = [int(value) for value in rgb_values]
    return '#{:02X}{:02X}{:02X}'.format(*rgb_integers)