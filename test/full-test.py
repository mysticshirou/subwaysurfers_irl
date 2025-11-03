"""
Input 1 to start live tracking after all models are loaded to start the tracking
Tracking auto reselects using the depth scan when the target is lost.
"""
from pos2key.tracking import Tracker
from pos2key.subway_surfers_interface import SubwaySurfer
from time import perf_counter

tracker = Tracker()
tracker.set_model_path("./models/yolo11n.pt")

subway_surfer = SubwaySurfer()

def event_parser(event: dict):
    start_time = perf_counter()
    if event["pause"] is None:
        subway_surfer.move_to(event)
        print(f"Event elapsed time: {start_time - perf_counter()}")
        return 1
    
    if event.get("pause", None):
        subway_surfer.toggle_pause()
        print(f"Event elapsed time: {start_time - perf_counter()}")
        return 1
    
        

while True:
    choice = input(">>>")
    if choice == "1":
        tracker.begin_tracking(broadcast_fn=event_parser, show_other_dets=True, use_wayland_viewer=False)
    else:
        exit()