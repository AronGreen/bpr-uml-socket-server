import requests
from flask import request, session
from flask_socketio import send, emit, join_room, Namespace, leave_room
import settings
from bpr_data.models.model import FullModelRepresentation
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
            emit(
                'connection_response',
                {
                    'success': True,
                })

    def on_join_diagram(self, data):
        if 'diagramId' in data:
            diagram = diagram_service.get_diagram(data['diagramId'])

            if diagram is not None:
                session['diagram'] = diagram
                session['room'] = diagram.id.__str__

                join_room(session['room'])

                diagram_models = model_service.get_full_model_representations_for_diagram(diagram.id)

                emit('all_diagram_models',
                     FullModelRepresentation.as_dict_list(diagram_models))

                emit('user_joined',
                     {'id': session['user']['_id'], 'name': session['user']['name']},
                     to=session['room'])
            else:
                send('diagram_not_found')

    def on_leave_diagram(self):
        session['diagram'] = None
        emit('user_left',
             {'id': session['user']['_id'], 'name': session['user']['name']},
             to=session['room'])
        leave_room(session['room'])
        session['room'] = ''

    def on_create_model(self, model, representation):
        self.__ensure_client_is_in_room()

        created = model_service.create(model, representation, session['diagram'])
        if created is None:
            send('create_model_error')
            return
        emit('model_created', created.as_dict(), to=session['room'])

    def on_add_model(self, model_data, representation):
        self.__ensure_client_is_in_room()

        added = model_service.add_to_diagram(model_data['modelId'], representation, session['diagram'])

        if added is None:
            send('create_model_error')
            return
        emit('model_added', added.as_dict(), to=session['room'])

    def on_update_model_representation(self, data):
        self.__ensure_client_is_in_room()

        updated = model_service.update_model_representation(data)

        if updated is None:
            send('update_model_error')
            return
        emit('model_updated', updated.as_dict(), to=session['room'])

    def on_add_model_attribute(self, references, attribute):
        self.__ensure_client_is_in_room()

        updated = model_service.add_attribute(
            model_id=references['modelId'],
            representation_id=references['modelRepresentationId'],
            user_id=session['user']['_id'],
            attribute=attribute)

        if updated is None:
            send('update_model_error')
            return
        emit('model_updated', updated.as_dict(), to=session['room'])

    def on_remove_model_attribute(self, references):
        self.__ensure_client_is_in_room()

        updated = model_service.remove_attribute(
            model_id=references['modelId'],
            representation_id=references['modelRepresentationId'],
            attribute_id=references['attributeId'],
            user_id=session['user']['_id']
        )

        if updated is None:
            send('update_model_error')
            return
        emit('model_updated', updated.as_dict(), to=session['room'])

    @staticmethod
    def __ensure_client_is_in_room() -> None:
        if 'room' not in session or session['room'] is None:
            raise ConnectionRefusedError('please join a diagram before taking this action!')
