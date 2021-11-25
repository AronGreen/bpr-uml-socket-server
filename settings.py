import os
from dotenv import load_dotenv

load_dotenv()

APP_PORT = int(os.environ['APP_PORT'])

REST_DOMAIN = os.environ['REST_DOMAIN']

MONGO_CONN = {
    'protocol': os.environ['MONGO_PROTOCOL'],
    'default_db': os.environ['MONGO_DEFAULT_DB'],
    'pw': os.environ['MONGO_PW'],
    'host': os.environ['MONGO_HOST'],
    'user': os.environ['MONGO_USER']
}
