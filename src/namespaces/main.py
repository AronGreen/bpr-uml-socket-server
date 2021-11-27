import json
from typing import Callable, TypeVar, Any

import requests
from bpr_data.models.model import FullModelRepresentation
from bpr_data.models.mongo_document_base import SerializableObject
from flask import request, session
from flask_socketio import emit, join_room, Namespace, leave_room

import settings
from src.services import diagram_service, model_service


# noinspection PyMethodMayBeStatic
class MainNamespace(Namespace):

    def on_connect(self):
        headers = {'Authorization': request.headers['Authorization']}
        response = requests.post(f'{settings.REST_DOMAIN}/users', headers=headers)
        if response.status_code == 401:
            print("Auth failed!", flush=True)
            raise ConnectionRefusedError('unauthorized!')
        else:
            session['user'] = response.json()
            session['user']['id'] = str(session['user']['_id'])
            emit(
                'connection_response',
                json.dumps({
                    'success': True,
                }, default=str))

    def on_disconnect(self):
        emit('user_left',
             json.dumps({'id': session['user']['id'], 'name': session['user']['name']}, default=str),
             to=session['room'])

    def on_join_diagram(self, data):
        if 'diagramId' in data:
            diagram = diagram_service.get_diagram(data['diagramId'])

            if diagram is not None:
                session['diagram'] = diagram
                session['room'] = str(diagram.id)

                join_room(session['room'])

                diagram_models = model_service.get_full_model_representations_for_diagram(diagram.id)

                emit('all_diagram_models',
                     FullModelRepresentation.as_json_list(diagram_models))

                emit('user_joined',
                     json.dumps({'id': session['user']['id'], 'name': session['user']['name']}, default=str),
                     to=session['room'])
            else:
                emit('error', {'error_type': 'diagram_not_found'})

    def on_leave_diagram(self):
        session['diagram'] = None
        emit('user_left',
             json.dumps({'id': session['user']['id'], 'name': session['user']['name']}, default=str),
             to=session['room'])
        leave_room(session['room'])
        session['room'] = ''

    def on_create_model(self, model, representation):
        self.__ensure_client_is_in_room()
        if self.__validate(model, ['type', 'path']) and self.__validate(representation, ['x', 'y', 'w', 'h']):
            self.__handle_model_add(model_service.create,
                                    model=model,
                                    representation=representation,
                                    diagram=session['diagram'],
                                    user_id=session['user']['_id'])

    def on_add_model(self, model_data, representation):
        self.__ensure_client_is_in_room()
        if self.__validate(model_data, ['modelId']) and self.__validate(representation, ['x', 'y', 'w', 'h']):
            self.__handle_model_add(model_service.add_to_diagram,
                                    model_id=model_data['modelId'],
                                    representation=representation,
                                    diagram=session['diagram'])

    def on_update_model_representation(self, data):
        self.__ensure_client_is_in_room()
        if self.__validate(data, ['_id', 'x', 'y', 'w', 'h']):
            self.__handle_model_update(model_service.update_model_representation, data)

    def on_add_model_attribute(self, references, attribute):
        self.__ensure_client_is_in_room()
        if self.__validate(references, ['modelId', 'modelRepresentationId']) \
                and self.__validate_attribute(attribute):
            self.__handle_model_update(model_service.add_attribute,
                                       model_id=references['modelId'],
                                       representation_id=references['modelRepresentationId'],
                                       user_id=session['user']['_id'],
                                       attribute=attribute)

    def on_remove_model_attribute(self, references):
        self.__ensure_client_is_in_room()
        if self.__validate(references, ['modelId', 'modelRepresentationId', 'attributeId']):
            self.__handle_model_update(model_service.remove_attribute,
                                       model_id=references['modelId'],
                                       representation_id=references['modelRepresentationId'],
                                       attribute_id=references['attributeId'],
                                       user_id=session['user']['_id'])

    def on_update_model_attribute(self, references, attribute):
        self.__ensure_client_is_in_room()
        if self.__validate(references, ['modelId', 'modelRepresentationId']) \
                and self.__validate_attribute(attribute):
            self.__handle_model_update(model_service.update_attribute,
                                       model_id=references['modelId'],
                                       representation_id=references['modelRepresentationId'],
                                       user_id=session['user']['_id'],
                                       attribute=attribute)

    def on_create_model_relation(self, references, relation):
        self.__ensure_client_is_in_room()
        if self.__validate(references, ['modelId', 'modelRepresentationId']) \
                and self.__validate(relation, ['target']):
            self.__handle_model_update(model_service.create_relation,
                                       model_id=references['modelId'],
                                       representation_id=references['modelRepresentationId'],
                                       user_id=session['user']['_id'],
                                       relation_target=relation['target'])

    def on_update_model_relation(self, references, relation):
        self.__ensure_client_is_in_room()
        if self.__validate(references, ['modelId', 'modelRepresentationId']) \
                and self.__validate(relation, ['_id', 'target']):
            self.__handle_model_update(model_service.update_relation,
                                       model_id=references['modelId'],
                                       representation_id=references['modelRepresentationId'],
                                       user_id=session['user']['_id'],
                                       relation=relation)

    def on_remove_model_relation(self, data):
        self.__ensure_client_is_in_room()
        if self.__validate(data, ['modelId', 'modelRepresentationId', 'relationId', 'deep']):
            self.__handle_model_update(model_service.delete_relation,
                                       model_id=data['modelId'],
                                       representation_id=data['modelRepresentationId'],
                                       relation_id=data['relationId'],
                                       deep=data['deep'],
                                       user_id=session['user']['_id'])

    # TODO: Move to mongo_document_base in data module
    SOType = TypeVar('SOType', bound=SerializableObject)

    def __handle_model_add(self, func: Callable[[Any], SOType], *args, **kwargs):
        self.__handle_model_change(func, 'model_added', 'model_error', *args, **kwargs)

    def __handle_model_update(self, func: Callable[[Any], SOType], *args, **kwargs):
        self.__handle_model_change(func, 'model_updated', 'update_model_error', *args, **kwargs)

    @staticmethod
    def __handle_model_change(func: Callable[[Any], SOType], success_event: str, error_event: str, *args, **kwargs):
        """
        func return value must inherit from SerializableObject
        """
        result = func(*args, **kwargs)
        if result is None:
            emit('error', {'error_type': error_event})
            return
        emit(success_event, result.as_json(), to=session['room'])

    @staticmethod
    def __ensure_client_is_in_room() -> None:
        if 'room' not in session or session['room'] is None:
            raise ConnectionRefusedError('please join a diagram before taking this action!')

    def __validate_attribute(self, to_check: dict) -> bool:
        if 'kind' not in to_check:
            emit('error', {'error_type': 'missingParameters', 'message': 'attribute must have `kind` field'})
            return False
        if to_check['kind'] == 'field':
            return self.__validate(to_check, ['kind', 'name', 'type', 'accessModifier'])
        if to_check['kind'] == 'method':
            return self.__validate(to_check, ['kind', 'name', 'type', 'accessModifier', 'parameters'])
        return self.__validate(to_check, ['kind', 'value'])

    @staticmethod
    def __validate(to_check: dict, required_keys: list) -> bool:
        if all(key in to_check for key in required_keys):
            return True
        emit('error',
             {'error_type': 'missingParameters', 'message': [i for i in required_keys if i not in list(to_check)]})
        return False
