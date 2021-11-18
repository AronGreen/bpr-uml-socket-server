from __future__ import annotations

from bson import ObjectId

from bpr_data.repository import Repository, Collection
from bpr_data.models.diagram import Diagram
from bpr_data.models.model import Model, ModelRepresentation, FullModelRepresentation

import settings

db = Repository.get_instance(
    protocol=settings.MONGO_PROTOCOL,
    default_db=settings.MONGO_DEFAULT_DB,
    pw=settings.MONGO_PW,
    host=settings.MONGO_HOST,
    user=settings.MONGO_USER)


def get_model(model_id: str) -> Model:
    model = db.find_one(Collection.MODEL, id=model_id)
    return Model.parse(model)


def get_full_model_representation(representation_id: str) -> FullModelRepresentation:
    result = db.join(
        local_collection=Collection.MODEL_REPRESENTATION,
        local_field='modelId',
        foreign_collection=Collection.MODEL,
        foreign_field='_id',
        to_field='model',
        unwind=True,
        id=representation_id
    )
    if len(result) >= 1:
        return FullModelRepresentation.from_dict(result[0])


def get_full_model_representations_for_diagram(diagram_id: str | ObjectId) -> list:
    result = db.join(
        local_collection=Collection.MODEL_REPRESENTATION,
        local_field='modelId',
        foreign_collection=Collection.MODEL,
        foreign_field='_id',
        to_field='model',
        unwind=True,
        diagramId=ObjectId(diagram_id)
    )
    return FullModelRepresentation.from_dict_list(result)


def create(model: dict, representation: dict, diagram: Diagram) -> FullModelRepresentation:
    created_model = __create_model(model, diagram.projectId)
    created_representation = __create_representation(representation, created_model.id, diagram.id)

    db.push(Collection.DIAGRAM, diagram.id, 'models', item=created_representation.id)

    return get_full_model_representation(created_representation.id)


def add_to_diagram(model_id: str | ObjectId, representation: dict, diagram: Diagram) -> FullModelRepresentation:
    model = get_model(model_id)
    created_representation = __create_representation(representation, model.id, diagram.id)
    return get_full_model_representation(created_representation.id)


def update_model_representation(data: dict) -> FullModelRepresentation:
    if 'modelId' not in data or 'diagramId' not in data:
        ref_model = db.find_one(Collection.MODEL_REPRESENTATION, id=data['_id'])
        data['modelId'] = ref_model['modelId']
        data['diagramId'] = ref_model['diagramId']

    to_update = ModelRepresentation.from_dict(data)

    # may return None if the update makes no changes
    db.update(Collection.MODEL_REPRESENTATION, to_update)

    return get_full_model_representation(to_update.id)


def __create_model(model: dict, project_id: str | ObjectId):
    model['_id'] = None
    model['projectId'] = ObjectId(project_id)
    return Model.parse(db.insert(Collection.MODEL, Model.parse(model)))


def __create_representation(representation: dict, model_id: str | ObjectId, diagram_id: str | ObjectId):
    representation['_id'] = None
    representation['modelId'] = ObjectId(model_id)
    representation['diagramId'] = ObjectId(diagram_id)
    return ModelRepresentation.from_dict(
        db.insert(Collection.MODEL_REPRESENTATION, ModelRepresentation.from_dict(representation)))
