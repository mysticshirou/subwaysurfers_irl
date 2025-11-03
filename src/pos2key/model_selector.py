from pos2key.subway_surfers_interface import SubwaySurfer, Grid
from pos2key.hand_tracking import HandController
from pos2key.tracking import Tracker

class GeneralTracker():
    def __init__(self, socketio, tracker: str="tracking", **kwargs):
        """
        tracker: Choose the tracker of choice, default is tracking
            1. "tracking" (full body tracking)
            2. "hand-tracking" (hand tracking)
        """
        self._selection = tracker.lower()
        assert self._selection in ["tracking", "hand-tracking"]
        match self._selection:
            case "tracking":
                self._subway_surfer = SubwaySurfer(socketio=socketio)
                self.tracker = Tracker(**kwargs)
            case "hand-tracking":
                self.tracker = HandController(socketio=socketio, **kwargs)

    # Event parsing / broadcasting function for full body tracking
    def _event_parser(self, event: dict):
        if event.get("pause", None) is None:
            self._subway_surfer.move_to(event)
            return 1
        elif event.get("pause", None):
            self._subway_surfer.toggle_pause()
            return 1
        
    def run(self, **kwargs):
        """
        Returns a generator of the selected tracker, with additional kwargs if needed
        """
        match self._selection:
            case "tracking": 
                return self.tracker.begin_tracking(broadcast_fn=self._event_parser, **kwargs)
            case "hand-tracking":
                return self.tracker.run(**kwargs)