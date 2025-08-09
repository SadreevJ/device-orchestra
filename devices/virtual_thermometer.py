import time
import random
import threading
from typing import Dict, Any, List, Callable
from core.device_base import DeviceBase
from core.events import event_bus, DeviceEvent


class VirtualThermometer(DeviceBase):
    """
    Виртуальный термометр для демонстрации E2E работы системы.
    
    Периодически генерирует температурные данные в диапазоне 20-30°C
    и отправляет события через event_bus. При температуре > 28°C
    генерирует событие перегрева.
    """

    def __init__(self, id: str, params: Dict[str, Any]):
        super().__init__(id, params)
        
        # Настройки термометра
        self.min_temp = params.get("min_temp", 20.0)
        self.max_temp = params.get("max_temp", 30.0) 
        self.overheat_threshold = params.get("overheat_threshold", 28.0)
        self.measurement_interval = params.get("measurement_interval", 1.0)  # секунды
        self.temperature_drift = params.get("temperature_drift", 0.5)  # максимальное изменение за раз
        
        # Внутреннее состояние
        self._started = False
        self._current_temperature = (self.min_temp + self.max_temp) / 2  # стартуем с средней температуры
        self._measurement_thread = None
        self._stop_event = threading.Event()
        self._measurement_count = 0
        
        # Логи для тестирования
        self.measurement_log: List[Dict[str, Any]] = []
        self.overheat_events: List[Dict[str, Any]] = []
        self.cooling_commands: List[Dict[str, Any]] = []

    def start(self) -> None:
        """Запуск термометра и начало измерений"""
        if self._started:
            return
            
        self._started = True
        self._stop_event.clear()
        
        # Запускаем поток для периодических измерений
        self._measurement_thread = threading.Thread(target=self._measurement_loop, daemon=True)
        self._measurement_thread.start()
        
        # Уведомляем о запуске устройства
        event_bus.emit(DeviceEvent.DEVICE_STARTED, {
            "device_id": self.id,
            "device_type": "VirtualThermometer",
            "timestamp": time.time()
        })

    def stop(self) -> None:
        """Остановка термометра"""
        if not self._started:
            return
            
        self._started = False
        self._stop_event.set()
        
        if self._measurement_thread and self._measurement_thread.is_alive():
            self._measurement_thread.join(timeout=2.0)
        
        # Уведомляем об остановке устройства
        event_bus.emit(DeviceEvent.DEVICE_STOPPED, {
            "device_id": self.id,
            "device_type": "VirtualThermometer", 
            "timestamp": time.time()
        })

    def status(self) -> Dict[str, Any]:
        """Получение текущего статуса термометра"""
        return {
            "id": self.id,
            "type": self.type,
            "started": self._started,
            "current_temperature": round(self._current_temperature, 2),
            "overheat_threshold": self.overheat_threshold,
            "measurement_count": self._measurement_count,
            "measurement_interval": self.measurement_interval,
            "temperature_range": [self.min_temp, self.max_temp],
            "recent_measurements": len(self.measurement_log),
            "overheat_events_count": len(self.overheat_events),
            "cooling_commands_count": len(self.cooling_commands)
        }

    def send_command(self, command: str, **kwargs) -> Any:
        """Обработка команд, отправляемых термометру"""
        # Некоторые команды доступны и для остановленного устройства
        if not self._started and command not in ["get_logs", "get_temperature"]:
            raise RuntimeError(f"Термометр {self.id} не запущен")

        if command == "get_temperature":
            # Возвращаем текущую температуру
            return {
                "temperature": round(self._current_temperature, 2),
                "timestamp": time.time(),
                "unit": "°C",
                "device_id": self.id
            }
            
        elif command == "cooling_activate":
            # Команда охлаждения - снижаем температуру
            cooling_power = kwargs.get("power", 2.0)
            self._current_temperature = max(
                self.min_temp, 
                self._current_temperature - cooling_power
            )
            
            cooling_command = {
                "command": "cooling_activate",
                "power": cooling_power,
                "temperature_before": self._current_temperature + cooling_power,
                "temperature_after": self._current_temperature,
                "timestamp": time.time()
            }
            
            self.cooling_commands.append(cooling_command)
            
            return cooling_command
            
        elif command == "get_logs":
            # Возвращаем логи для анализа в тестах
            return {
                "measurements": self.measurement_log.copy(),
                "overheat_events": self.overheat_events.copy(),
                "cooling_commands": self.cooling_commands.copy()
            }
            
        elif command == "set_temperature":
            # Ручная установка температуры (для тестирования)
            new_temp = kwargs.get("temperature", self._current_temperature)
            self._current_temperature = max(self.min_temp, min(self.max_temp, new_temp))
            return {
                "temperature": self._current_temperature,
                "timestamp": time.time()
            }
            
        else:
            raise ValueError(f"Неизвестная команда термометра: {command}")

    def _measurement_loop(self) -> None:
        """Основной цикл измерений температуры"""
        while not self._stop_event.is_set():
            try:
                # Генерируем новое измерение
                measurement = self._generate_measurement()
                
                # Сохраняем в лог
                self.measurement_log.append(measurement)
                
                # Отправляем событие с данными
                event_bus.emit(DeviceEvent.DEVICE_DATA, {
                    "device_id": self.id,
                    "device_type": "VirtualThermometer",
                    "data": measurement
                })
                
                # Проверяем перегрев
                if measurement["temperature"] > self.overheat_threshold:
                    overheat_event = {
                        "device_id": self.id,
                        "temperature": measurement["temperature"],
                        "threshold": self.overheat_threshold,
                        "timestamp": measurement["timestamp"],
                        "measurement_id": measurement["measurement_id"]
                    }
                    
                    self.overheat_events.append(overheat_event)
                    
                    # Отправляем событие перегрева
                    event_bus.emit("thermometer.overheat", overheat_event)
                
                # Ждем до следующего измерения
                self._stop_event.wait(self.measurement_interval)
                
            except Exception as e:
                # Отправляем событие об ошибке
                event_bus.emit(DeviceEvent.DEVICE_ERROR, {
                    "device_id": self.id,
                    "error": str(e),
                    "timestamp": time.time()
                })
                break

    def _generate_measurement(self) -> Dict[str, Any]:
        """Генерация одного измерения температуры"""
        self._measurement_count += 1
        
        # Случайное изменение температуры в пределах drift
        temperature_change = random.uniform(-self.temperature_drift, self.temperature_drift)
        self._current_temperature += temperature_change
        
        # Ограничиваем температуру заданными рамками
        self._current_temperature = max(self.min_temp, min(self.max_temp, self._current_temperature))
        
        # Иногда делаем резкие скачки для имитации реальных условий
        if random.random() < 0.1:  # 10% вероятность
            spike = random.uniform(-1.5, 2.0)
            self._current_temperature = max(self.min_temp, min(self.max_temp, self._current_temperature + spike))
        
        return {
            "measurement_id": self._measurement_count,
            "temperature": round(self._current_temperature, 2),
            "timestamp": time.time(),
            "unit": "°C",
            "device_id": self.id
        }

    def get_measurement_history(self) -> List[Dict[str, Any]]:
        """Получение истории измерений для анализа"""
        return self.measurement_log.copy()

    def get_overheat_history(self) -> List[Dict[str, Any]]:
        """Получение истории событий перегрева"""
        return self.overheat_events.copy()

    def get_cooling_history(self) -> List[Dict[str, Any]]:
        """Получение истории команд охлаждения"""
        return self.cooling_commands.copy()

    def clear_logs(self) -> None:
        """Очистка всех логов (полезно для тестов)"""
        self.measurement_log.clear()
        self.overheat_events.clear() 
        self.cooling_commands.clear()
        self._measurement_count = 0
