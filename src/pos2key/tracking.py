import os
import cv2
import time
import typing
import numpy as np
from PIL import Image
from pathlib import Path
from ultralytics import YOLO
from transformers import pipeline
import os
import shlex
import subprocess

from pos2key.config import Config
cfg = Config()

def draw_gridlines(image, h_thresh: list[int]|tuple[int], v_thresh: list[int]|tuple[int], colour=(0,0,255)):
    """Draws gridlines on image"""
    image = cv2.line(image, (h_thresh[0], 0), (h_thresh[0], image.shape[0]), colour, 2)
    image = cv2.line(image, (h_thresh[1], 0), (h_thresh[1], image.shape[0]), colour, 2)
    image = cv2.line(image, (0, v_thresh[0]), (image.shape[1], v_thresh[0]), colour, 2)
    image = cv2.line(image, (0, v_thresh[1]), (image.shape[1], v_thresh[1]), colour, 2)
    return image

class FrameViewer:
        def __init__(self, prefer_ffplay: bool = False):
            # Default to cv2. Enable ffplay if explicitly requested via prefer_ffplay
            # or via the USE_WAYLAND_VIEWER env var. This keeps default behaviour unchanged.
            self.backend = "cv2"
            if prefer_ffplay or os.environ.get("USE_WAYLAND_VIEWER"):
                self.backend = "ffplay"
            self.process = None
            self.width = None
            self.height = None
            self.fps = 30
            self.window_name = "Camera"

        def open(self, width: int, height: int, fps: int = 30, window_name: str = "Camera"):
            self.width = width
            self.height = height
            self.fps = fps
            self.window_name = window_name
            if self.backend != "ffplay":
                return

            cmd = (
                f"ffplay -f rawvideo -pixel_format bgr24 -video_size {width}x{height}"
                f" -framerate {fps} -window_title {shlex.quote(window_name)} -i - -hide_banner -loglevel error"
            )
            try:
                # Start ffplay
                self.process = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print("ffplay not found; falling back to cv2.imshow")
                self.backend = "cv2"

        def show(self, frame, window_name: str = "Camera"):
            if self.backend == "cv2":
                cv2.imshow(window_name, frame)
                return

            # backend is ffplay
            if self.process is None or self.process.poll() is not None:
                # (re)open
                self.open(frame.shape[1], frame.shape[0], self.fps, window_name)
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                try:
                    if self.process:
                        self.process.kill()
                except Exception:
                    pass
                self.open(frame.shape[1], frame.shape[0], self.fps, window_name)

            try:
                if self.process and self.process.stdin:
                    self.process.stdin.write(frame.tobytes())
                    self.process.stdin.flush()
                else:
                    # fallback
                    cv2.imshow(window_name, frame)
            except Exception:
                cv2.imshow(window_name, frame)

        def close(self):
            if self.backend == "cv2":
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
                return

            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except Exception:
                    pass
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass

