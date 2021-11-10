from __future__ import annotations

from bson import ObjectId

import src.repository as db
from src.models.diagram import Diagram
from src.models.model import Model, ModelRepresentation


def find_one(model_id: str) -> Model:
    model = db.find_one(db.Collection.MODEL, id=model_id)
    return Model.parse(model)


def create(model: dict, representation: dict, diagram: Diagram) -> (Model, ModelRepresentation):
    model['_id'] = None
    model['projectId'] = diagram.projectId
    created_model = Model.parse(db.insert(db.Collection.MODEL, Model.parse(model)))

    representation['_id'] = None
    representation['modelId'] = created_model.id
    representation['diagramId'] = diagram.id
    representation = ModelRepresentation.from_dict(representation)
    created_representation = ModelRepresentation.from_dict(
        db.insert(db.Collection.MODEL_REPRESENTATION, representation))

    db.push(db.Collection.DIAGRAM, diagram.id, 'models', item=created_representation.id)

    return created_model, created_representation
