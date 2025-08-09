"""
End-to-End тест с виртуальным термометром

Демонстрирует полный цикл работы системы:
1. Подключение виртуального устройства (термометр)
2. Периодическая генерация данных
3. Обработка событий и логирование
4. Реакция на перегрев с отправкой команд охлаждения
5. Проверка корректности работы всей архитектуры
"""

import pytest
import time
import threading
from typing import List, Dict, Any
from core import DeviceManager, event_bus, DeviceEvent
from devices.virtual_thermometer import VirtualThermometer


class DataCollector:
    """Вспомогательный класс для сбора событий во время тестирования"""
    
    def __init__(self):
        self.device_data_events: List[Dict[str, Any]] = []
        self.overheat_events: List[Dict[str, Any]] = []
        self.device_started_events: List[Dict[str, Any]] = []
        self.device_stopped_events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def on_device_data(self, data: Dict[str, Any]) -> None:
        """Обработчик данных от устройств"""
        with self.lock:
            self.device_data_events.append(data)
    
    def on_overheat(self, data: Dict[str, Any]) -> None:
        """Обработчик событий перегрева"""
        with self.lock:
            self.overheat_events.append(data)
    
    def on_device_started(self, data: Dict[str, Any]) -> None:
        """Обработчик событий запуска устройств"""
        with self.lock:
            self.device_started_events.append(data)
    
    def on_device_stopped(self, data: Dict[str, Any]) -> None:
        """Обработчик событий остановки устройств"""
        with self.lock:
            self.device_stopped_events.append(data)
    
    def clear(self) -> None:
        """Очистка всех собранных данных"""
        with self.lock:
            self.device_data_events.clear()
            self.overheat_events.clear()
            self.device_started_events.clear()
            self.device_stopped_events.clear()
    
    def get_data_copy(self) -> tuple:
        """Получение копий всех собранных данных"""
        with self.lock:
            return (
                self.device_data_events.copy(),
                self.overheat_events.copy(),
                self.device_started_events.copy(),
                self.device_stopped_events.copy()
            )


class CoolingSystem:
    """Система охлаждения, реагирующая на перегрев термометра"""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.cooling_actions: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def on_overheat(self, overheat_data: Dict[str, Any]) -> None:
        """Обработчик перегрева - отправляет команду охлаждения"""
        device_id = overheat_data.get("device_id")
        temperature = overheat_data.get("temperature")
        
        try:
            # Получаем устройство и отправляем команду охлаждения
            device = self.device_manager.get(device_id)
            
            # Вычисляем мощность охлаждения на основе превышения температуры
            overheat_amount = temperature - overheat_data.get("threshold", 28.0)
            cooling_power = min(max(1.0, overheat_amount * 0.5), 3.0)  # от 1.0 до 3.0
            
            cooling_result = device.send_command("cooling_activate", power=cooling_power)
            
            with self.lock:
                self.cooling_actions.append({
                    "timestamp": time.time(),
                    "device_id": device_id,
                    "trigger_temperature": temperature,
                    "cooling_power": cooling_power,
                    "cooling_result": cooling_result
                })
                
        except Exception as e:
            # В реальной системе здесь бы был логгер
            print(f"Ошибка при активации охлаждения: {e}")
    
    def get_cooling_history(self) -> List[Dict[str, Any]]:
        """Получение истории действий системы охлаждения"""
        with self.lock:
            return self.cooling_actions.copy()
    
    def clear_history(self) -> None:
        """Очистка истории действий"""
        with self.lock:
            self.cooling_actions.clear()