class Tracker:
    def __init__(self):
        self.tracking_model = YOLO(cfg.get("tracking").get("model_path", "models/yolo11n.pt"))
        self.depth_model = pipeline(task="depth-estimation", model=cfg.get("tracking").get("depth_model", "depth-anything/Depth-Anything-V2-Small-hf"))

        self.GRID_OFFSETX = cfg.get("tracking").get("grid_offsetx", (50, -50))
        self.GRID_OFFSETY = cfg.get("tracking").get("grid_offsety", (50, -50))

        self.BBOX_COLOUR = cfg.get("tracking").get("bbox_colour", (0,255,0))
        self.GRID_COLOUR = cfg.get("tracking").get("grid_colour", (0,0,255))

        self.CAMERA = cfg.get("config").get("camera_id", 0)   # Camera index to use, default is 0
        self.PERSON = cfg.get("tracking").get("person_cls", 0)  # Class # for person class, default is 0

        self.output_dir = cfg.get("tracking").get("output_dir", os.path.join(os.getcwd(), "outputs"))

        self.centroid_prediction_rate = 1
        self.previous_centre = None

    def set_model_path(self, model_path: Path):
        """
        Changes yolo_model_path and reloads the tracking model used (This does not affect the config)

        model_path: path to YOLO model
        """
        self.tracking_model = YOLO(model_path)
        return 1
    
    def set_grid_offset(self, offsetx: tuple[int|float] = (100, 100), offsety: tuple[int|float] = (50, 50)):
        """
        Set the grid offsets by any numerical value
        """
        self.GRID_OFFSETX = (offsetx[0], offsetx[1] if offsetx[1] <= 0 else -offsetx[1])
        self.GRID_OFFSETY = (offsety[0], offsety[1] if offsety[1] <= 0 else -offsety[1])

        cfg.set("tracking").get("grid_offsetx", self.GRID_OFFSETX)
        cfg.set("tracking").get("grid_offsety", self.GRID_OFFSETY)

        return 1
        
    def depth_scan(self, frame: np.array):
        """
        Uses the Depth-Anything-V2-Small model to determine closest objects to camera

        Inputs:
            frame: Current frame of the cv2.VideoCapture

        Outputs:
            masked_frame: Final segmented image of closest objects to the camera, created using binary_image mask & initial frame
            clustered_frame: Depth scan image segmented using k-means clustering, for debugging
            binary_image: Thresholded clustered_frame to create binary image mask, for debugging
        """
        # Convert the cv2 image into PIL for depth scan
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        depth = self.depth_model(frame_pil)["depth"]
        cvdepth = cv2.cvtColor(np.array(depth), cv2.COLOR_RGB2BGR)

        # K means clustering to create segmentation mask
        pixel_values = cvdepth.reshape((-1, 3))
        pixel_values = np.float32(pixel_values)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, (centers) = cv2.kmeans(pixel_values, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        centers = np.uint8(centers)
        clustered_frame = centers[labels.flatten()]
        clustered_frame = clustered_frame.reshape(cvdepth.shape)
        _, binary_image = cv2.threshold(cv2.cvtColor(clustered_frame, cv2.COLOR_BGR2GRAY), np.max(clustered_frame)-1, 255, cv2.THRESH_BINARY)

        masked_frame = cv2.bitwise_and(frame, frame, mask=binary_image)
        # masked_frame = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2RGB)
        return masked_frame, clustered_frame, binary_image

    def check_position(self, broadcast_fn: typing.Callable, position: tuple[int], h_thresh: list[int]|tuple[int], v_thresh: list[int]|tuple[int]):
        if self.previous_centre is None:
            self.previous_centre = position
            return
        
        dx = (position[0] - self.previous_centre[0]) * 2
        delta_y = position[1] - self.previous_centre[1]

        if delta_y < 0:
            dy = delta_y * 12
        else:
            dy = delta_y * 3

        centroid_prediction_rate = self.centroid_prediction_rate

        predicted_x = position[0] + (dx*centroid_prediction_rate)
        predicted_y = position[1] + (dy*centroid_prediction_rate)

        x, y = 0, 0
        if predicted_x > h_thresh[0]: x = 1
        elif predicted_x < h_thresh[1]: x = -1
        else: x = 0

        if predicted_y > v_thresh[0]: y = -1
        elif predicted_y < v_thresh[1]: y = 1
        else: y = 0

        self.previous_centre = position

        print({"x": x, "y": y})
        broadcast_fn({"x": x, "y": y})

        return (predicted_x, predicted_y)

    def game_pause_event(self, broadcast_fn: typing.Callable, pause: bool):
        broadcast_fn({"pause": pause})

    def begin_tracking(
        self,
        broadcast_fn: typing.Callable,
        save: bool = False,
        show_other_dets: bool = False,
        fps: int = 30,
        verbose: bool = False,
        use_wayland_viewer: bool = False,
        fixed_center: bool = True,
    ):
        """
        Starts real time tracking
        """
        print("Started")

        cap = cv2.VideoCapture(self.CAMERA, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # ---- Initial frame grab (required for writer / viewer init)
        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to read initial frame from camera")

        video_writer = cv2.VideoWriter(
            os.path.join(self.output_dir, "tracking_output.mp4"),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (frame.shape[1], frame.shape[0]),
        )

        viewer = None
        if use_wayland_viewer or os.environ.get("USE_WAYLAND_VIEWER"):
            try:
                viewer = FrameViewer(
                    prefer_ffplay=use_wayland_viewer
                    or bool(os.environ.get("USE_WAYLAND_VIEWER"))
                )
                viewer.open(frame.shape[1], frame.shape[0], fps=fps, window_name="Camera")
            except Exception as e:
                print(f"Viewer init failed: {e}")
                viewer = None

        do_depth_scan = True
        fail_count = 0
        TRACKING_ID = None
        GRID_HORIZONTAL, GRID_VERTICAL = [], []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                fail_count += 1
                print("Camera frame grab failed, retrying...")
                time.sleep(0.01)
                if fail_count > 300000000000000000000000000000000000000000000000000000000000000:
                    print("Camera appears disconnected, stopping tracking.")
                    break
                continue
            fail_count = 0

            frame = cv2.flip(frame, 1)
            annotated_frame = frame.copy()

            # ------------------------------------------------------------
            # Initial depth scan / re-scan
            # ------------------------------------------------------------
            if do_depth_scan:
                self.game_pause_event(broadcast_fn=broadcast_fn, pause=True)
                s = time.perf_counter()

                segmented, _, _ = self.depth_scan(annotated_frame)
                results = self.tracking_model.track(
                    segmented, persist=True, conf=0.1, verbose=verbose
                )

                found = False
                for det in results[0].boxes:
                    if int(det.cls) == self.PERSON:
                        found = True
                        x1, y1, x2, y2 = map(int, det.xyxy[0])
                        TRACKING_ID = int(det.id.item()) if det.id is not None else -1
                        conf = det.conf.item()

                        if fixed_center:
                            center = (
                                annotated_frame.shape[1] // 2,
                                annotated_frame.shape[0] // 2,
                            )
                        else:
                            center = (
                                (x2 - x1) // 2 + x1,
                                (y2 - y1) // 2 + y1,
                            )

                        annotated_frame = cv2.rectangle(
                            annotated_frame, (x1, y1), (x2, y2), self.BBOX_COLOUR, 2
                        )
                        overlay = frame.copy()
                        overlay = cv2.rectangle(
                            overlay, (x1, y1), (x2, y2), self.BBOX_COLOUR, -1
                        )
                        annotated_frame = cv2.addWeighted(
                            overlay, 0.4, annotated_frame, 0.6, 0.0
                        )

                        annotated_frame = cv2.circle(
                            annotated_frame, center, 5, self.GRID_COLOUR, 2
                        )

                        label = f"ID: {TRACKING_ID} | Conf: {conf:.2f}"
                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            self.GRID_COLOUR,
                            2,
                        )

                        GRID_HORIZONTAL, GRID_VERTICAL = [], []

                        for value in self.GRID_OFFSETX:
                            if isinstance(value, int):
                                GRID_HORIZONTAL.append(center[0] + value)
                            else:
                                GRID_HORIZONTAL.append(center[0] + round(value * (x2 - x1)))

                        for value in self.GRID_OFFSETY:
                            if isinstance(value, int):
                                GRID_VERTICAL.append(center[1] + value)
                            else:
                                GRID_VERTICAL.append(center[1] + round(value * (y2 - y1)))

                        annotated_frame = draw_gridlines(
                            annotated_frame,
                            GRID_HORIZONTAL,
                            GRID_VERTICAL,
                            self.GRID_COLOUR,
                        )
                        break

                if not found:
                    print("Depth scan found no person, retrying...")
                    continue

                if save:
                    cv2.imwrite(
                        os.path.join(self.output_dir, "initial_scan.png"),
                        annotated_frame,
                    )

                e = time.perf_counter()
                print(f"Depth scan runtime: {e - s:.6f} seconds")

                do_depth_scan = False
                self.game_pause_event(broadcast_fn=broadcast_fn, pause=True)
                continue

            # ------------------------------------------------------------
            # Tracking loop
            # ------------------------------------------------------------
            results = self.tracking_model.track(
                frame, persist=True, conf=0.1, iou=0.5, verbose=verbose
            )

            annotated_frame = draw_gridlines(
                annotated_frame, GRID_HORIZONTAL, GRID_VERTICAL, self.GRID_COLOUR
            )

            id_found = False

            if results and len(results[0].boxes) > 0:
                for det in results[0].boxes:
                    x1, y1, x2, y2 = map(int, det.xyxy[0])

                    if det.id is not None and int(det.id.item()) == TRACKING_ID:
                        id_found = True
                        center = (
                            (x2 - x1) // 2 + x1,
                            (y2 - y1) // 2 + y1,
                        )

                        xy_center = self.check_position(
                            broadcast_fn, center, GRID_HORIZONTAL, GRID_VERTICAL
                        )
                        conf = det.conf.item()

                        annotated_frame = cv2.rectangle(
                            annotated_frame, (x1, y1), (x2, y2), self.BBOX_COLOUR, 2
                        )
                        overlay = frame.copy()
                        overlay = cv2.rectangle(
                            overlay, (x1, y1), (x2, y2), self.BBOX_COLOUR, -1
                        )
                        annotated_frame = cv2.addWeighted(
                            overlay, 0.4, annotated_frame, 0.6, 0.0
                        )

                        annotated_frame = cv2.circle(
                            annotated_frame, xy_center, 5, self.GRID_COLOUR, 2
                        )

                        label = f"ID: {TRACKING_ID} | Conf: {conf:.2f}"
                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            self.GRID_COLOUR,
                            2,
                        )

                    elif show_other_dets:
                        conf = det.conf.item()
                        tid = int(det.id.item()) if det.id is not None else -1
                        annotated_frame = cv2.rectangle(
                            annotated_frame, (x1, y1), (x2, y2), (100, 0, 0), 1
                        )
                        cv2.putText(
                            annotated_frame,
                            f"ID: {tid} | Conf: {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            self.GRID_COLOUR,
                            1,
                        )

            if not id_found:
                print("Lost track of person, rescanning...")
                do_depth_scan = True

            video_writer.write(annotated_frame)

            if viewer is not None:
                viewer.show(annotated_frame, window_name="Camera")
            else:
                cv2.imshow("Camera", annotated_frame)

            _, buffer = cv2.imencode(".jpg", annotated_frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

            if cv2.waitKey(1) == ord("q"):
                break

        cap.release()
        video_writer.release()

        try:
            if viewer is not None:
                viewer.close()
        except Exception:
            pass



if __name__ == "__main__":
    tracker = Tracker()

    # Use Wayland viewer only when explicitly requested via env var
    use_viewer_flag = bool(os.environ.get("USE_WAYLAND_VIEWER"))

    while True:
        choice = input(">>>")
        if choice == "1":
            tracker.begin_tracking(broadcast_fn=print, save=True, show_other_dets=True, use_wayland_viewer=use_viewer_flag)
        else:

            exit()
