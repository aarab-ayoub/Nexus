import os
import boto3
from botocore.exceptions import NoCredentialsError
import datetime
from kafka import KafkaConsumer
import json
import time

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


def ingest_streaming_data(s3_client):
	consumer = KafkaConsumer(
		'clicks_topic',
		bootstrap_servers=['localhost:9092'],
		group_id='s3-ingestion-group',
		auto_offset_reset='earliest',
		value_deserializer=lambda x: json.loads(x.decode('utf-8'))
	)
	print("kafka consumer created, listening to clicks_topic")

	batch = []
	batch_size = 50
	last_upload_time = time.time()
	max_interval = 60
	try:
		for message in consumer:
			batch.append(message.value)

			current_time = time.time()
			diff_time = current_time - last_upload_time

			if len(batch) >= batch_size or diff_time >= max_interval:
				if batch:
					now = datetime.datetime.now()
					filename = f"{now.strftime('%Y/%m/%d/%H-%M-%S')}-clickstream.json"

					file_content = '\n'.join([json.dumps(record) for record in batch])

					try:
						s3_client.put_object(
							Bucket=BUCKET_NAME,
							Key=filename,
							Body=file_content.encode('utf-8')
						)
						print(f"Uploaded {filename} to S3")
					except Exception as e:
						print(f"Error uploading to S3: {e}")
					batch = []
					last_upload_time = current_time


			print(f"Received message: {message.value}")
	except KeyboardInterrupt:
		print("Stopping Kafka consumer")


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

		ingest_streaming_data(s3_client)
