"""
Video processor for the gallery camera.

FastAPI mode: browser sends binary JPEG frames over WebSocket.
push_frame(jpeg_bytes) decodes and runs the analysis pipeline.

Analysis runs in a background thread at ~10 Hz. Thread-safe CameraState
is written there and read by the WebSocket handler on the main thread.
"""

import copy
import cv2
import threading
import time
import urllib.request
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from vision.face_detector import FaceResult
from vision.gaze import is_looking_at_camera, most_centered_face
from config import MIN_FACE_AREA_FRACTION, EMOTION_SAMPLE_RATE_HZ

_MODEL_POINTS = np.array([
    [0.0,    0.0,    0.0],
    [0.0,  -330.0,  -65.0],
    [-225.0, 170.0, -135.0],
    [225.0,  170.0, -135.0],
    [-150.0,-150.0, -125.0],
    [150.0, -150.0, -125.0],
], dtype=np.float64)

_LANDMARK_INDICES = [4, 152, 263, 33, 287, 57]

_POSE_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"


def _download(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception:
        return False


def _head_pose(landmarks, w: int, h: int) -> tuple:
    try:
        image_points = np.array(
            [[landmarks[i].x * w, landmarks[i].y * h] for i in _LANDMARK_INDICES],
            dtype=np.float64,
        )
        focal = w
        cam = np.array([[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]], dtype=np.float64)
        ok, rvec, _ = cv2.solvePnP(_MODEL_POINTS, image_points, cam, np.zeros((4, 1)),
                                    flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return 0.0, 0.0, 0.0
        rmat, _ = cv2.Rodrigues(rvec)
        angles, *_ = cv2.RQDecomp3x3(rmat)
        return float(angles[1]), float(angles[0]), float(angles[2])
    except Exception:
        return 0.0, 0.0, 0.0


_HANDS_DOWN_GRACE_S = 0.4  # ignore brief detection dropouts up to this long

@dataclass
class CameraState:
    face_present: bool = False
    face_centered: bool = False
    hands_raised: bool = False
    hands_raised_since: Optional[float] = None
    stable_since: Optional[float] = None
    latest_emotions: dict = field(default_factory=dict)
    frame_w: int = 640
    frame_h: int = 480
    num_faces: int = 0


class GalleryProcessor:
    """Frame processor for the FastAPI backend. Call push_frame() with JPEG bytes."""

    def __init__(self):
        self._state_lock = threading.Lock()
        self._state = CameraState()

        self._frame_lock = threading.Lock()
        self._latest_rgb: Optional[np.ndarray] = None
        self._latest_shape: tuple = (480, 640)

        self._do_emotion = False
        self._do_pose = True
        self._running = True
        self._hands_down_since: Optional[float] = None  # debounce: when hands first went down

        self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()

    def get_state(self) -> CameraState:
        with self._state_lock:
            return copy.copy(self._state)

    def set_emotion_sampling(self, active: bool):
        self._do_emotion = active

    def set_pose_sampling(self, active: bool):
        self._do_pose = active

    def push_frame(self, jpeg_bytes: bytes):
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        with self._frame_lock:
            self._latest_rgb = img_rgb
            self._latest_shape = (h, w)

    def stop(self):
        self._running = False

    def _analysis_loop(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        from vision.emotion import _blendshapes_to_emotions, _MODEL_CACHE, _MODEL_URL

        if not _MODEL_CACHE.exists() and not _download(_MODEL_URL, _MODEL_CACHE):
            return

        _POSE_CACHE = _MODEL_CACHE.parent / "pose_landmarker_lite.task"
        if not _POSE_CACHE.exists():
            _download(_POSE_URL, _POSE_CACHE)

        base_opts = mp_python.BaseOptions(model_asset_path=str(_MODEL_CACHE))
        opts = mp_vision.FaceLandmarkerOptions(
            base_options=base_opts,
            output_face_blendshapes=True,
            num_faces=4,
            min_face_detection_confidence=0.4,
            min_face_presence_confidence=0.4,
            min_tracking_confidence=0.4,
        )
        landmarker = mp_vision.FaceLandmarker.create_from_options(opts)

        pose_landmarker = None
        if _POSE_CACHE.exists():
            try:
                pose_opts = mp_vision.PoseLandmarkerOptions(
                    base_options=mp_python.BaseOptions(model_asset_path=str(_POSE_CACHE)),
                    num_poses=1,
                    min_pose_detection_confidence=0.4,
                    min_tracking_confidence=0.4,
                )
                pose_landmarker = mp_vision.PoseLandmarker.create_from_options(pose_opts)
            except Exception:
                pose_landmarker = None

        target_interval = 1.0 / EMOTION_SAMPLE_RATE_HZ

        while self._running:
            loop_start = time.time()

            with self._frame_lock:
                rgb = self._latest_rgb
                shape = self._latest_shape

            if rgb is None:
                time.sleep(0.05)
                continue

            h, w = shape

            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect(mp_image)
            except Exception:
                time.sleep(0.1)
                continue

            faces: list = []
            emotions: dict = {}

            if result.face_landmarks:
                for i, lm_list in enumerate(result.face_landmarks):
                    xs = [lm.x * w for lm in lm_list]
                    ys = [lm.y * h for lm in lm_list]
                    x1, x2 = int(min(xs)), int(max(xs))
                    y1, y2 = int(min(ys)), int(max(ys))
                    bw, bh = x2 - x1, y2 - y1
                    area_fraction = (bw * bh) / (w * h)
                    if area_fraction < MIN_FACE_AREA_FRACTION:
                        continue
                    yaw, pitch, roll = _head_pose(lm_list, w, h)
                    faces.append(FaceResult(
                        bbox=(x1, y1, bw, bh),
                        landmarks=lm_list,
                        head_yaw=yaw,
                        head_pitch=pitch,
                        head_roll=roll,
                        area_fraction=area_fraction,
                    ))

                if self._do_emotion and result.face_blendshapes:
                    emotions = _blendshapes_to_emotions(result.face_blendshapes[0])

            target = most_centered_face(faces, w, h)
            looking = target is not None and is_looking_at_camera(target)

            hands_up = False
            if self._do_pose and pose_landmarker is not None:
                try:
                    pose_result = pose_landmarker.detect(mp_image)
                    if pose_result.pose_landmarks:
                        pose = pose_result.pose_landmarks[0]
                        hands_up = (
                            pose[15].y < pose[11].y
                            and pose[16].y < pose[12].y
                        )
                except Exception:
                    pass

            now = time.time()
            with self._state_lock:
                prev_looking = self._state.face_centered
                prev_hands = self._state.hands_raised
                self._state.face_present = target is not None
                self._state.face_centered = looking
                self._state.frame_w = w
                self._state.frame_h = h
                self._state.num_faces = len(faces)
                if emotions:
                    self._state.latest_emotions = emotions
                if looking and not prev_looking:
                    self._state.stable_since = now
                elif not looking:
                    self._state.stable_since = None
                if hands_up:
                    self._hands_down_since = None
                    self._state.hands_raised = True
                    if not prev_hands:
                        self._state.hands_raised_since = now
                else:
                    if self._hands_down_since is None:
                        self._hands_down_since = now
                    grace_expired = (now - self._hands_down_since) >= _HANDS_DOWN_GRACE_S
                    if grace_expired:
                        self._state.hands_raised = False
                        self._state.hands_raised_since = None

            elapsed_loop = time.time() - loop_start
            time.sleep(max(0.01, target_interval - elapsed_loop))

        landmarker.close()
        if pose_landmarker:
            pose_landmarker.close()
