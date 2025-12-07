import csv
from faker import Faker
import datetime
import random

fake = Faker()

def generate_users_data(num_users=100):
	with open('Users.csv' , 'w' , newline='') as file:
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
	with open('Products.csv', 'w' , newline='') as file1:
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
	with open('Orders.csv' , 'w' , newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['order_id', 'user_id', 'product_id', 'quantity','total_amount'])

		for i in range(1 , num_orders + 1):
			order_id = f'ord_{i}'
			user_id = random.choice(user_ids)
			product_id = random.choice(product_ids)
			quantity = round(random.uniform(1, 100))
			total_amount = round(random.uniform(5.0, 1000.0), 2)

			writer.writerow([order_id,user_id,product_id,quantity,total_amount,])


if __name__ == "__main__":
	
	num_users=100
	num_products=200
	num_orders=1000
	
	user_ids = generate_users_data(num_users)
	product_ids =generate_products_data(num_products)

	generate_orders_data(user_ids , product_ids ,num_orders)