from flask import Flask, request
from flask_socketio import SocketIO
# from flask_cors import CORS, cross_origin

app = Flask(__name__)
# CORS(app)
# cors = CORS(app=app, origins='*', send_wildcard=True)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return 'Hello, world! running on %s' % request.host 


@socketio.on('send_message')
def handle_source(json_data):
    text = json_data['message']
    socketio.emit('echo', {'echo': 'Server Says: '+text})


if __name__ == '__main__':
    socketio.run(app)
