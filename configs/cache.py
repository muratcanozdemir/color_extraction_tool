from cachetools import LRUCache
from minio import Minio

cache = LRUCache(maxsize=100)  

BUCKET_NAME = "color-extractor-project"
minio_client = Minio(
    endpoint="minio:9000",
    access_key="minio",
    secret_key="minio123",
    secure=False  # set to True in a production environment with HTTPS
)