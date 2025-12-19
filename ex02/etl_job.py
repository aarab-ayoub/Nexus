from pyspark.sql import SparkSession
import pyspark.sql.functions as F

def connection_to_postgres():
	postgres_url = "jdbc:postgresql://postgres:5432/ecommerce"
	postgres_properties = {
		"user": "admin",
		"password": "admin",
		"driver": "org.postgresql.Driver"
	}
	return postgres_url, postgres_properties

def spark_connection():
	aws_access_key_id = "minioadmin"
	aws_secret_access_key = "minioadmin"
	minio_endpoint = "http://minio:9000"

	spark = SparkSession.builder \
        .appName("ECommerceETL") \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id) \
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .getOrCreate()
        # .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        # .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        # .config("spark.hadoop.fs.s3a.connection.timeout", "30000") \
        # .config("spark.hadoop.fs.s3a.connection.establish.timeout", "30000") \
        # .config("spark.hadoop.fs.s3a.attempts.maximum", "3") \
	return spark

def batch_ETL(spark, postgres_url, postgres_properties):
	
	processing_date_str = "2025/12/19"
	base_s3_path = f"s3a://raw-data/{processing_date_str}"
		
	users_df = spark.read.csv(f'{base_s3_path}/Users.csv', header=True, inferSchema=True)
	products_df = spark.read.csv(f'{base_s3_path}/Products.csv', header=True, inferSchema=True)
	orders_df = spark.read.csv(f'{base_s3_path}/Orders.csv', header=True, inferSchema=True)

	print("cleaning it ...")

	users_df.printSchema()
	products_df.printSchema()
	orders_df.printSchema()

	users_df=users_df.dropna()
	users_df = users_df.withColumnRenamed("user id", "user_id")\
		.withColumn("signup_date" , F.to_timestamp("signup_date"))
		
	#products turn jaja
	products_df=products_df.dropna()
	products_df=products_df.withColumnRenamed("product id" , "product_id")
		
	#orders turn jaja
	orders_df=orders_df.dropna()
	orders_df=orders_df.withColumnRenamed("order id" ,"order_id")\
		.withColumnRenamed("user id" , "user_id")\
		.withColumnRenamed("product id" , "product_id")
	
	# print(users_df.head())
	# print(products_df.head())
	# print(orders_df.head())

	#joining them into one table 

	result = orders_df.join(users_df , on="user_id" , how="inner")
	final_result = result.join(products_df , on="product_id" , how="inner")

	# final_result.printSchema()
	# final_result.show(5)

	final_result.write\
		.mode("overwrite")\
		.jdbc(url=postgres_url, table="fact_orders", properties=postgres_properties)

	print("loaded succesfuly")

	
def main():

	spark = spark_connection()
	postgres_url, postgres_properties = connection_to_postgres()

	print("connecting to minio")


	try :
		batch_ETL(spark, postgres_url, postgres_properties)

	except Exception as e:
		print(e)
	
	finally:
		spark.stop()

if __name__ == "__main__":
	main()