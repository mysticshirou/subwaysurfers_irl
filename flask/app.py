from flask import Flask, send_from_directory, Response
from flask_socketio import SocketIO, emit
import cv2
from pos2key.model_selector import GeneralTracker

app = Flask(__name__, static_folder="vue_dist", static_url_path="")
socketio = SocketIO(app)

# Initialising tracker model, ("tracking", "hand-tracking")
model = GeneralTracker(socketio=socketio, tracker="tracking")

# DELETE THIS
model.set

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
        model._left()
    elif action == 'right':
        model._right()
    elif action == 'jump':
        model._jump()
    elif action == 'roll':
        model._roll()
    elif action == 'pause':
        model.toggle_pause()
    elif action == 'start':
        model.start_game()
    else:
        return 'Invalid action!', 400
    return f'Action {action} sent!'

# Generating mjpeg frames from webcam
def generate_frames():
    camera = cv2.VideoCapture(0)  # Camera source
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/webcam-feed')
def video_feed():
    return Response(model.run(show_other_dets=True, use_wayland_viewer=False, fixed_center=True), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
