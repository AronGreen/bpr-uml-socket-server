import pymongo
import settings

def get_collection(collection):
    client = pymongo.MongoClient(f"{settings.MONGO_PROTOCOL}://{settings.MONGO_USER}:{settings.MONGO_PW}@{settings.MONGO_HOST}/{settings.MONGO_DEFAULT_DB}?retryWrites=true&w=majority")
    db = client.get_default_database()
    return db[collection]

col = get_collection("test_coll")

item = {"name": "Aron2", "fingerCount": 10}
col.insert_one(item)
