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


def join(
        local_collection: Collection,
        local_field: str,
        foreign_collection: Collection,
        foreign_field: str,
        to_field: str,
        unwind: bool = False,
        **match_args) -> list:
    """
    Returns results from the `local_collection` with the matching documents in the `foreign_collection` as sub-documents.

    Equivalent to a left outer join.

    If `unwind` is True, an unwind step on to_field is added to the pipeline.
    From MongoDB documentation:
    "Deconstructs an array field from the input documents to output a document for each element.
    Each output document is the input document with the value of the array field replaced by the element."

    A filter step will be added to the beginning of the pipeline if filtering arguments are added to `match_args`.

    :param local_collection: collection add sub-documents to
    :param local_field: field to join on in local collection
    :param foreign_collection: collection to join
    :param foreign_field: field to join on in foreign collection
    :param to_field: field containing the results of the join
    :param unwind: if true, unwinds on to_field
    :param match_args: arguments to filter local collection by
    :return: list of resulting documents
    """

    if 'id' in match_args:
        if match_args['id'] is not None:
            match_args['_id'] = ObjectId(match_args['id'])
        del match_args['id']

    pipeline = [
            {
                '$lookup': {
                    'from': foreign_collection.value,
                    'localField': local_field,
                    'foreignField': foreign_field,
                    'as': to_field
                }
            }
        ]

    if match_args:
        pipeline.insert(0, {'$match': match_args})
    if unwind:
        pipeline.append({'$unwind': f'${to_field}'})

    result = __get_collection(local_collection).aggregate(pipeline)
    return list(result)


def __get_collection(collection: Collection):
    client = mongo.MongoClient(
        f'{settings.MONGO_PROTOCOL}://{settings.MONGO_USER}:{settings.MONGO_PW}@{settings.MONGO_HOST}/{settings.MONGO_DEFAULT_DB}?retryWrites=true&w=majority')
    db = client.get_default_database()
    return db[collection.value]
