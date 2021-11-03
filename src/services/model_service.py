from bson import ObjectId

import src.repository as db
from src.models.model import *
from src.util import ensure_object_id


def find_one(model_id) -> Model:
    _id = ensure_object_id(model_id)
    model = db.find_one(db.Collection.MODEL, id=_id)
    return Model.parse(model)


def create(data) -> Model:
    model = Model.parse(data)
    return Model.parse(db.insert(db.Collection.MODEL, model))
