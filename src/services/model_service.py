from __future__ import annotations

from datetime import datetime
from typing import Union

from bpr_data.models.diagram import Diagram
from bpr_data.models.model import Model, ModelRepresentation, FullModelRepresentation, CreateModelAction, \
    AddAttributeAction, AttributeType, RemoveAttributeAction, HistoryActionType, SetAttributeAction, \
    AttributeBase, Relation, AddRelationAction, RemoveRelationAction
from bpr_data.repository import Repository, Collection
from bson import ObjectId

import settings

db = Repository.get_instance(**settings.MONGO_CONN)

# TODO: Move to data module
MongoId = Union[ObjectId, str]


def get_model(model_id: MongoId) -> Model:
    model = db.find_one(Collection.MODEL, id=model_id)
    return Model.from_dict(model, True)


def get_full_model_representation(representation_id: MongoId) -> FullModelRepresentation:
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


def create(model: dict, representation: dict, diagram: Diagram, user_id: MongoId) -> FullModelRepresentation:
    created_model = __create_model(model, diagram.projectId, user_id)
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

    db.update(Collection.MODEL_REPRESENTATION, to_update)

    return get_full_model_representation(to_update.id)


def add_attribute(model_id: MongoId,
                  representation_id: MongoId,
                  user_id: MongoId,
                  attribute: dict) -> FullModelRepresentation:
    attr = __construct_attribute(attribute)
    added = db.push(Collection.MODEL, ObjectId(model_id), 'attributes', attr.as_dict())

    if added:
        action = AddAttributeAction(item=attr,
                                    timestamp=str(datetime.utcnow()),
                                    userId=ObjectId(user_id))
        db.push(Collection.MODEL, ObjectId(model_id), 'history', action.as_dict())
        return get_full_model_representation(representation_id)


def remove_attribute(model_id: MongoId,
                     representation_id: MongoId,
                     attribute_id: MongoId,
                     user_id: MongoId) -> FullModelRepresentation:
    removed = db.pull(Collection.MODEL, ObjectId(model_id), 'attributes', {'_id': ObjectId(attribute_id)})

    if removed:
        action = RemoveAttributeAction(timestamp=str(datetime.utcnow()),
                                       userId=ObjectId(user_id),
                                       itemId=ObjectId(attribute_id))
        __add_to_history(model_id, action)
        return get_full_model_representation(representation_id)


def set_attribute(model_id: MongoId,
                  representation_id: MongoId,
                  user_id: MongoId,
                  attribute: dict) -> FullModelRepresentation:
    if '_id' not in attribute:
        raise KeyError("missing _id field on attribute")

    model = get_model(model_id)
    new_attr = __construct_attribute(attribute)
    old_attr = next((AttributeBase.parse(a, True) for a in model.attributes if a['_id'] == new_attr.id), None)

    if old_attr is not None and old_attr != new_attr:
        action = SetAttributeAction(oldItem=old_attr,
                                    newItem=new_attr,
                                    userId=ObjectId(user_id),
                                    timestamp=str(datetime.utcnow()))
        __add_to_history(ObjectId(model_id), action)
        db.update_list_item(collection=Collection.MODEL,
                            document_id=ObjectId(model_id),
                            field_name='attributes',
                            field_query={'attributes._id': new_attr.id},
                            item=new_attr)
        return get_full_model_representation(representation_id)


def add_relation(model_id: MongoId,
                 representation_id: MongoId,
                 user_id: MongoId,
                 relation: dict) -> FullModelRepresentation:
    rel = __construct_relation(relation)
    added = db.push(Collection.MODEL, ObjectId(model_id), 'relations', rel.as_dict())

    if added:
        action = AddRelationAction(item=rel,
                                   timestamp=str(datetime.utcnow()),
                                   userId=ObjectId(user_id))
        db.push(Collection.MODEL, ObjectId(model_id), 'history', action.as_dict())
        return get_full_model_representation(representation_id)


def remove_relation(model_id: MongoId,
                    representation_id: MongoId,
                    relation_id: MongoId,
                    user_id: MongoId) -> FullModelRepresentation:
    removed = db.pull(Collection.MODEL, ObjectId(model_id), 'relations', {'_id': ObjectId(relation_id)})

    if removed:
        action = RemoveRelationAction(timestamp=str(datetime.utcnow()),
                                      userId=ObjectId(user_id),
                                      itemId=ObjectId(relation_id))
        __add_to_history(model_id, action)
        return get_full_model_representation(representation_id)


def __add_to_history(model_id: MongoId, action: HistoryActionType):
    db.push(Collection.MODEL, ObjectId(model_id), 'history', action.as_dict())


def __construct_attribute(d: dict) -> AttributeType:
    # ensure that an id is present
    # if existing _id, ensure that it is ObjectId
    if '_id' not in d:
        d['_id'] = ObjectId()
    else:
        d['_id'] = ObjectId(d['_id'])

    return AttributeBase.parse(d, True)


def __construct_relation(d: dict) -> AttributeType:
    # ensure that an id is present
    # if existing _id, ensure that it is ObjectId
    if '_id' not in d:
        d['_id'] = ObjectId()
    else:
        d['_id'] = ObjectId(d['_id'])

    return Relation.from_dict(d, True)


def __create_model(model: dict, project_id: MongoId, user_id: MongoId) -> Model:
    model['_id'] = None
    model['projectId'] = ObjectId(project_id)

    if 'attributes' in model:
        attributes = [__construct_attribute(a) for a in model['attributes']]
        model['attributes'] = attributes
    else:
        model['attributes'] = []

    if 'relations' in model:
        relations = [__construct_relation(r) for r in model['relations']]
        model['relations'] = relations
    else:
        model['relations'] = []

    action = CreateModelAction(timestamp=str(datetime.utcnow()), userId=ObjectId(user_id))
    model['history'] = [action]
    return db.insert(Collection.MODEL, Model.from_dict(model), return_type=Model)


def __create_representation(representation: dict, model_id: str | ObjectId, diagram_id: str | ObjectId):
    representation['_id'] = None
    representation['modelId'] = ObjectId(model_id)
    representation['diagramId'] = ObjectId(diagram_id)
    return ModelRepresentation.from_dict(
        db.insert(Collection.MODEL_REPRESENTATION, ModelRepresentation.from_dict(representation)))
