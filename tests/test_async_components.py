"""
Unit тесты для асинхронных компонентов device-orchestra.

Тестирует:
- CommunicationInterface
- CommunicationFactory
- AsyncSerialAdapter
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from core.communication_interface import (
    CommunicationInterface, 
    ConnectionState, 
    ProtocolVersion
)
from core.communication_factory import CommunicationFactory
from adapters.async_serial_adapter import AsyncSerialAdapter


class TestCommunicationInterface:
    """Тесты для базового интерфейса связи."""
    
    def test_connection_state_enum(self):
        """Тест enum состояний соединения."""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.ERROR.value == "error"
    
    def test_protocol_version_enum(self):
        """Тест enum версий протоколов."""
        assert ProtocolVersion.V1_0.value == "1.0"
        assert ProtocolVersion.V2_0.value == "2.0"
        assert ProtocolVersion.V3_0.value == "3.0"
    
    def test_interface_initialization(self):
        """Тест инициализации интерфейса."""
        config = {"test": "value"}
        
        # Создаем мок-класс для тестирования абстрактного класса
        class MockInterface(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        interface = MockInterface(config)
        
        assert interface.config == config
        assert interface.state == ConnectionState.DISCONNECTED
        assert interface.protocol_version == ProtocolVersion.V1_0
        assert interface.connection_pool == {}
    
    def test_get_status(self):
        """Тест получения статуса."""
        class MockInterface(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        config = {"port": "/dev/ttyUSB0"}
        interface = MockInterface(config)
        
        status = interface.get_status()
        
        assert status["state"] == "disconnected"
        assert status["protocol_version"] == "1.0"
        assert status["config"] == config
        assert status["connected"] is False
    
    @pytest.mark.asyncio
    async def test_is_connected(self):
        """Тест проверки состояния соединения."""
        class MockInterface(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        interface = MockInterface({})
        
        # Изначально не подключен
        assert await interface.is_connected() is False
        
        # Подключаемся
        interface.state = ConnectionState.CONNECTED
        assert await interface.is_connected() is True
    
    def test_set_protocol_version(self):
        """Тест установки версии протокола."""
        class MockInterface(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        interface = MockInterface({})
        
        # Установка версии строкой
        interface.set_protocol_version("2.0")
        assert interface.protocol_version == ProtocolVersion.V2_0
        
        # Установка версии enum
        interface.set_protocol_version(ProtocolVersion.V3_0)
        assert interface.protocol_version == ProtocolVersion.V3_0
        
        # Неверная версия
        with pytest.raises(ValueError):
            interface.set_protocol_version("invalid")


class TestCommunicationFactory:
    """Тесты для фабрики адаптеров связи."""
    
    def setup_method(self):
        """Очистка фабрики перед каждым тестом."""
        CommunicationFactory.clear()
    
    def test_register_adapter(self):
        """Тест регистрации адаптера."""
        class MockAdapter(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        CommunicationFactory.register("mock", MockAdapter)
        assert "mock" in CommunicationFactory.list_available()
    
    def test_register_duplicate_adapter(self):
        """Тест регистрации дубликата адаптера."""
        class MockAdapter(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        CommunicationFactory.register("mock", MockAdapter)
        
        with pytest.raises(ValueError, match="уже зарегистрирован"):
            CommunicationFactory.register("mock", MockAdapter)
    
    def test_register_invalid_adapter(self):
        """Тест регистрации неверного адаптера."""
        class InvalidAdapter:
            pass
        
        with pytest.raises(ValueError, match="должен наследоваться"):
            CommunicationFactory.register("invalid", InvalidAdapter)
    
    def test_create_adapter(self):
        """Тест создания адаптера."""
        class MockAdapter(CommunicationInterface):
            def __init__(self, config):
                super().__init__(config)
                self.test_config = config
            
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        CommunicationFactory.register("mock", MockAdapter)
        
        config = {"test": "value"}
        adapter = CommunicationFactory.create("mock", config)
        
        assert isinstance(adapter, MockAdapter)
        assert adapter.test_config == config
    
    def test_create_unknown_adapter(self):
        """Тест создания неизвестного адаптера."""
        with pytest.raises(ValueError, match="Неизвестный тип адаптера"):
            CommunicationFactory.create("unknown", {})
    
    def test_list_available(self):
        """Тест получения списка доступных адаптеров."""
        class MockAdapter(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        assert len(CommunicationFactory.list_available()) == 0
        
        CommunicationFactory.register("mock1", MockAdapter)
        CommunicationFactory.register("mock2", MockAdapter)
        
        available = CommunicationFactory.list_available()
        assert "mock1" in available
        assert "mock2" in available
        assert len(available) == 2
    
    def test_is_registered(self):
        """Тест проверки регистрации адаптера."""
        class MockAdapter(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        assert CommunicationFactory.is_registered("mock") is False
        
        CommunicationFactory.register("mock", MockAdapter)
        assert CommunicationFactory.is_registered("mock") is True
    
    def test_unregister_adapter(self):
        """Тест удаления регистрации адаптера."""
        class MockAdapter(CommunicationInterface):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> bool:
                return True
            
            async def send_command(self, command: str, **kwargs) -> Any:
                return "OK"
            
            async def read_response(self, timeout: float = 5.0) -> Any:
                return "response"
        
        CommunicationFactory.register("mock", MockAdapter)
        assert CommunicationFactory.is_registered("mock") is True
        
        assert CommunicationFactory.unregister("mock") is True
        assert CommunicationFactory.is_registered("mock") is False
        
        # Удаление несуществующего адаптера
        assert CommunicationFactory.unregister("unknown") is False


class TestAsyncSerialAdapter:
    """Тесты для асинхронного Serial адаптера."""
    
    def test_adapter_initialization(self):
        """Тест инициализации адаптера."""
        config = {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
            "timeout": 2.0,
            "protocol_version": "2.0"
        }
        
        adapter = AsyncSerialAdapter(config)
        
        assert adapter.port == "/dev/ttyUSB0"
        assert adapter.baudrate == 9600
        assert adapter.timeout == 2.0
        assert adapter.protocol_version == ProtocolVersion.V2_0
        assert adapter.state == ConnectionState.DISCONNECTED
    
    def test_adapter_default_config(self):
        """Тест конфигурации по умолчанию."""
        adapter = AsyncSerialAdapter({})
        
        assert adapter.port == "/dev/ttyUSB0"
        assert adapter.baudrate == 115200
        assert adapter.timeout == 1.0
        assert adapter.protocol_version == ProtocolVersion.V1_0
    
    @pytest.mark.asyncio
    async def test_connect_without_serial_asyncio(self):
        """Тест подключения без serial_asyncio (эмуляция)."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        with patch('builtins.__import__', side_effect=ImportError):
            result = await adapter.connect()
            
            assert result is True
            assert adapter.state == ConnectionState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Тест отключения."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        # Подключаемся сначала
        with patch('builtins.__import__', side_effect=ImportError):
            await adapter.connect()
        
        # Отключаемся
        result = await adapter.disconnect()
        
        assert result is True
        assert adapter.state == ConnectionState.DISCONNECTED
        assert adapter._reader is None
        assert adapter._writer is None
    
    @pytest.mark.asyncio
    async def test_send_command_not_connected(self):
        """Тест отправки команды без подключения."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        with pytest.raises(RuntimeError, match="Не подключен"):
            await adapter.send_command("test")
    
    @pytest.mark.asyncio
    async def test_send_command_emulation(self):
        """Тест отправки команды в режиме эмуляции."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        # Подключаемся в режиме эмуляции
        with patch('builtins.__import__', side_effect=ImportError):
            await adapter.connect()
        
        # Отправляем команду
        response = await adapter.send_command("test", param1="value1")
        
        assert response == "OK:1.0"
    
    @pytest.mark.asyncio
    async def test_read_response_not_connected(self):
        """Тест чтения ответа без подключения."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        with pytest.raises(RuntimeError, match="Не подключен"):
            await adapter.read_response()
    
    @pytest.mark.asyncio
    async def test_read_response_emulation(self):
        """Тест чтения ответа в режиме эмуляции."""
        adapter = AsyncSerialAdapter({"port": "/dev/ttyUSB0"})
        
        # Подключаемся в режиме эмуляции
        with patch('builtins.__import__', side_effect=ImportError):
            await adapter.connect()
        
        # Читаем ответ
        response = await adapter.read_response()
        
        assert response == "OK:1.0"
    
    def test_get_status(self):
        """Тест получения статуса."""
        config = {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
            "timeout": 2.0
        }
        
        adapter = AsyncSerialAdapter(config)
        status = adapter.get_status()
        
        assert status["port"] == "/dev/ttyUSB0"
        assert status["baudrate"] == 9600
        assert status["timeout"] == 2.0
        assert status["state"] == "disconnected"
        assert status["connected"] is False
        assert status["has_reader"] is False
        assert status["has_writer"] is False


class TestIntegration:
    """Интеграционные тесты."""
    
    def setup_method(self):
        """Очистка фабрики перед каждым тестом."""
        CommunicationFactory.clear()
    
    @pytest.mark.asyncio
    async def test_factory_with_serial_adapter(self):
        """Тест фабрики с Serial адаптером."""
        # Регистрируем адаптер
        CommunicationFactory.register("serial", AsyncSerialAdapter)
        
        # Создаем адаптер через фабрику
        config = {"port": "/dev/ttyUSB0", "baudrate": 115200}
        adapter = CommunicationFactory.create("serial", config)
        
        assert isinstance(adapter, AsyncSerialAdapter)
        assert adapter.port == "/dev/ttyUSB0"
        assert adapter.baudrate == 115200
        
        # Тестируем подключение в режиме эмуляции
        with patch('builtins.__import__', side_effect=ImportError):
            result = await adapter.connect()
            assert result is True
            assert adapter.state == ConnectionState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_command_with_protocol_version(self):
        """Тест отправки команды с версией протокола."""
        adapter = AsyncSerialAdapter({
            "port": "/dev/ttyUSB0",
            "protocol_version": "2.0"
        })
        
        # Подключаемся в режиме эмуляции
        with patch('builtins.__import__', side_effect=ImportError):
            await adapter.connect()
        
        # Отправляем команду
        response = await adapter.send_command("MOVE", steps=100)
        
        assert response == "OK:2.0"
        assert adapter.protocol_version == ProtocolVersion.V2_0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
