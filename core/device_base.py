from abc import ABC, abstractmethod
from typing import Any, Dict


class DeviceBase(ABC):

    def __init__(self, id: str, params: Dict[str, Any]):
        self.id = id
        self.type = self.__class__.__name__
        self.params = params

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def send_command(self, command: str, **kwargs) -> Any:
        pass
