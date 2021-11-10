from enum import Enum
import pymongo as mongo
from bson.objectid import ObjectId

import settings as settings
from src.models.mongo_document_base import MongoDocumentBase, SimpleMongoDocumentBase


class Collection(Enum):
    APPLICATION_LOG = 'application_log'
    WORKSPACE = "workspace"
    USER = "user"
    TEAM = 'team'
    INVITATION = 'invitation'
    PROJECT = 'project'
    TESTING = 'testing'
    DIAGRAM = 'diagram'
    MODEL = 'model'
    MODEL_REPRESENTATION = 'model_representation'


def insert(collection: Collection, item: MongoDocumentBase) -> dict:
    """
    Inserts a document into the given collection.
    Note that the _id field will be ignored on insertion
    :param collection: Collection to insert into
    :param item: the item to insert
    :return: the inserted item with its given id
    """
    d = item.as_dict()
    # NOTE: We always delete the _id field, since MongoDB should handle that
    # This also removes issues where errors has led to garbage values in the _id field
    if '_id' in d:
        del d['_id']

    result = __get_collection(collection).insert_one(d)
    if result.acknowledged:
        return find_one(collection, _id=result.inserted_id)


def find(collection: Collection, **kwargs) -> list:
    """
    Find all items matching the query in kwargs.
    Note that `_id` must be of type ObjectId if used.
    A special parameter, `id`, will automatically be converted from string to ObjectId and be used in the query as `_id`.
    :param collection: collection to search
    :param kwargs: search params in key-value form
    :return: the resulting list of items as dicts
    """
    if kwargs.get('id') is not None:
        if isinstance(kwargs['id'], str):
            kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']

    return list(__get_collection(collection).find(kwargs))


def find_one(collection: Collection, **kwargs) -> dict:
    """
    Find the first item that matches the query in kwargs.
    Note that `_id` must be of type ObjectId if used.
    A special parameter, `id`, will automatically be converted from string to ObjectId and be used in the query as `_id`.
    :param collection: collection to search
    :param kwargs: search params in key-value form
    :return: the first item matching the query
    """
    if kwargs.get('id') is not None:
        if isinstance(kwargs['id'], str):
            kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']

    return __get_collection(collection).find_one(kwargs)


def delete(collection: Collection, **kwargs) -> bool:
    """
    Delete the first item that matches the query in kwargs.
    Note that `_id` must be of type ObjectId if used.
    A special parameter, `id`, will automatically be converted from string to ObjectId and be used in the query as `_id`.
    :param collection: collection to delete from
    :param kwargs: search params in key-value form
    :return: True if an item was deleted, otherwise False
    """
    if kwargs.get('id') is not None:
        if isinstance(kwargs['id'], str):
            kwargs['_id'] = ObjectId(kwargs['id'])
        del kwargs['id']
    delete_result = __get_collection(collection).delete_one(kwargs)
    return delete_result.deleted_count > 0


def __purge(collection: Collection):
    """
    Utility function that deletes all items in a given collection
    Intended for testing purposes, do not use in code
    :param collection: collection to query
    :return:
    """
    __get_collection(collection).delete_many({})


def update(collection: Collection, item: MongoDocumentBase) -> dict:
    """
    Updates a document with new values.
    Document is found by _id
    :param collection: collection to query
    :param item: item to update
    :return: updated item
    """
    query = {'_id': item.id}
    values = {'$set': item.as_dict()}
    update_result = __get_collection(collection).update_one(query, values)
    if update_result.modified_count > 0:
        return find_one(collection, _id=item.id)


def push(collection: Collection, document_id: ObjectId, field_name: str, item) -> bool:
    """
    Inserts an item into a list on a document.
    :rtype: object
    :param collection: collection to query
    :param document_id:document id
    :param field_name: list field on document
    :param item: Document to modify
    :return:  True if a document was modified
    """
    if isinstance(item, SimpleMongoDocumentBase) or isinstance(item, MongoDocumentBase):
        item = item.as_dict()

    # NOTE: Consider changing $push to $addToSet to avoid dupes in list
    update_result = __get_collection(collection).update_one(
        {'_id': document_id},
        {'$push': {field_name: item}}
    )
    return update_result.modified_count > 0


def pull(collection: Collection, document_id: ObjectId, field_name: str, item) -> bool:
    """
    Removes an item from a list on a document.
    :param collection: collection to query
    :param document_id: document id
    :param field_name: list field on document
    :param item: Document to modify
    :return: True if a document was modified
    """
    update_result = __get_collection(collection).update_one(
        {'_id': document_id},
        {'$pull': {field_name: item}}
    )
    return update_result.modified_count > 0


def __get_collection(collection: Collection):
    client = mongo.MongoClient(
        f'{settings.MONGO_PROTOCOL}://{settings.MONGO_USER}:{settings.MONGO_PW}@{settings.MONGO_HOST}/{settings.MONGO_DEFAULT_DB}?retryWrites=true&w=majority')
    db = client.get_default_database()
    return db[collection.value]
