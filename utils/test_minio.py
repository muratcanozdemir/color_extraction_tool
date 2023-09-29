from minio import Minio

# Create a client
minio_client = Minio(
    "192.168.0.3:9000",
    access_key="minio",
    secret_key="minio123",
    secure=False  # set to True for HTTPS
)

# List buckets
buckets = minio_client.list_buckets()
for bucket in buckets:
    print(bucket.name)

# List objects in a bucket
objects = minio_client.list_objects("color-extractor-project")
for obj in objects:
    print(obj.object_name)

# Download an object
result = minio_client.get_object("color-extractor-project", "results/imageid.json")
with open("downloaded-file", "wb") as file_data:
    for d in result.stream(32 * 1024):
        file_data.write(d)

result = minio_client.get_object("color-extractor-project", "images/imageid.jpg")
with open("downloaded-file", "wb") as file_data:
    for d in result.stream(32 * 1024):
        file_data.write(d)
