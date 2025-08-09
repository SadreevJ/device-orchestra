import time
import logging
from typing import Dict, Any, List
from core.device_manager import DeviceManager


class DeviceTestResult:
    
    def __init__(self, device_id: str, test_name: str):
        self.device_id = device_id
        self.test_name = test_name
        self.start_time = time.time()
        self.success = False
        self.error_message = None
        self.details = {}
        self.duration = 0
        
    def finish(self, success: bool, error_message: str = None, **details):
        self.duration = time.time() - self.start_time
        self.success = success
        self.error_message = error_message
        self.details.update(details)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'test_name': self.test_name,
            'duration': self.duration,
            'success': self.success,
            'error_message': self.error_message,
            'details': self.details
        }


class DeviceTester:
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger("ucdf.device_tester")
        self.test_results: List[DeviceTestResult] = []
        
    def test_device(self, device_id: str) -> List[DeviceTestResult]:
        self.logger.info(f"Тестирование устройства: {device_id}")
        
        device_results = []
        
        try:
            device = self.device_manager.get(device_id)
            
            result = self._test_start_stop(device)
            device_results.append(result)
            self.test_results.append(result)
            
            result = self._test_status(device)
            device_results.append(result)
            self.test_results.append(result)
            
            if device.type == "OpenCVCamera":
                result = self._test_camera_commands(device)
                device_results.append(result)
                self.test_results.append(result)
            elif device.type == "StepperMotor":
                result = self._test_motor_commands(device)
                device_results.append(result)
                self.test_results.append(result)
            elif device.type == "FakeDevice":
                result = self._test_fake_device_commands(device)
                device_results.append(result)
                self.test_results.append(result)
                
        except Exception as e:
            result = DeviceTestResult(device_id, "general_error")
            result.finish(False, f"Общая ошибка: {str(e)}")
            device_results.append(result)
            self.test_results.append(result)
            
        success_count = sum(1 for r in device_results if r.success)
        total_count = len(device_results)
        
        self.logger.info(f"Тестирование {device_id}: {success_count}/{total_count} тестов прошли")
        return device_results
        
    def test_all_devices(self) -> Dict[str, List[DeviceTestResult]]:
        all_results = {}
        devices = self.device_manager.list()
        
        for device_info in devices:
            device_id = device_info["id"]
            results = self.test_device(device_id)
            all_results[device_id] = results
            
        return all_results
        
    def _test_start_stop(self, device) -> DeviceTestResult:
        result = DeviceTestResult(device.id, "start_stop")
        
        try:
            self.device_manager.start(device.id)
            status_after_start = device.status()
            
            self.device_manager.stop(device.id)
            status_after_stop = device.status()
            
            result.finish(True, details={
                'status_after_start': status_after_start,
                'status_after_stop': status_after_stop
            })
            
        except Exception as e:
            result.finish(False, f"Ошибка start/stop: {str(e)}")
            
        return result
        
    def _test_status(self, device) -> DeviceTestResult:
        result = DeviceTestResult(device.id, "status")
        
        try:
            status = device.status()
            
            if isinstance(status, dict) and "id" in status:
                result.finish(True, details={'status': status})
            else:
                result.finish(False, "Статус не содержит корректной информации")
                
        except Exception as e:
            result.finish(False, f"Ошибка получения статуса: {str(e)}")
            
        return result
        
    def _test_camera_commands(self, device) -> DeviceTestResult:
        result = DeviceTestResult(device.id, "camera_commands")
        
        try:
            self.device_manager.start(device.id)
            
            capture_result = device.send_command("capture")
            
            self.device_manager.stop(device.id)
            
            if capture_result and "timestamp" in capture_result:
                result.finish(True, details={'capture_result': capture_result})
            else:
                result.finish(False, "Команда capture не вернула ожидаемый результат")
                
        except Exception as e:
            result.finish(False, f"Ошибка команд камеры: {str(e)}")
            
        return result
        
    def _test_motor_commands(self, device) -> DeviceTestResult:
        result = DeviceTestResult(device.id, "motor_commands")
        
        try:
            self.device_manager.start(device.id)
            
            home_result = device.send_command("home")
            
            move_result = device.send_command("move", steps=10)
            
            self.device_manager.stop(device.id)
            
            if home_result and move_result:
                result.finish(True, details={
                    'home_result': home_result,
                    'move_result': move_result
                })
            else:
                result.finish(False, "Команды мотора не вернули ожидаемый результат")
                
        except Exception as e:
            result.finish(False, f"Ошибка команд мотора: {str(e)}")
            
        return result
        
    def _test_fake_device_commands(self, device) -> DeviceTestResult:
        result = DeviceTestResult(device.id, "fake_device_commands")
        
        try:
            self.device_manager.start(device.id)
            
            device_type = device.params.get("device_type", "generic")
            
            if device_type == "camera":
                test_result = device.send_command("capture")
            elif device_type == "motor":
                test_result = device.send_command("move", steps=5)
            else:
                test_result = device.send_command("ping")
                
            self.device_manager.stop(device.id)
            
            if test_result:
                result.finish(True, details={'test_result': test_result})
            else:
                result.finish(False, "Команда не вернула результат")
                
        except Exception as e:
            result.finish(False, f"Ошибка команд фейкового устройства: {str(e)}")
            
        return result
        
    def generate_report(self) -> Dict[str, Any]:
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'results': [r.to_dict() for r in self.test_results]
        }