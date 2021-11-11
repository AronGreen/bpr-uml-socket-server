from __future__ import annotations

from bson import ObjectId

import src.repository as db
from src.models.diagram import Diagram
from src.models.model import Model, ModelRepresentation, FullModelRepresentation


def get_model(model_id: str) -> Model:
    model = db.find_one(db.Collection.MODEL, id=model_id)
    return Model.parse(model)


def get_full_model_representation(representation_id: str) -> FullModelRepresentation:
    result = db.join(
        local_collection=db.Collection.MODEL_REPRESENTATION,
        local_field='modelId',
        foreign_collection=db.Collection.MODEL,
        foreign_field='_id',
        to_field='model',
        unwind=True,
        id=representation_id
    )
    if len(result) >= 1:
        return FullModelRepresentation.from_dict(result[0])


def get_full_model_representations_for_diagram(diagram_id: str | ObjectId) -> list:
    result = db.join(
        local_collection=db.Collection.MODEL_REPRESENTATION,
        local_field='modelId',
        foreign_collection=db.Collection.MODEL,
        foreign_field='_id',
        to_field='model',
        unwind=True,
        diagramId=ObjectId(diagram_id)
    )
    return FullModelRepresentation.from_dict_list(result)


def create(model: dict, representation: dict, diagram: Diagram) -> FullModelRepresentation:
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

    return get_full_model_representation(created_representation.id)
