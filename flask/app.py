from flask import Flask, send_from_directory
from pos2key.subway_surfers_interface import SubwaySurfer
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__, static_folder="vue_dist", static_url_path="")
socketio = SocketIO(app)
subway_surfer = SubwaySurfer(socketio=socketio)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, "index.html")

# Example route that triggers a JS function
@app.route('/connection-test')
def connection_test():
    socketio.emit('connectionTest', {'message': 'Hello from Flask!'})
    return 'Event sent!'

# Models should directly use SubwaySurfer instead of using this route
@app.route('/trigger-keyboard/<action>')
def trigger_keyboard(action):
    if action == 'left':
        subway_surfer._left()
    elif action == 'right':
        subway_surfer._right()
    elif action == 'jump':
        subway_surfer._jump()
    elif action == 'roll':
        subway_surfer._roll()
    elif action == 'pause':
        subway_surfer.toggle_pause()
    elif action == 'start':
        subway_surfer.start_game()
    else:
        return 'Invalid action!', 400
    return f'Action {action} sent!'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
