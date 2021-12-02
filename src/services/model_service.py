from __future__ import annotations

from datetime import datetime
from typing import Union, List

from bpr_data.models.diagram import Diagram
from bpr_data.models.model import Model, ModelRepresentation, FullModelRepresentation, CreateModelAction, \
    AddAttributeAction, AttributeType, RemoveAttributeAction, HistoryActionType, UpdateAttributeAction, \
    AttributeBase, Relation, CreateRelationAction, RemoveRelationAction, RelationRepresentation, UpdateRelationAction
from bpr_data.repository import Repository, Collection
from bson import ObjectId

import settings
from src.util.exceptions import ListItemNotFoundException, MissingPropertyException

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
    return FullModelRepresentation.from_dict_list(result, True)


def create(model: dict, representation: dict, diagram: Diagram, user_id: MongoId) -> FullModelRepresentation:
    created_model = __create_model(model, diagram.projectId, user_id)
    created_representation = __create_representation(representation, created_model.id, diagram.id)
    db.push(Collection.DIAGRAM, diagram.id, 'models', item=created_representation.id)
    return get_full_model_representation(created_representation.id)


def delete_model(model_id: MongoId) -> bool:
    __on_model_delete_cleanup(model_id)
    return db.delete(Collection.MODEL, id=model_id)


def delete_model_rep(representation_id: MongoId):
    __on_model_rep_delete_cleanup([ObjectId(representation_id)])
    return db.delete(Collection.MODEL_REPRESENTATION, id=representation_id)


def __on_model_delete_cleanup(model_id: MongoId) -> None:
    # delete cascade is partially handled in triggers, but we are at the limit for free tier, so here we go:
    # delete diagram.models affected
    rep_ids = [r.id for r in db.find(Collection.MODEL_REPRESENTATION, ModelRepresentation, modelId=ObjectId(model_id))]
    __on_model_rep_delete_cleanup(rep_ids)
    # diagrams = db.find(Collection.DIAGRAM, Diagram, models={'$in': representation_ids})
    # for diagram in diagrams:
    #     for rep in representation_ids:
    #         db.pull(Collection.DIAGRAM, diagram.id, 'models', rep)


def __on_model_rep_delete_cleanup(rep_ids: List[ObjectId]) -> None:
    # delete cascade is partially handled in triggers, but we are at the limit for free tier, so here we go:
    # delete diagram.models affected
    diagrams = db.find(Collection.DIAGRAM, Diagram, models={'$in': rep_ids})
    for diagram in diagrams:
        for rep in rep_ids:
            db.pull(Collection.DIAGRAM, diagram.id, 'models', rep)


def add_to_diagram(model_id: str | ObjectId, representation: dict, diagram: Diagram) -> FullModelRepresentation:
    model = get_model(model_id)
    created_representation = __create_representation(representation, model.id, diagram.id)
    return get_full_model_representation(created_representation.id)


def update_model_rep(data: dict) -> FullModelRepresentation:
    if 'modelId' not in data or 'diagramId' not in data:
        ref_model = db.find_one(Collection.MODEL_REPRESENTATION, id=data['_id'])
        data['modelId'] = ref_model['modelId']
        data['diagramId'] = ref_model['diagramId']
        data['relations'] = ref_model['relations']

    to_update = ModelRepresentation.from_dict(data)

    db.update(Collection.MODEL_REPRESENTATION, to_update)

    return get_full_model_representation(to_update.id)


def add_attribute(model_id: MongoId,
                  user_id: MongoId,
                  attribute: dict) -> Model:
    attr = __construct_attribute(attribute)
    success = db.push(Collection.MODEL, ObjectId(model_id), 'attributes', attr.as_dict())

    if success:
        __add_to_history(model_id,
                         AddAttributeAction(item=attr, timestamp=str(datetime.utcnow()), userId=ObjectId(user_id)))

        return get_model(model_id)


def remove_attribute(model_id: MongoId,
                     attribute_id: MongoId,
                     user_id: MongoId) -> Model:
    success = db.pull(Collection.MODEL, ObjectId(model_id), 'attributes', {'_id': ObjectId(attribute_id)})

    if success:
        __add_to_history(model_id, RemoveAttributeAction(timestamp=str(datetime.utcnow()), userId=ObjectId(user_id),
                                                         itemId=ObjectId(attribute_id)))
        return get_model(model_id)


