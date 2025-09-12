import io
import os
import pickle
from minio import Minio
from minio.error import S3Error


def upload_json_object(obj, object_name):
    # Read configuration from environment variables
    endpoint = os.environ.get("S3_ENDPOINT")
    access_key = os.environ.get("S3_ACCESS_KEY")
    secret_key = os.environ.get("S3_SECRET_KEY")
    bucket_name = os.environ.get("S3_BUCKET_NAME")
    secure = os.environ.get("S3_SECURE", "true").lower() == "true"

    if not all([endpoint, access_key, secret_key, bucket_name]):
        raise ValueError("Missing one or more required S3 environment variables.")

    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )

    # Ensure bucket exists
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    try:
        json_data =  pickle.dumps(obj)
        client.put_object(
            bucket_name,
            object_name,
            data=io.BytesIO(json_data),
            length=len(json_data),
            content_type="application/json"
        )
        print(f"JSON object uploaded to bucket '{bucket_name}' as '{object_name}'.")
    except S3Error as err:
        print(f"Error uploading JSON object: {err}")

# Example usage:
# upload_file("localfile.txt")