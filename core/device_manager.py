from typing import Dict, List, Any
import logging
from .device_base import DeviceBase
from .config_loader import ConfigLoader
from .device_factory import device_factory


class DeviceManager:

    def __init__(self):
        self.devices: Dict[str, DeviceBase] = {}
        self.config_loader = ConfigLoader()
        self.logger = logging.getLogger("device-orchestra.device_manager")

    def load_config(self, path: str) -> None:
        self.config_loader = ConfigLoader(path if "/" in path else "config")
        devices_config = self.config_loader.load_devices_config()

        for device_config in devices_config:
            device_id = device_config["id"]
            device_type = device_config["type"]
            params = device_config["params"]

            try:
                device = device_factory.create(device_type, device_id, params)
                self.devices[device_id] = device
                self.logger.info(f"Загружено устройство: {device_id}")
            except ValueError as e:
                self.logger.error(f"Ошибка создания устройства {device_id}: {e}")

    def register_device_instance(self, device: DeviceBase) -> None:
        self.devices[device.id] = device
        self.logger.info(f"Зарегистрировано устройство: {device.id}")

    def get(self, device_id: str) -> DeviceBase:
        if device_id not in self.devices:
            raise ValueError(f"Устройство {device_id} не найдено")
        return self.devices[device_id]

    def start(self, device_id: str) -> None:
        device = self.get(device_id)
        device.start()
        self.logger.info(f"Запущено устройство: {device_id}")

    def stop(self, device_id: str) -> None:
        device = self.get(device_id)
        device.stop()
        self.logger.info(f"Остановлено устройство: {device_id}")

    def list(self) -> List[Dict]:
        devices_list = []
        for device_id, device in self.devices.items():
            device_info = {
                "id": device.id,
                "type": device.type,
                "status": device.status(),
            }
            devices_list.append(device_info)
        return devices_list
