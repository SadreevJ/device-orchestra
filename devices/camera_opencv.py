import cv2
import os
import time
from typing import Dict, Any
import numpy as np
from core.device_base import DeviceBase


class OpenCVCamera(DeviceBase):

    def __init__(self, id: str, params: Dict[str, Any]):
        super().__init__(id, params)
        self.index = params.get("index", 0)
        self.resolution = params.get("resolution", [1920, 1080])
        self.fps = params.get("fps", 30)
        self.capture = None
        self._started = False

    def start(self) -> None:
        try:
            self.capture = cv2.VideoCapture(self.index)
            if not self.capture.isOpened():
                raise RuntimeError(f"Не удалось открыть камеру с индексом {self.index}")

            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)

            ret, frame = self.capture.read()
            if not ret:
                raise RuntimeError("Камера не возвращает кадры")

            self._started = True

        except Exception as e:
            if self.capture:
                self.capture.release()
                self.capture = None
            raise RuntimeError(f"Ошибка запуска камеры: {e}")

    def stop(self) -> None:
        if self.capture:
            self.capture.release()
            self.capture = None
        self._started = False

    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "started": self._started,
            "index": self.index,
            "resolution": self.resolution,
            "fps": self.fps,
            "connected": (self.capture is not None and self.capture.isOpened() if self.capture else False),
        }

    def send_command(self, command: str, **kwargs) -> Any:
        if not self._started:
            raise RuntimeError(f"Камера {self.id} не запущена")

        if command == "capture":
            return self.capture_frame(**kwargs)
        elif command == "get_frame":
            return self.get_current_frame()
        elif command == "save_frame":
            return self.save_frame(**kwargs)
        else:
            raise ValueError(f"Неизвестная команда камеры: {command}")

    def capture_frame(self, save_to: str = None, **kwargs) -> Dict[str, Any]:

        if not self.capture or not self.capture.isOpened():
            raise RuntimeError("Камера не подключена")

        ret, frame = self.capture.read()
        if not ret:
            raise RuntimeError("Не удалось захватить кадр")

        result = {
            "timestamp": time.time(),
            "resolution": [frame.shape[1], frame.shape[0]],
            "channels": frame.shape[2] if len(frame.shape) > 2 else 1,
            "frame_data": frame,
        }

        if save_to:
            success = self._save_frame_to_file(frame, save_to)
            result["saved"] = success
            result["save_to"] = save_to if success else None

        return result

    def get_current_frame(self) -> Any:
        if not self.capture or not self.capture.isOpened():
            raise RuntimeError("Камера не подключена")

        ret, frame = self.capture.read()
        if not ret:
            raise RuntimeError("Не удалось получить кадр")

        return frame

    def save_frame(self, filepath: str, **kwargs) -> Dict[str, Any]:
        frame = self.get_current_frame()
        success = self._save_frame_to_file(frame, filepath)

        return {
            "saved": success,
            "filepath": filepath if success else None,
            "timestamp": time.time(),
        }

    def _save_frame_to_file(self, frame: np.ndarray, filepath: str) -> bool:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Сохранение кадра
            success = cv2.imwrite(filepath, frame)
            return success

        except Exception:
            return False
