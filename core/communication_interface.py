from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import asyncio
from enum import Enum


class ConnectionState(Enum):
    """Состояния соединения с устройством"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ProtocolVersion(Enum):
    """Версии протоколов связи"""
    V1_0 = "1.0"
    V2_0 = "2.0"
    V3_0 = "3.0"


class CommunicationInterface(ABC):
    """
    Базовый абстрактный класс для интерфейсов связи с устройствами.
    
    Обеспечивает унифицированный API для различных типов соединений:
    - Serial порты
    - HTTP/REST API
    - WebSocket
    - SSH
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация интерфейса связи.
        
        Args:
            config: Конфигурация соединения (порт, URL, параметры и т.д.)
        """
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.protocol_version = ProtocolVersion.V1_0
        self.connection_pool = {}
        self._lock = asyncio.Lock()
        self._logger = None  # Будет установлен в наследниках

    @abstractmethod
    async def connect(self) -> bool:
        """
        Асинхронное подключение к устройству.
        
        Returns:
            True если подключение успешно, False в противном случае
            
        Raises:
            RuntimeError: При ошибке подключения
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Асинхронное отключение от устройства.
        
        Returns:
            True если отключение успешно, False в противном случае
            
        Raises:
            RuntimeError: При ошибке отключения
        """
        pass

    @abstractmethod
    async def send_command(self, command: str, **kwargs) -> Any:
        """
        Асинхронная отправка команды устройству.
        
        Args:
            command: Команда для отправки
            **kwargs: Дополнительные параметры команды
            
        Returns:
            Ответ от устройства
            
        Raises:
            RuntimeError: При ошибке отправки команды
        """
        pass

    @abstractmethod
    async def read_response(self, timeout: float = 5.0) -> Optional[Any]:
        """
        Асинхронное чтение ответа от устройства.
        
        Args:
            timeout: Таймаут ожидания ответа в секундах
            
        Returns:
            Ответ от устройства или None если таймаут
            
        Raises:
            RuntimeError: При ошибке чтения ответа
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса соединения.
        
        Returns:
            Словарь с информацией о состоянии соединения
        """
        return {
            "state": self.state.value,
            "protocol_version": self.protocol_version.value,
            "config": self.config,
            "connected": self.state == ConnectionState.CONNECTED
        }

    async def is_connected(self) -> bool:
        """
        Проверка состояния соединения.
        
        Returns:
            True если соединение активно
        """
        return self.state == ConnectionState.CONNECTED

    def set_protocol_version(self, version: Union[str, ProtocolVersion]) -> None:
        """
        Установка версии протокола.
        
        Args:
            version: Версия протокола (строка или enum)
        """
        if isinstance(version, str):
            try:
                self.protocol_version = ProtocolVersion(version)
            except ValueError:
                raise ValueError(f"Неизвестная версия протокола: {version}")
        else:
            self.protocol_version = version

    async def health_check(self) -> bool:
        """
        Проверка здоровья соединения.
        
        Returns:
            True если соединение здорово
        """
        try:
            if not await self.is_connected():
                return False
            
            # Простая проверка - отправка ping команды
            response = await self.send_command("ping")
            return response is not None
            
        except Exception:
            return False

    def get_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации соединения.
        
        Returns:
            Копия конфигурации
        """
        return self.config.copy()