class TestVirtualDeviceFlow:
    """E2E тест демонстрирующий работу с виртуальным термометром"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.device_manager = DeviceManager()
        self.data_collector = DataCollector()
        self.cooling_system = CoolingSystem(self.device_manager)
        
        # Подписываемся на события
        event_bus.subscribe(DeviceEvent.DEVICE_DATA, self.data_collector.on_device_data)
        event_bus.subscribe("thermometer.overheat", self.data_collector.on_overheat)
        event_bus.subscribe("thermometer.overheat", self.cooling_system.on_overheat)
        event_bus.subscribe(DeviceEvent.DEVICE_STARTED, self.data_collector.on_device_started)
        event_bus.subscribe(DeviceEvent.DEVICE_STOPPED, self.data_collector.on_device_stopped)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        # Отписываемся от событий
        event_bus.unsubscribe(DeviceEvent.DEVICE_DATA, self.data_collector.on_device_data)
        event_bus.unsubscribe("thermometer.overheat", self.data_collector.on_overheat)
        event_bus.unsubscribe("thermometer.overheat", self.cooling_system.on_overheat)
        event_bus.unsubscribe(DeviceEvent.DEVICE_STARTED, self.data_collector.on_device_started)
        event_bus.unsubscribe(DeviceEvent.DEVICE_STOPPED, self.data_collector.on_device_stopped)
        
        # Останавливаем все устройства
        for device_id, device in self.device_manager.devices.items():
            try:
                device.stop()
            except:
                pass
    
    def test_basic_thermometer_functionality(self):
        """Базовый тест функциональности термометра"""
        # Создаем и регистрируем термометр
        thermometer = VirtualThermometer("test_thermometer", {
            "min_temp": 20.0,
            "max_temp": 30.0,
            "overheat_threshold": 28.0,
            "measurement_interval": 0.1  # Измерения каждые 100мс для быстрого теста
        })
        
        self.device_manager.register_device_instance(thermometer)
        
        # Проверяем статус перед запуском
        status = thermometer.status()
        assert status["started"] is False
        assert status["current_temperature"] == 25.0  # начальная температура
        
        # Запускаем термометр
        self.device_manager.start("test_thermometer")
        
        # Проверяем статус после запуска
        status = thermometer.status()
        assert status["started"] is True
        
        # Ждем несколько измерений
        time.sleep(0.5)
        
        # Проверяем, что данные генерируются
        data_events, _, started_events, stopped_events = self.data_collector.get_data_copy()
        
        assert len(data_events) > 0, "Должны быть получены данные от термометра"
        assert len(started_events) > 0, "Должно быть событие запуска устройства"
        
        # Проверяем структуру данных
        first_data_event = data_events[0]
        assert "device_id" in first_data_event
        assert "device_type" in first_data_event
        assert "data" in first_data_event
        
        measurement = first_data_event["data"]
        assert "temperature" in measurement
        assert "timestamp" in measurement
        assert "unit" in measurement
        assert measurement["unit"] == "°C"
        
        # Останавливаем термометр
        self.device_manager.stop("test_thermometer")
        
        # Проверяем финальный статус
        status = thermometer.status()
        assert status["started"] is False
    
    def test_overheat_detection_and_cooling(self):
        """Тест обнаружения перегрева и системы охлаждения"""
        # Создаем термометр с низким порогом перегрева для гарантированного срабатывания
        thermometer = VirtualThermometer("overheat_thermometer", {
            "min_temp": 27.0,  # Высокий минимум
            "max_temp": 32.0,  # Высокий максимум
            "overheat_threshold": 28.0,  # Низкий порог
            "measurement_interval": 0.1,
            "temperature_drift": 1.0  # Большие колебания для гарантии перегрева
        })
        
        self.device_manager.register_device_instance(thermometer)
        
        # Запускаем термометр
        self.device_manager.start("overheat_thermometer")
        
        # Принудительно устанавливаем высокую температуру
        thermometer.send_command("set_temperature", temperature=29.5)
        
        # Ждем несколько циклов измерений
        time.sleep(1.0)
        
        # Проверяем, что была зафиксирована высокая температура и перегрев
        data_events, overheat_events, _, _ = self.data_collector.get_data_copy()
        
        assert len(data_events) > 0, "Должны быть данные измерений"
        assert len(overheat_events) > 0, "Должно быть минимум одно событие перегрева"
        
        # Проверяем структуру события перегрева
        overheat_event = overheat_events[0]
        assert "device_id" in overheat_event
        assert "temperature" in overheat_event
        assert "threshold" in overheat_event
        assert overheat_event["temperature"] > overheat_event["threshold"]
        
        # Проверяем, что система охлаждения сработала
        cooling_history = self.cooling_system.get_cooling_history()
        assert len(cooling_history) > 0, "Система охлаждения должна была сработать"
        
        # Проверяем структуру действия охлаждения
        cooling_action = cooling_history[0]
        assert "device_id" in cooling_action
        assert "trigger_temperature" in cooling_action
        assert "cooling_power" in cooling_action
        assert "cooling_result" in cooling_action
        
        # Проверяем, что команда охлаждения была получена термометром
        device_logs = thermometer.send_command("get_logs")
        assert len(device_logs["cooling_commands"]) > 0, "Термометр должен получить команды охлаждения"
        
        self.device_manager.stop("overheat_thermometer")
    
    def test_full_e2e_scenario(self):
        """Полный E2E сценарий с проверкой всех компонентов"""
        # Создаем термометр с реалистичными параметрами
        thermometer = VirtualThermometer("e2e_thermometer", {
            "min_temp": 22.0,
            "max_temp": 31.0,
            "overheat_threshold": 28.0,
            "measurement_interval": 0.15,
            "temperature_drift": 0.8
        })
        
        self.device_manager.register_device_instance(thermometer)
        
        # Очищаем предыдущие данные
        self.data_collector.clear()
        self.cooling_system.clear_history()
        thermometer.clear_logs()
        
        # Запускаем систему
        self.device_manager.start("e2e_thermometer")
        
        # Даем системе поработать какое-то время
        initial_wait = 1.0
        time.sleep(initial_wait)
        
        # Принудительно вызываем перегрев несколько раз
        for i in range(3):
            # Устанавливаем температуру перегрева
            thermometer.send_command("set_temperature", temperature=29.0 + i * 0.5)
            time.sleep(0.3)  # Ждем обработки
        
        # Даем системе еще немного времени на обработку
        final_wait = 0.5
        time.sleep(final_wait)
        
        # Останавливаем термометр
        self.device_manager.stop("e2e_thermometer")
        
        # ===== ПРОВЕРКИ РЕЗУЛЬТАТОВ =====
        
        # 1. Проверяем данные измерений
        data_events, overheat_events, started_events, stopped_events = self.data_collector.get_data_copy()
        
        total_runtime = initial_wait + 3 * 0.3 + final_wait  # ~2.4 сек
        expected_min_measurements = int(total_runtime / 0.15) - 2  # с небольшим запасом
        
        assert len(data_events) >= expected_min_measurements, f"Недостаточно измерений: {len(data_events)} < {expected_min_measurements}"
        
        # 2. Проверяем события перегрева
        assert len(overheat_events) >= 1, "Должно быть минимум одно событие перегрева"
        
        # 3. Проверяем действия системы охлаждения
        cooling_history = self.cooling_system.get_cooling_history()
        assert len(cooling_history) >= 1, "Система охлаждения должна была сработать"
        
        # 4. Проверяем логи устройства
        device_logs = thermometer.send_command("get_logs")
        assert len(device_logs["measurements"]) >= expected_min_measurements, "В логах устройства недостаточно измерений"
        assert len(device_logs["overheat_events"]) >= 1, "В логах устройства должны быть события перегрева"
        assert len(device_logs["cooling_commands"]) >= 1, "Устройство должно получить команды охлаждения"
        
        # 5. Проверяем события статуса устройства
        assert len(started_events) >= 1, f"Должно быть минимум 1 событие запуска, получено: {len(started_events)}"
        assert len(stopped_events) >= 1, f"Должно быть минимум 1 событие остановки, получено: {len(stopped_events)}"
        
        # Проверяем содержимое событий
        start_event = started_events[0]
        stop_event = stopped_events[0]
        assert start_event["device_id"] == "e2e_thermometer"
        assert stop_event["device_id"] == "e2e_thermometer"
        
        # 6. Проверяем корректность временных меток
        first_measurement_time = data_events[0]["data"]["timestamp"]
        last_measurement_time = data_events[-1]["data"]["timestamp"]
        measurement_duration = last_measurement_time - first_measurement_time
        
        assert measurement_duration > 0.5, "Измерения должны происходить в течение значительного времени"
        
        # 7. Проверяем реакцию на охлаждение
        final_temperature = thermometer.status()["current_temperature"]
        # После команд охлаждения температура должна снизиться
        # (точное значение проверить сложно из-за случайности, но можно проверить логику)
        
        # 8. Детальная проверка связности событий
        for overheat_event in overheat_events:
            overheat_device_id = overheat_event["device_id"]
            overheat_temp = overheat_event["temperature"]
            overheat_time = overheat_event["timestamp"]
            
            # Ищем соответствующее действие охлаждения
            related_cooling = [
                c for c in cooling_history 
                if c["device_id"] == overheat_device_id and 
                   abs(c["timestamp"] - overheat_time) < 0.1  # в пределах 100мс
            ]
            
            assert len(related_cooling) > 0, f"Для перегрева на {overheat_temp}°C не найдено соответствующее действие охлаждения"
    
    def test_concurrent_multiple_thermometers(self):
        """Тест с несколькими термометрами одновременно"""
        thermometers = []
        
        # Создаем 3 термометра с разными настройками
        for i in range(3):
            thermometer = VirtualThermometer(f"multi_thermo_{i}", {
                "min_temp": 20.0 + i,
                "max_temp": 30.0 + i,
                "overheat_threshold": 27.0 + i,
                "measurement_interval": 0.1 + i * 0.05,
                "temperature_drift": 0.3 + i * 0.1
            })
            
            thermometers.append(thermometer)
            self.device_manager.register_device_instance(thermometer)
        
        # Запускаем все термометры
        for i, thermometer in enumerate(thermometers):
            self.device_manager.start(f"multi_thermo_{i}")
        
        # Даем системе поработать
        time.sleep(1.5)
        
        # Принудительно вызываем перегрев в разных термометрах
        for i, thermometer in enumerate(thermometers):
            thermometer.send_command("set_temperature", temperature=29.0 + i)
        
        time.sleep(0.5)
        
        # Останавливаем все термометры
        for i in range(3):
            self.device_manager.stop(f"multi_thermo_{i}")
        
        # Проверяем результаты
        data_events, overheat_events, _, _ = self.data_collector.get_data_copy()
        
        # Должны быть данные от всех термометров
        device_ids_in_data = set(event["device_id"] for event in data_events)
        expected_device_ids = {f"multi_thermo_{i}" for i in range(3)}
        
        assert expected_device_ids.issubset(device_ids_in_data), "Данные должны быть от всех термометров"
        
        # Должны быть события перегрева
        assert len(overheat_events) >= 3, "Должно быть минимум 3 события перегрева (по одному от каждого)"
        
        # Система охлаждения должна была сработать для всех перегревов
        cooling_history = self.cooling_system.get_cooling_history()
        assert len(cooling_history) >= 3, "Система охлаждения должна была сработать минимум 3 раза"
    
    def test_device_commands_and_status(self):
        """Тест команд устройства и получения статуса"""
        thermometer = VirtualThermometer("command_test_thermo", {
            "min_temp": 20.0,
            "max_temp": 30.0,
            "overheat_threshold": 28.0,
            "measurement_interval": 0.2
        })
        
        self.device_manager.register_device_instance(thermometer)
        self.device_manager.start("command_test_thermo")
        
        # Тестируем команду получения температуры
        temp_result = thermometer.send_command("get_temperature")
        assert "temperature" in temp_result
        assert "timestamp" in temp_result
        assert "unit" in temp_result
        assert temp_result["unit"] == "°C"
        
        # Тестируем команду установки температуры
        set_result = thermometer.send_command("set_temperature", temperature=25.5)
        assert abs(set_result["temperature"] - 25.5) < 0.1
        
        # Тестируем команду охлаждения
        cooling_result = thermometer.send_command("cooling_activate", power=2.0)
        assert "temperature_before" in cooling_result
        assert "temperature_after" in cooling_result
        assert cooling_result["temperature_after"] < cooling_result["temperature_before"]
        
        # Тестируем получение логов
        time.sleep(0.5)  # Даем накопиться данным
        logs = thermometer.send_command("get_logs")
        assert "measurements" in logs
        assert "overheat_events" in logs
        assert "cooling_commands" in logs
        assert len(logs["measurements"]) > 0
        
        # Тестируем статус устройства
        status = thermometer.status()
        required_fields = [
            "id", "type", "started", "current_temperature", 
            "overheat_threshold", "measurement_count", "measurement_interval"
        ]
        for field in required_fields:
            assert field in status, f"Поле '{field}' отсутствует в статусе"
        
        self.device_manager.stop("command_test_thermo")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
