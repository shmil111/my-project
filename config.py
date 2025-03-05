import os
from dotenv import load_dotenv

# Load .env file from the secure location
load_dotenv('C:/Documents/credentials/myproject/.env')

API_KEY = os.getenv('API_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')
SECRET_TOKEN = os.getenv('SECRET_TOKEN') 