import os
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_DB = os.environ['MONGO_DB']
PORT = int(os.environ['PORT'])
