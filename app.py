import json
from enum import Enum

import requests
from flask import Flask, request, session
from flask_socketio import SocketIO, send, emit, disconnect, join_room, rooms
import settings
from src.models.model import FullModelRepresentation
from src.services import diagram_service, model_service

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return 'Hello, world! running on %s' % request.host


@socketio.on('connect')
def on_connection(data):
    headers = {'Authorization': request.headers['Authorization']}
    response = requests.post(f'{settings.REST_DOMAIN}/users', headers=headers)
    if response.status_code == 401:
        print("Auth failed!", flush=True)
        emit(
            'connection_response',
            {
                'success': False,
                'error': response.status_code
            })  # TODO: find out if this is received
        raise ConnectionRefusedError('unauthorized!')
    else:
        session['user'] = response.json()
        send(session['user'])
        emit(
            'connection_response',
            {
                'success': True,
            })


@socketio.on('join_diagram')
def on_join_diagram(data):
    if 'diagramId' in data:
        diagram = diagram_service.get_diagram(data['diagramId'])
        if diagram is not None:
            session['diagram'] = diagram
            send(session['diagram'].as_json())

            session['room'] = diagram.id.__str__
            join_room(session['room'])
            diagram_models = model_service.get_full_model_representations_for_diagram(diagram.id)
            if diagram_models:
                emit('all_diagram_models', FullModelRepresentation.as_json_list(diagram_models))
            emit('user_joined', {'id': session['user']['_id'], 'name': session['user']['name']}, to=session['room'])

        else:
            send('diagram_not_found')


@socketio.on('create_model')
def on_create_model(model, representation):
    __ensure_client_is_in_room()

    created = model_service.create(model, representation, session['diagram'])
    if created is None:
        send('create_model_error')
        return
    emit('model_created', created.as_json(), to=session['room'])


@socketio.on('add_model')
def on_add_model(model_data, representation):
    __ensure_client_is_in_room()

    added = model_service.add_to_diagram(model_data['modelId'], representation, session['diagram'])

    if added is None:
        send('create_model_error')
        return
    emit('model_added', added.as_json(), to=session['room'])


# TODO: Make this a middleware
def __ensure_client_is_in_room() -> None:
    if 'room' not in session or session['room'] is None:
        raise ConnectionRefusedError('please join a diagram before taking this action!')


@socketio.on_error_default
def default_error_handler(e):
    send(e.__str__())
    disconnect()


# demo
@socketio.on('send_message')
def handle_source(json_data):
    text = json_data['message']
    socketio.emit('echo', {'echo': 'Server Says: ' + text})


if __name__ == '__main__':
    socketio.run(app, port=settings.APP_PORT)
