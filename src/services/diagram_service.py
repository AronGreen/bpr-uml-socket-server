from bson import ObjectId

import src.repository as db
from src.models.diagram import Diagram


def find_one(diagram_id) -> Diagram:
    _id = diagram_id
    if type(diagram_id) == str:
        _id = ObjectId(diagram_id)
    if type(_id) is not ObjectId:
        raise TypeError
    diagram = db.find_one(db.Collection.PROJECT, id=_id)
    return Diagram.from_dictionary(diagram)
