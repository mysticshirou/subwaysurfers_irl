from flask import Flask, send_from_directory, Response
from flask_socketio import SocketIO, emit
import cv2
from pos2key.hand_tracking import HandController
from pos2key.tracking import Tracker

app = Flask(__name__, static_folder="vue_dist", static_url_path="")
socketio = SocketIO(app)
model = HandController(socketio=socketio)

# Model setup (full body tracking) -------------------------------
from pos2key.subway_surfers_interface import SubwaySurfer, Grid
subway_surfer = SubwaySurfer(socketio=socketio)
tracker = Tracker()
tracker.set_model_path("./models/yolo11n.onnx") # .onnx or .pt
def event_parser(event: dict):
    if event.get("pause", None) is None:
        subway_surfer.move_to(event)
        return 1
    elif event.get("pause", None):
        subway_surfer.toggle_pause()
        return 1
# --------------------------------------------------------------

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
# def generate_frames():
#     camera = cv2.VideoCapture(0)  # Camera source
#     while True:
#         success, frame = camera.read()
#         if not success:
#             break
#         else:
#             _, buffer = cv2.imencode('.jpg', frame)
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Hand tracking -----------------------------------------
# @app.route('/webcam-feed')
# def video_feed():
#     return Response(model.run(), mimetype='multipart/x-mixed-replace; boundary=frame')
# -------------------------------------------------------

# Full body tracking ------------------------------------
@app.route('/webcam-feed')
def video_feed():
    return Response(tracker.begin_tracking(broadcast_fn=event_parser, show_other_dets=True, use_wayland_viewer=False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
# -------------------------------------------------------

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
