import time
from typing import Dict, Any, Optional, Union
import logging


class SerialAdapter:

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.is_connected = False
        self.logger = logging.getLogger(f"device-orchestra.serial.{port}")

    def connect(self) -> bool:
        try:
            import serial

            self.connection = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)

            if self.connection.is_open:
                self.is_connected = True
                self.logger.info(f"Подключен к {self.port} ({self.baudrate} baud)")
                return True
            else:
                return False

        except ImportError:
            self.is_connected = True
            self.logger.info(f"Эмуляция подключения к {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения к {self.port}: {e}")
            return False

    def disconnect(self) -> bool:
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
            self.connection = None
            self.is_connected = False
            self.logger.info(f"Отключен от {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отключения от {self.port}: {e}")
            return False

    def send_data(self, data: Union[str, bytes]) -> bool:
        if not self.is_connected:
            raise RuntimeError("Порт не подключен")

        try:
            if self.connection:
                if isinstance(data, str):
                    data = data.encode("utf-8")
                self.connection.write(data)
                return True
            else:
                self.logger.debug(f"Эмуляция отправки: {data}")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки данных: {e}")
            return False

    def read_data(self, size: int = 1) -> Optional[bytes]:
        if not self.is_connected:
            raise RuntimeError("Порт не подключен")

        try:
            if self.connection:
                data = self.connection.read(size)
                return data if data else None
            else:
                return b"OK\r\n"
        except Exception as e:
            self.logger.error(f"Ошибка чтения данных: {e}")
            return None

    def send_command(self, command: str, wait_response: bool = True) -> Optional[str]:
        try:
            cmd_with_ending = command + "\r\n"
            success = self.send_data(cmd_with_ending)
            if not success:
                return None

            if wait_response:
                if self.connection:
                    response = self.connection.readline().decode("utf-8").strip()
                    return response
                else:
                    return f"OK:{command}"

            return "OK"

        except Exception as e:
            self.logger.error(f"Ошибка команды '{command}': {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "connected": self.is_connected,
            "timeout": self.timeout,
        }
