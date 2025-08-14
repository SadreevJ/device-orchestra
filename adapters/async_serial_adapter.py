import asyncio
import logging
from typing import Any, Optional, Dict
from core.communication_interface import CommunicationInterface, ConnectionState, ProtocolVersion


class AsyncSerialAdapter(CommunicationInterface):
    """
    Асинхронный адаптер для работы с Serial портами.
    
    Поддерживает асинхронное подключение, отправку команд и чтение ответов
    через последовательные порты с поддержкой версионирования протоколов.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация асинхронного Serial адаптера.
        
        Args:
            config: Конфигурация соединения
                - port: Порт для подключения (например, "/dev/ttyUSB0")
                - baudrate: Скорость передачи (по умолчанию 115200)
                - timeout: Таймаут операций (по умолчанию 1.0)
                - protocol_version: Версия протокола (по умолчанию "1.0")
        """
        super().__init__(config)
        
        # Параметры соединения
        self.port = config.get("port", "/dev/ttyUSB0")
        self.baudrate = config.get("baudrate", 115200)
        self.timeout = config.get("timeout", 1.0)
        self.data_bits = config.get("data_bits", 8)
        self.parity = config.get("parity", "N")
        self.stop_bits = config.get("stop_bits", 1)
        
        # Установка версии протокола
        protocol_version = config.get("protocol_version", "1.0")
        self.set_protocol_version(protocol_version)
        
        # Внутренние переменные
        self._reader = None
        self._writer = None
        self._logger = logging.getLogger(f"device-orchestra.serial.{self.port}")

    async def connect(self) -> bool:
        """
        Асинхронное подключение к Serial порту.
        
        Returns:
            True если подключение успешно
            
        Raises:
            RuntimeError: При ошибке подключения
        """
        try:
            self.state = ConnectionState.CONNECTING
            self._logger.info(f"Подключение к {self.port} ({self.baudrate} baud)")
            
            # Попытка импорта serial_asyncio
            try:
                import serial_asyncio
            except ImportError:
                self._logger.warning("serial_asyncio не установлен, используем эмуляцию")
                self.state = ConnectionState.CONNECTED
                return True
            
            # Создание асинхронного соединения
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=self.data_bits,
                parity=self.parity,
                stopbits=self.stop_bits
            )
            
            self.state = ConnectionState.CONNECTED
            self._logger.info(f"Успешно подключен к {self.port}")
            return True
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            error_msg = f"Ошибка подключения к {self.port}: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def disconnect(self) -> bool:
        """
        Асинхронное отключение от Serial порта.
        
        Returns:
            True если отключение успешно
            
        Raises:
            RuntimeError: При ошибке отключения
        """
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
            
            self._reader = None
            self._writer = None
            self.state = ConnectionState.DISCONNECTED
            self._logger.info(f"Отключен от {self.port}")
            return True
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            error_msg = f"Ошибка отключения от {self.port}: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def send_command(self, command: str, **kwargs) -> Any:
        """
        Асинхронная отправка команды через Serial порт.
        
        Args:
            command: Команда для отправки
            **kwargs: Дополнительные параметры команды
            
        Returns:
            Ответ от устройства
            
        Raises:
            RuntimeError: При ошибке отправки команды
        """
        if self.state != ConnectionState.CONNECTED:
            raise RuntimeError(f"Не подключен к {self.port}")
        
        try:
            # Формирование команды с версией протокола
            versioned_command = f"{self.protocol_version.value}:{command}"
            
            # Добавление параметров к команде
            if kwargs:
                params_str = " ".join([f"{k}={v}" for k, v in kwargs.items()])
                versioned_command += f" {params_str}"
            
            # Добавление завершающего символа
            command_with_ending = versioned_command + "\r\n"
            
            self._logger.debug(f"Отправка команды: {versioned_command}")
            
            # Отправка команды
            if self._writer:
                self._writer.write(command_with_ending.encode("utf-8"))
                await self._writer.drain()
            else:
                # Эмуляция для тестов
                self._logger.debug(f"Эмуляция отправки: {versioned_command}")
            
            # Чтение ответа
            return await self.read_response()
            
        except Exception as e:
            error_msg = f"Ошибка отправки команды '{command}': {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def read_response(self, timeout: float = 5.0) -> Optional[Any]:
        """
        Асинхронное чтение ответа от Serial порта.
        
        Args:
            timeout: Таймаут ожидания ответа в секундах
            
        Returns:
            Ответ от устройства или None если таймаут
            
        Raises:
            RuntimeError: При ошибке чтения ответа
        """
        if self.state != ConnectionState.CONNECTED:
            raise RuntimeError(f"Не подключен к {self.port}")
        
        try:
            if self._reader:
                # Асинхронное чтение с таймаутом
                response = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=timeout
                )
                
                if response:
                    decoded_response = response.decode("utf-8").strip()
                    self._logger.debug(f"Получен ответ: {decoded_response}")
                    return decoded_response
                else:
                    self._logger.warning("Пустой ответ от устройства")
                    return None
            else:
                # Эмуляция для тестов
                await asyncio.sleep(0.1)  # Симуляция задержки
                return f"OK:{self.protocol_version.value}"
                
        except asyncio.TimeoutError:
            error_msg = f"Таймаут ожидания ответа ({timeout}s)"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Ошибка чтения ответа: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def send_raw_data(self, data: bytes) -> bool:
        """
        Отправка сырых данных через Serial порт.
        
        Args:
            data: Данные для отправки в байтах
            
        Returns:
            True если отправка успешна
        """
        if self.state != ConnectionState.CONNECTED:
            raise RuntimeError(f"Не подключен к {self.port}")
        
        try:
            if self._writer:
                self._writer.write(data)
                await self._writer.drain()
                return True
            else:
                self._logger.debug(f"Эмуляция отправки сырых данных: {data}")
                return True
                
        except Exception as e:
            error_msg = f"Ошибка отправки сырых данных: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def read_raw_data(self, size: int = 1) -> Optional[bytes]:
        """
        Чтение сырых данных из Serial порта.
        
        Args:
            size: Количество байт для чтения
            
        Returns:
            Прочитанные данные или None
        """
        if self.state != ConnectionState.CONNECTED:
            raise RuntimeError(f"Не подключен к {self.port}")
        
        try:
            if self._reader:
                data = await self._reader.read(size)
                return data if data else None
            else:
                # Эмуляция для тестов
                await asyncio.sleep(0.1)
                return b"OK\r\n"
                
        except Exception as e:
            error_msg = f"Ошибка чтения сырых данных: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_status(self) -> Dict[str, Any]:
        """
        Получение расширенного статуса Serial соединения.
        
        Returns:
            Словарь с информацией о состоянии соединения
        """
        base_status = super().get_status()
        base_status.update({
            "port": self.port,
            "baudrate": self.baudrate,
            "timeout": self.timeout,
            "data_bits": self.data_bits,
            "parity": self.parity,
            "stop_bits": self.stop_bits,
            "has_reader": self._reader is not None,
            "has_writer": self._writer is not None
        })
        return base_status
