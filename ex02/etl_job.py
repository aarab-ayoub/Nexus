from pyspark.sql import SparkSession
import pyspark.sql.functions as F

def main():

	aws_access_key_id = "minioadmin"
	aws_secret_access_key = "minioadmin"
	minio_endpoint = "http://minio:9000"

	spark = SparkSession.builder \
        .appName("ECommerceETL") \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id) \
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config("spark.hadoop.fs.s3a.connection.timeout", "30000") \
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "30000") \
        .config("spark.hadoop.fs.s3a.attempts.maximum", "3") \
        .getOrCreate()

	print("connecting to minio")

	processing_date_str = "2025/12/14"
	base_s3_path = f"s3a://raw-data/{processing_date_str}"

	try :
		users_df = spark.read.csv(f'{base_s3_path}/Users.csv', header=True, inferSchema=True)
		products_df = spark.read.csv(f'{base_s3_path}/Products.csv', header=True, inferSchema=True)
		orders_df = spark.read.csv(f'{base_s3_path}/Orders.csv', header=True, inferSchema=True)

		print("reading the data ")

		users_df.show(5)
		products_df.show(5)
		orders_df.show(5)
	
	except Exception as e:
		print(e)
	
	finally:
		spark.stop()

if __name__ == "__main__":
	main()