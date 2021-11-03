from enum import Enum
import pymongo as mongo
from bson.objectid import ObjectId

import src.settings as settings
from src.models.mongo_document_base import MongoDocumentBase


class Collection(Enum):
    APPLICATION_LOG = 'socket_log'
    MODEL = "model"
    PROJECT = "project"


def insert(collection: Collection, item: MongoDocumentBase):
    d = item.as_dict()
    if '_id' in d and d['_id'] is None:
        del d['_id']

    result = __get_collection(collection).insert_one(d)
    if result.acknowledged:
        return find_one(collection, id=result.inserted_id)


def find(collection: Collection, **kwargs):
    if kwargs.get('id') is not None:
        kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']

    return list(__get_collection(collection).find(kwargs))


def find_one(collection: Collection, **kwargs):
    if kwargs.get('id') is not None:
        kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']

    return __get_collection(collection).find_one(kwargs)


def delete(collection: Collection, **kwargs):
    if kwargs.get('id') is not None:
        kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']
    __get_collection(collection).delete_one(kwargs)


def purge(collection: Collection):
    __get_collection(collection).delete_many({})


def update(collection: Collection, item: MongoDocumentBase):
    query = {'_id': item.id}
    values = {'$set': item.to_dict()}
    __get_collection(collection).update_one(query, values)


def push(collection: Collection, document_id: ObjectId, field_name: str, item):
    __get_collection(collection).update_one(
        {'_id': document_id},
        {'$push': {field_name: item}}
    )


def pull(collection: Collection, document_id: ObjectId, field_name: str, item):
    __get_collection(collection).update_one(
        {'_id': document_id},
        {'$pull': {field_name: item}}
    )


def __get_collection(collection: Collection):
    client = mongo.MongoClient(
        f'{settings.MONGO_PROTOCOL}://{settings.MONGO_USER}:{settings.MONGO_PW}@{settings.MONGO_HOST}/{settings.MONGO_DEFAULT_DB}?retryWrites=true&w=majority')
    db = client.get_default_database()
    return db[collection.value]
