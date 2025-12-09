import os
import boto3
from botocore.exceptions import NoCredentialsError
import datetime

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = 'raw-data'

LOCAL_DATA_PATH = '../ex00/data/'

def get_s3_client():
	try:
		client = boto3.client(
			's3',
			endpoint_url=f'http://{MINIO_ENDPOINT}',
			aws_access_key_id=MINIO_ACCESS_KEY,
			aws_secret_access_key=MINIO_SECRET_KEY,
			config=boto3.session.Config(signature_version='s3v4')
		)
		print("S3 client created successfully")
		return client
	
	except NoCredentialsError:
		print("Credentials not available")
		return None


def upload_files_to_s3(client ,bucket , local_path , s3_object_name):
	try:
		client.upload_file(local_path, bucket, s3_object_name)
		print(f"Uploaded {local_path} to s3://{bucket}/{s3_object_name}")
		return 1
	except FileNotFoundError:
		print(f"The file {local_path} was not found")
		return 0
	except NoCredentialsError:
		print("Credentials not available")
		return 0


if __name__ == "__main__":
	s3_client = get_s3_client()
	if s3_client:
		now= datetime.datetime.now()
		day = now.strftime("%d")
		month = now.strftime("%m")
		year = now.strftime("%Y")

		files = os.listdir(LOCAL_DATA_PATH)
		total_uploaded = 0
		# bucket = s3_client.create_bucket(Bucket=BUCKET_NAME)
		for i in files:
			if(i.endswith('.csv') == True):
				s3_object_name = f"{year}/{month}/{day}/{i}"
				local_files = os.path.join(LOCAL_DATA_PATH , i)
				uploaded = upload_files_to_s3(s3_client , BUCKET_NAME , local_files , s3_object_name)
				total_uploaded += uploaded
			elif not os.path.isdir(LOCAL_DATA_PATH):
				print(f"{LOCAL_DATA_PATH} is not a directory")
		print(f"Total files uploaded: {total_uploaded}")

