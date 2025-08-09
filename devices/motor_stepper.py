import time
from typing import Dict, Any
from core.device_base import DeviceBase


class StepperMotor(DeviceBase):
    
    def __init__(self, id: str, params: Dict[str, Any]):
        super().__init__(id, params)
        self.port = params.get("port", "/dev/ttyUSB0")
        self.baudrate = params.get("baudrate", 115200)
        self.microstep = params.get("microstep", 16)
        self.steps_per_rev = params.get("steps_per_rev", 200)
        self.serial_conn = None
        self._started = False
        self._position = 0
        
    def start(self) -> None:
        try:
            import serial
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            
            if not self.serial_conn.is_open:
                raise RuntimeError(f"Не удалось открыть порт {self.port}")
                
            self._send_command("INIT")
            self._started = True
            
        except ImportError:
            self._started = True
        except Exception as e:
            if self.serial_conn:
                self.serial_conn.close()
                self.serial_conn = None
            raise RuntimeError(f"Ошибка запуска мотора: {e}")
            
    def stop(self) -> None:
        if self.serial_conn:
            try:
                self._send_command("STOP")
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None
        self._started = False
        
    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "started": self._started,
            "port": self.port,
            "baudrate": self.baudrate,
            "microstep": self.microstep,
            "position": self._position,
            "connected": self.serial_conn is not None and self.serial_conn.is_open if self.serial_conn else False
        }
        
    def send_command(self, command: str, **kwargs) -> Any:
        if not self._started:
            raise RuntimeError(f"Мотор {self.id} не запущен")
            
        if command == "home":
            return self.home()
        elif command == "move":
            steps = kwargs.get("steps", 0)
            return self.move(steps)
        elif command == "stop":
            return self.emergency_stop()
        elif command == "set_position":
            position = kwargs.get("position", 0)
            return self.set_position(position)
        elif command == "get_position":
            return self.get_position()
        else:
            raise ValueError(f"Неизвестная команда мотора: {command}")
            
    def home(self) -> Dict[str, Any]:
        try:
            self._send_command("HOME")
            time.sleep(2.0)
            self._position = 0
            
            return {
                "status": "homed",
                "position": self._position,
                "timestamp": time.time()
            }
            
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения HOME: {e}")
            
    def move(self, steps: int) -> Dict[str, Any]:
        try:
            cmd = f"MOVE {steps}"
            self._send_command(cmd)
            
            move_time = abs(steps) * 0.001  # 1ms на шаг
            time.sleep(move_time)
            
            self._position += steps
            
            return {
                "steps_moved": steps,
                "position": self._position,
                "move_time": move_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения MOVE: {e}")
            
    def emergency_stop(self) -> Dict[str, Any]:
        try:
            self._send_command("ESTOP")
            
            return {
                "status": "stopped",
                "position": self._position,
                "timestamp": time.time()
            }
            
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения STOP: {e}")
            
    def set_position(self, position: int) -> Dict[str, Any]:
        old_position = self._position
        self._position = position
        
        return {
            "old_position": old_position,
            "new_position": self._position,
            "timestamp": time.time()
        }
        
    def get_position(self) -> Dict[str, Any]:
        return {
            "position": self._position,
            "timestamp": time.time()
        }
        
    def _send_command(self, command: str) -> str:
        if self.serial_conn and self.serial_conn.is_open:
            try:
                cmd_bytes = (command + "\r\n").encode('utf-8')
                self.serial_conn.write(cmd_bytes)
                
                response = self.serial_conn.readline().decode('utf-8').strip()
                return response
                
            except Exception as e:
                raise RuntimeError(f"Ошибка serial команды '{command}': {e}")
        else:
            return f"OK:{command}"