import os
from dotenv import load_dotenv

load_dotenv()


APP_PORT = int(os.environ['APP_PORT'])

MONGO_PROTOCOL = os.environ['MONGO_PROTOCOL']
MONGO_USER = os.environ['MONGO_USER']
MONGO_PW = os.environ['MONGO_PW']
MONGO_HOST = os.environ['MONGO_HOST']
MONGO_DEFAULT_DB = os.environ['MONGO_DEFAULT_DB']
