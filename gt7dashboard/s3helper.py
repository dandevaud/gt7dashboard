import io
import os
import pickle
from minio import Minio
from minio.error import S3Error

class S3Client:
    def __init__(self, bucket_name: str = None):
        # Read configuration from environment variables
        self.endpoint = os.environ.get("S3_ENDPOINT")
        self.access_key = os.environ.get("S3_ACCESS_KEY")
        self.secret_key = os.environ.get("S3_SECRET_KEY")
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET_NAME")

        if not all([self.endpoint, self.access_key, self.secret_key, self.bucket_name]):
            raise ValueError("Missing one or more required S3 environment variables.")

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )

        # Ensure bucket exists
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    # TODO: Refactor remove duplication with s3helper in gt7dashboard
    def upload_json_object(self, obj, object_name, bucket_name: str = None):
        if bucket_name is None:
            bucket_name = self.bucket_name         

        # Ensure bucket exists
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

        try:
            json_data =  pickle.dumps(obj)
            self.client.put_object(
                bucket_name,
                object_name,
                data=io.BytesIO(json_data),
                length=len(json_data),
                content_type="application/json"
            )
            print(f"JSON object uploaded to bucket '{bucket_name}' as '{object_name}'.")
        except S3Error as err:
            print(f"Error uploading JSON object: {err}")

    def upload_file(self, file_path, object_name=None, bucket_name: str = None):
        
        if bucket_name is None:
            bucket_name = self.bucket_name

        if object_name is None:
            object_name = os.path.basename(file_path)
       
        # Ensure bucket exists
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as file_data:
                self.client.put_object(
                    bucket_name,
                    object_name,
                    data=file_data,
                    length=file_size,
                    content_type="application/octet-stream"
                )
            print(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
        except S3Error as err:
            print(f"Error uploading file: {err}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def download_file(self, object_name, file_path=None, bucket_name: str = None):     
        if bucket_name is None:
            bucket_name = self.bucket_name     

        if file_path is None:
            file_path = object_name

        try:
            response = self.client.get_object(bucket_name, object_name)
            with open(file_path, "wb") as file_data:
                for chunk in response.stream(32 * 1024):
                    file_data.write(chunk)
            response.close()
            response.release_conn()
            print(f"File '{object_name}' downloaded from bucket '{bucket_name}' to '{file_path}'.")
        except S3Error as err:
            print(f"Error downloading file: {err}")
        except Exception as e:
            print(f"Unexpected error: {e}")


    def list_objects(self, bucket_name: str = None ):       
        if bucket_name is None:
            bucket_name = self.bucket_name
        try:
            objects = self.client.list_objects(bucket_name)
            return [obj.object_name for obj in objects]
        except S3Error as err:
            print(f"Error listing objects: {err}")
            return []

    def get_object(self, object_name, bucket_name: str = None):
        if bucket_name is None:
            bucket_name = self.bucket_name       
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return pickle.loads(data)
        except S3Error as err:
            print(f"Error retrieving object '{object_name}': {err}")
            return None
    
    