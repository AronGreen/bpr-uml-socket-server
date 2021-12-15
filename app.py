from flask import Flask
from flask_socketio import SocketIO, emit, disconnect

import settings
from src.namespaces.main import MainNamespace

app = Flask(__name__)

socket_io = SocketIO(app, cors_allowed_origins="*")

socket_io.on_namespace(MainNamespace(''))


@app.route('/')
def index():
    return 'Server is running!'


@socket_io.on_error_default
def default_error_handler(e):
    if isinstance(e, ConnectionRefusedError):
        # for some reason, events emitted right before disconnect() are not received, so commenting this for now
        # emit('error', {'error_type': 'connection', 'error': e.__str__()})
        disconnect()
    else:
        emit('error', {'error_type': 'general', 'error': e.__repr__()})


# demo
@socket_io.on('send_message')
def handle_source(json_data):
    text = json_data['message']
    socket_io.emit('echo', {'echo': 'Server Says: ' + text})


if __name__ == '__main__':
    socket_io.run(app, port=settings.APP_PORT)
