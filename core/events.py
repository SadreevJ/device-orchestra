from typing import Any, Callable, Dict, List
import logging


class EventBus:

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("ucdf.events")

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Добавлен подписчик на событие: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                self.logger.debug(f"Удален подписчик события: {event_type}")
            except ValueError:
                self.logger.warning(f"Подписчик не найден для события: {event_type}")

    def emit(self, event_type: str, data: Any = None) -> None:
        if event_type in self.subscribers:
            self.logger.debug(f"Отправка события: {event_type} с данными: {data}")
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Ошибка в обработчике события {event_type}: {e}")


event_bus = EventBus()


class DeviceEvent:
    DEVICE_STARTED = "device.started"
    DEVICE_STOPPED = "device.stopped"
    DEVICE_ERROR = "device.error"
    DEVICE_DATA = "device.data"
    DEVICE_STATUS_CHANGED = "device.status_changed"
