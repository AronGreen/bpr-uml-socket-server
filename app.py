import json

from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send, rooms, emit
# from flask_cors import CORS, cross_origin
from src import settings
from src.services import model_service, diagram_service

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return 'Hello, world! running on %s' % request.host 


@socketio.on('connection')
def on_connection(token):
    # TODO: verify token with rest server
    emit('connection_response', {'data': 'Connected'})


@socketio.on('join_diagram')
def on_join_diagram(data):
    """
    username
    diagramId
    """
    print(data, flush=True)
    json_data = json.loads(data)
    username = json_data['username']
    diagram_id = json_data['diagramId']
    # TODO: when diagrams are ready, find real project and diagram id
    project_id = diagram_id  # diagram_service.find_one(diagram_id).projectId
    room = f'{diagram_id}-{project_id}'
    join_room(room)
    send(username + ' has entered the room.', to=room)
    # return list of other active users


@socketio.on('leave_diagram')
def on_leave_diagram(data):
    """
    username
    diagramId
    """
    username = data['username']
    diagram_id = data['projectId']
    # TODO: when diagrams are ready, find real project and diagram id
    project_id = diagram_id  # diagram_service.find_one(diagram_id).projectId
    room = f'{diagram_id}-{project_id}'
    leave_room(room)
    send(username + ' has left the room.', to=room)


@socketio.on('create_model')
def on_create_model(data):
    rs = rooms()
    if rs is None:
        emit('create_model_error', 'client is not in room')
        return
    created = model_service.create(data)
    if created is None:
        emit('create_model_error', 'could not create model')
        return
    emit('model_created', created.as_json())


@socketio.on('add_model')
def on_add_model(diagramId, modelId):
    pass


#demo
@socketio.on('send_message')
def handle_source(json_data):
    text = json_data['message']
    socketio.emit('echo', {'echo': 'Server Says: '+text})


if __name__ == '__main__':
    socketio.run(app, port=settings.APP_PORT)
