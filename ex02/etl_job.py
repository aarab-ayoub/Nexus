from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
# import snowflake.connector
# from snowflake.connector.pandas_tools import write_pandas


def connection_to_postgres():
	postgres_url = "jdbc:postgresql://postgres:5432/ecommerce"
	postgres_properties = {
		"user": "admin",
		"password": "admin",
		"driver": "org.postgresql.Driver"
	}
	return postgres_url, postgres_properties

def connection_to_Bigquery():
	bigquery_url = "jdbc:bigquery://https://www.googleapis.com/bigquery/v2:443;ProjectId=your_project_id;DatasetId=your_dataset_id;"
	bigquery_properties = {
		"user": "your_username",
		"password": "your_password",
		"driver": "com.simba.googlebigquery.jdbc.Driver"
	}
	return bigquery_url, bigquery_properties

def connection_to_snowflake():
	cnx = snowflake.connector.connect(
		user='your_username',
		password='your_password',
		account='your_account',
		warehouse='your_warehouse',
		database='your_database',
		schema='your_schema'
	)
	return cnx

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
	
	processing_date_str = "2026/01/14"
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
	pass

def stream_ETL(spark, postgres_url, postgres_properties):
	
	click_stream_schema = StructType([
		StructField("eventid", StringType(), True),
		StructField("userid", StringType(), True),
		StructField("url", StringType(), True),
		StructField("timestamp", TimestampType(), True),
		StructField("action", StringType(), True)
	])

	#1st line mean read the stream from kafka topic
	#2nd line mean set the kafka bootstrap server address
	#3rd line mean subscribe to the topic named click_topic
	#4th line mean set the starting offsets to earliest
	#5th line mean load the stream
	kafka_df = spark.readStream \
		.format("kafka") \
		.option("kafka.bootstrap.servers", "kafka:29092") \
		.option("subscribe", "clicks_topic") \
		.option("startingOffsets", "earliest") \
		.load()
	
	# Extract the JSON value from the Kafka message and parse it
	#1st line mean cast the value to string
	#2nd line mean parse the json string using the defined schema
	#3rd line mean select all the fields from the parsed json
	json_df = kafka_df.selectExpr("CAST(value AS STRING) as json_value") \
		.select(F.from_json("json_value", click_stream_schema).alias("data")) \
		.select("data.*")
	
	# Ensure we have an event_timestamp column of TimestampType
	click_df = json_df.withColumnRenamed("timestamp", "event_timestamp")

	page_views = click_df\
		.withWatermark("event_timestamp", "1 minute")\
		.groupBy(
			F.window("event_timestamp", "1 minute"),
			"action"
		)\
		.count()\
		.withColumnRenamed("count", "action_count")

	# Flatten the window struct (start,end) into separate timestamp columns for JDBC
	page_views_flat = page_views.withColumn("window_start", F.col("window.start"))\
		.withColumn("window_end", F.col("window.end"))\
		.drop("window")

	# use a top-level function for foreachBatch to avoid serialization issues
	def write_batch(df, epoch_id):
		df.write.mode("append").jdbc(url=postgres_url, table="fact_page_views", properties=postgres_properties)

	query = page_views_flat.writeStream \
	    .outputMode("update") \
	    .foreachBatch(write_batch) \
	    .trigger(processingTime='1 minute') \
	    .start()
	
	print("Streaming query has been started.")
	query.awaitTermination()
	
def main():

	spark = spark_connection()
	postgres_url, postgres_properties = connection_to_postgres()

	print("connecting to minio")
	try :

		batch_ETL(spark, postgres_url, postgres_properties)
		stream_ETL(spark, postgres_url, postgres_properties)
	except Exception as e:
		print(e)
	finally:
		spark.stop()

if __name__ == "__main__":
	main()