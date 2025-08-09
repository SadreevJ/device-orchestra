import time
import random
from typing import Dict, Any
from core.device_base import DeviceBase


class FakeDevice(DeviceBase):

    def __init__(self, id: str, params: Dict[str, Any]):
        super().__init__(id, params)
        self.simulation_mode = params.get("simulation_mode", "normal")
        self.base_delay = params.get("base_delay", 0.1)
        self.error_probability = params.get("error_probability", 0.02)
        self.device_type = params.get("device_type", "generic")
        self._started = False
        self._data_counter = 0

    def start(self) -> None:
        self._simulate_delay()
        if self._should_simulate_error():
            raise RuntimeError("Симулированная ошибка запуска")
        self._started = True

    def stop(self) -> None:
        self._simulate_delay(0.05)
        self._started = False

    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "started": self._started,
            "device_type": self.device_type,
            "simulation_mode": self.simulation_mode,
            "data_counter": self._data_counter,
        }

    def send_command(self, command: str, **kwargs) -> Any:
        if not self._started:
            raise RuntimeError(f"Устройство {self.id} не запущено")

        self._simulate_delay()

        if self._should_simulate_error():
            raise RuntimeError(f"Симулированная ошибка команды: {command}")

        self._data_counter += 1

        if self.device_type == "camera":
            return self._simulate_camera_command(command, **kwargs)
        elif self.device_type == "sensor":
            return self._simulate_sensor_command(command, **kwargs)
        elif self.device_type == "motor":
            return self._simulate_motor_command(command, **kwargs)
        else:
            return self._simulate_generic_command(command, **kwargs)

    def _simulate_camera_command(self, command: str, **kwargs) -> Any:
        if command == "capture":
            return {
                "image_id": f"fake_img_{self._data_counter}",
                "timestamp": time.time(),
                "resolution": kwargs.get("resolution", [640, 480]),
                "format": kwargs.get("format", "jpg"),
                "save_to": kwargs.get(
                    "save_to", f"images/fake_{self._data_counter}.jpg"
                ),
            }
        elif command == "get_frame":
            return f"fake_frame_data_{self._data_counter}"
        else:
            return self._simulate_generic_command(command, **kwargs)

    def _simulate_sensor_command(self, command: str, **kwargs) -> Any:
        if command == "read":
            return {
                "value": round(random.uniform(18.0, 25.0), 2),
                "unit": "°C",
                "timestamp": time.time(),
                "reading_id": self._data_counter,
            }
        else:
            return self._simulate_generic_command(command, **kwargs)

    def _simulate_motor_command(self, command: str, **kwargs) -> Any:
        if command == "move":
            steps = kwargs.get("steps", 100)
            return {"steps_moved": steps, "position": self._data_counter}
        elif command == "home":
            return {"status": "homed", "position": 0}
        elif command == "stop":
            return {"status": "stopped"}
        else:
            return self._simulate_generic_command(command, **kwargs)

    def _simulate_generic_command(self, command: str, **kwargs) -> Any:
        return {
            "command": command,
            "params": kwargs,
            "result": f"Executed {command}",
            "execution_id": self._data_counter,
            "timestamp": time.time(),
        }

    def _simulate_delay(self, override_delay: float = None):
        delay = override_delay if override_delay is not None else self.base_delay

        if self.simulation_mode == "slow":
            delay *= 3
        elif self.simulation_mode == "fast":
            delay *= 0.3
        elif self.simulation_mode == "unstable":
            delay *= random.uniform(0.5, 2.0)

        if delay > 0:
            time.sleep(delay)

    def _should_simulate_error(self) -> bool:
        return random.random() < self.error_probability
