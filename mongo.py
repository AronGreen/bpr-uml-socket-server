import pymongo
import settings

def get_collection(collection):
    client = pymongo.MongoClient(host=settings.MONGO_HOST, port=settings.MONGO_PORT, )
    con = client[settings.MONGO_DB]
    return con[collection]

col = get_collection("test_coll")

item = {"name": "Aron2", "fingerCount": 10}
col.insert_one(item)

