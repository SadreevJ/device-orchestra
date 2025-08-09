from typing import Dict, Type, Any
from .device_base import DeviceBase
import logging


class DeviceFactory:

    def __init__(self):
        self.device_classes: Dict[str, Type[DeviceBase]] = {}
        self.logger = logging.getLogger("ucdf.factory")

    def register(self, device_type: str, device_class: Type[DeviceBase]) -> None:
        self.device_classes[device_type] = device_class
        self.logger.info(f"Зарегистрирован тип устройства: {device_type}")

    def create(self, device_type: str, device_id: str, params: Dict[str, Any]) -> DeviceBase:
        if device_type not in self.device_classes:
            available_types = list(self.device_classes.keys())
            raise ValueError(f"Неизвестный тип устройства: {device_type}. " f"Доступные типы: {available_types}")

        device_class = self.device_classes[device_type]
        device = device_class(device_id, params)
        self.logger.info(f"Создано устройство: {device_id} ({device_type})")
        return device

    def get_registered_types(self) -> list:
        return list(self.device_classes.keys())

    def is_registered(self, device_type: str) -> bool:
        return device_type in self.device_classes


device_factory = DeviceFactory()