def update_attribute(model_id: MongoId,
                     user_id: MongoId,
                     attribute: dict) -> Model:
    if '_id' not in attribute:
        raise MissingPropertyException(prop='_id')

    model = get_model(model_id)
    new_attr = __construct_attribute(attribute)
    old_attr = next((AttributeBase.parse(a, True) for a in model.attributes if a['_id'] == new_attr.id), None)

    if old_attr is not None and old_attr != new_attr:
        __add_to_history(ObjectId(model_id),
                         UpdateAttributeAction(oldItem=old_attr, newItem=new_attr, userId=ObjectId(user_id),
                                               timestamp=str(datetime.utcnow())))

        db.update_list_item(collection=Collection.MODEL,
                            document_id=ObjectId(model_id),
                            field_name='attributes',
                            field_query={'attributes._id': new_attr.id},
                            item=new_attr)

        return get_model(model_id)


def create_relation(model_id: MongoId,
                    representation_id: MongoId,
                    user_id: MongoId,
                    relation_target: MongoId) -> FullModelRepresentation:
    relation = __create_relation({'target': ObjectId(relation_target)}, model_id)

    if relation is not None:
        relation_rep = RelationRepresentation.from_dict({'_id': ObjectId(), 'relationId': relation.id})
        db.push(Collection.MODEL_REPRESENTATION, ObjectId(representation_id), 'relations', relation_rep.as_dict())

        __add_to_history(model_id, CreateRelationAction(item=relation, timestamp=str(datetime.utcnow()),
                                                        userId=ObjectId(user_id)))

        return get_full_model_representation(representation_id)


def update_relation(model_id: MongoId,
                    user_id: MongoId,
                    relation: dict) -> Model:
    if '_id' not in relation:
        raise MissingPropertyException(prop='_id')

    model = get_model(model_id)

    old_rel = next((r for r in model.relations if str(r['_id']) == str(relation['_id'])), None)
    if old_rel is None:
        raise ListItemNotFoundException(document_id=model.id, list_field='relation',
                                        item_identifier=f'_id={relation["_id"]}')

    updated_rel = __construct_relation(relation)
    db.update_list_item(collection=Collection.MODEL,
                        document_id=ObjectId(model_id),
                        field_name='relations',
                        field_query={'relations._id': updated_rel.id},
                        item=updated_rel)

    __add_to_history(model_id,
                     UpdateRelationAction(timestamp=str(datetime.utcnow()), userId=ObjectId(user_id), oldItem=old_rel,
                                          newItem=updated_rel))

    return get_model(model_id)


def delete_relation(model_id: MongoId,
                    representation_id: MongoId,
                    relation_id: MongoId,
                    deep: bool,
                    user_id: MongoId):
    db.pull(Collection.MODEL_REPRESENTATION,
            ObjectId(representation_id),
            'relations',
            {'relationId': ObjectId(relation_id)})

    if deep:
        db.pull(Collection.MODEL, ObjectId(model_id), 'relations', {'_id': ObjectId(relation_id)})
        __add_to_history(model_id, RemoveRelationAction(timestamp=str(datetime.utcnow()), userId=ObjectId(user_id),
                                                        itemId=ObjectId(relation_id)))

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


def __construct_relation(d: dict) -> Relation:
    # ensure that an id is present
    # if existing _id, ensure that it is ObjectId
    if '_id' not in d:
        d['_id'] = ObjectId()
    else:
        d['_id'] = ObjectId(d['_id'])

    return Relation.from_dict(d, True)


def __create_relation(d: dict, model_id: MongoId) -> Relation:
    relation = __construct_relation(d)
    success = db.push(Collection.MODEL, ObjectId(model_id), 'relations', relation.as_dict())
    if success:
        return relation


def __construct_relation_representation(d: dict) -> Relation:
    # ensure that an id is present
    # if existing _id, ensure that it is ObjectId
    if '_id' not in d:
        d['_id'] = ObjectId()
    else:
        d['_id'] = ObjectId(d['_id'])

    return RelationRepresentation.from_dict(d, True)


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
    if 'relations' in representation:
        relations = [__construct_relation_representation(r) for r in representation['relations']]
        representation['relations'] = relations
    else:
        representation['relations'] = []
    return ModelRepresentation.from_dict(
        db.insert(Collection.MODEL_REPRESENTATION, ModelRepresentation.from_dict(representation)))


def __get_raw_model_representation(model_representation_id: MongoId) -> ModelRepresentation:
    model = db.find_one(Collection.MODEL_REPRESENTATION, id=model_representation_id)
    return ModelRepresentation.from_dict(model, True)
