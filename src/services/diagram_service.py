from __future__ import annotations

from typing import List, Union

from bpr_data.models.model import ModelRepresentation
from bpr_data.repository import Repository, Collection
from bpr_data.models.diagram import Diagram
from bson import ObjectId

import settings

# TODO: Move to data module
MongoId = Union[ObjectId, str]

db = Repository.get_instance(**settings.MONGO_CONN)


def get_diagram(diagram_id: MongoId) -> Diagram:
    diagram = db.find_one(Collection.DIAGRAM, id=diagram_id)
    if diagram is not None:
        return Diagram.from_dict(diagram)


def get_diagrams_for_model(model_id: MongoId) -> List[Diagram]:
    representation_ids = \
        [r.id for r in db.find(Collection.MODEL_REPRESENTATION, ModelRepresentation, modelId=ObjectId(model_id))]
    return db.find(Collection.DIAGRAM, Diagram, models={'$in': representation_ids})
