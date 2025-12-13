import csv
from faker import Faker
import datetime
import random

from kafka import KafkaProducer
import json
import time

fake = Faker()

def generate_users_data(num_users=100):
	with open('/app/data/Users.csv' , 'w' , newline='') as file:
		writer = csv.writer(file)
		user_list = []
		writer.writerow(['user_id' , 'signup_date' , 'country'])

		for i in range(1, num_users + 1):
			user_id = f'user{i}'
			signup_date = fake.date_time_this_decade().strftime('%Y-%m-%d %H:%M:%S')
			country = fake.country()
			user_list.append(user_id)
			writer.writerow([user_id , signup_date ,country])
	return user_list

def generate_products_data(num_products=200):
	with open('/app/data/Products.csv', 'w' , newline='') as file1:
		writer1 = csv.writer(file1)
		prod_list = []
		l = ['electronics', 'books', 'clothing', 'home goods', 'sports']
		writer1.writerow(['product_id' , 'category' , 'price'])

		for i in range(1 , num_products + 1):
			product_id = f'prod{i}'
			category = random.choice(l)
			price = round(random.uniform(5.0, 1000.0), 2)

			prod_list.append(product_id)
			writer1.writerow([product_id , category ,price])
	return prod_list

def generate_orders_data(user_ids, product_ids, num_orders=1000):
	with open('/app/data/Orders.csv' , 'w' , newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['order_id', 'user_id', 'product_id', 'quantity','total_amount'])

		for i in range(1 , num_orders + 1):
			order_id = f'ord_{i}'
			user_id = random.choice(user_ids)
			product_id = random.choice(product_ids)
			quantity = round(random.uniform(1, 100))
			total_amount = round(random.uniform(5.0, 1000.0), 2)

			writer.writerow([order_id,user_id,product_id,quantity,total_amount,])

#Streaming data part
def generate_click_events(user_ids):
	producer = None
	for _ in range(10):
		try:
			producer = KafkaProducer(
				bootstrap_servers=['kafka:29092'],
				value_serializer=lambda v: json.dumps(v).encode('utf-8')
			)
			print("Kafka connection successful")
			break
		except Exception as e:
			print(f"Kafka connection failed, retrying... {_+1}/10")
			time.sleep(5)
	if producer is None:
		print("Failed to connect to Kafka after multiple attempts. Exiting.")
		return

	l =['view_item', 'add_to_cart', 'checkout']
	event_id_counter = 0
	while(1):
		user_id = random.choice(user_ids)
		url = fake.uri_path()
		f_timestamp = datetime.datetime.now().isoformat()
		event = random.choice(l)

		event_id_counter += 1
		event_dic = {
			"eventid" : f'evt{event_id_counter}',
			"userid": user_id,
			"url": url,
			"timestamp": f_timestamp,
			"action": event
			}

		producer.send('clicks_topic' , event_dic)

		print(event_dic)
		time.sleep(1)

if __name__ == "__main__":
	
	num_users=100
	num_products=200
	num_orders=100
	
	user_ids = generate_users_data(num_users)
	product_ids =generate_products_data(num_products)

	generate_orders_data(user_ids , product_ids ,num_orders)
	generate_click_events(user_ids)