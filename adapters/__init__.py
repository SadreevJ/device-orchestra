"""
Адаптеры связи для device-orchestra.

Этот модуль содержит различные адаптеры для связи с устройствами:
- SerialAdapter: Синхронный адаптер для Serial портов
- AsyncSerialAdapter: Асинхронный адаптер для Serial портов
"""

from .serial_adapter import SerialAdapter
from .async_serial_adapter import AsyncSerialAdapter

# Регистрация адаптеров в фабрике
from core.communication_factory import CommunicationFactory

# Регистрируем асинхронный serial адаптер
CommunicationFactory.register("serial", AsyncSerialAdapter)

__all__ = [
    "SerialAdapter",
    "AsyncSerialAdapter",
]
