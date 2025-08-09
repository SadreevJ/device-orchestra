import json
import time
import logging
from typing import Dict, Any, List
from core.device_manager import DeviceManager


class PipelineRunner:
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger("ucdf.pipeline_runner")
        self.replay_mode = False
        self.dry_run = False
        self.parallel = False
        
    def load_pipeline(self, pipeline_path: str) -> List[Dict[str, Any]]:
        try:
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                pipeline = json.load(f)
            self.logger.info(f"Загружен пайплайн: {pipeline_path}, шагов: {len(pipeline)}")
            return pipeline
        except Exception as e:
            self.logger.error(f"Ошибка загрузки пайплайна {pipeline_path}: {e}")
            raise
            
    def run_pipeline(self, pipeline: List[Dict[str, Any]]) -> Dict[str, Any]:

        start_time = time.time()
        results = []
        errors = []
        
        self.logger.info(f"Начало выполнения пайплайна, шагов: {len(pipeline)}")
        
        for i, step in enumerate(pipeline):
            step_start_time = time.time()
            
            try:
                self.logger.info(f"Шаг {i+1}/{len(pipeline)}: {step.get('step', 'unknown')}")
                
                if self.dry_run:
                    result = self._dry_run_step(step)
                else:
                    result = self._execute_step(step)
                    
                step_duration = time.time() - step_start_time
                step_result = {
                    "step_index": i + 1,
                    "step_type": step.get("step", "unknown"),
                    "duration": step_duration,
                    "result": result,
                    "status": "success"
                }
                results.append(step_result)
                
                self.logger.info(f"Шаг {i+1} выполнен за {step_duration:.3f}с")
                
            except Exception as e:
                step_duration = time.time() - step_start_time
                error_info = {
                    "step_index": i + 1,
                    "step_type": step.get("step", "unknown"),
                    "duration": step_duration,
                    "error": str(e),
                    "status": "error"
                }
                errors.append(error_info)
                results.append(error_info)
                
                self.logger.error(f"Ошибка на шаге {i+1}: {e}")
                
                break
                
        total_duration = time.time() - start_time
        
        pipeline_result = {
            "total_steps": len(pipeline),
            "executed_steps": len(results),
            "successful_steps": len([r for r in results if r.get("status") == "success"]),
            "failed_steps": len(errors),
            "total_duration": total_duration,
            "results": results,
            "errors": errors,
            "dry_run": self.dry_run,
            "replay_mode": self.replay_mode
        }
        
        self.logger.info(f"Пайплайн завершен за {total_duration:.3f}с, "
                        f"успешно: {pipeline_result['successful_steps']}/{len(pipeline)}")
        
        return pipeline_result
        
    def run_pipeline_from_file(self, pipeline_path: str) -> Dict[str, Any]:
        pipeline = self.load_pipeline(pipeline_path)
        return self.run_pipeline(pipeline)
        
    def _execute_step(self, step: Dict[str, Any]) -> Any:
        step_type = step.get("step")
        
        if step_type == "capture":
            return self._execute_capture_step(step)
        elif step_type == "move":
            return self._execute_move_step(step)
        elif step_type == "init":
            return self._execute_init_step(step)
        elif step_type == "wait":
            return self._execute_wait_step(step)
        elif step_type == "custom_command":
            return self._execute_custom_command_step(step)
        elif step_type == "save":
            return self._execute_save_step(step)
        else:
            raise ValueError(f"Неизвестный тип шага: {step_type}")
            
    def _execute_capture_step(self, step: Dict[str, Any]) -> Any:
        device_id = step.get("device")
        action = step.get("action", "capture")
        save_to = step.get("save_to")
        
        device = self.device_manager.get(device_id)
        
        kwargs = {}
        if save_to:
            kwargs["save_to"] = save_to
            
        return device.send_command(action, **kwargs)
        
    def _execute_move_step(self, step: Dict[str, Any]) -> Any:
        device_id = step.get("device")
        action = step.get("action", "move")
        args = step.get("args", {})
        
        device = self.device_manager.get(device_id)
        return device.send_command(action, **args)
        
    def _execute_init_step(self, step: Dict[str, Any]) -> Any:
        device_id = step.get("device")
        action = step.get("action", "home")
        
        device = self.device_manager.get(device_id)
        return device.send_command(action)
        
    def _execute_wait_step(self, step: Dict[str, Any]) -> Any:
        duration = step.get("duration", 1.0)
        time.sleep(duration)
        return {"waited": duration, "timestamp": time.time()}
        
    def _execute_custom_command_step(self, step: Dict[str, Any]) -> Any:
        device_id = step.get("device")
        action = step.get("action")
        args = step.get("args", {})
        
        device = self.device_manager.get(device_id)
        return device.send_command(action, **args)
        
    def _execute_save_step(self, step: Dict[str, Any]) -> Any:
        filepath = step.get("filepath")
        data = step.get("data", "")
        
        if not filepath:
            raise ValueError("Не указан путь для сохранения")
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, dict) or isinstance(data, list):
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(data))
                    
            return {"saved": True, "filepath": filepath, "timestamp": time.time()}
        except Exception as e:
            raise RuntimeError(f"Ошибка сохранения файла {filepath}: {e}")
            
    def _dry_run_step(self, step: Dict[str, Any]) -> Any:
        step_type = step.get("step")
        device_id = step.get("device", "N/A")
        action = step.get("action", "N/A")
        
        return {
            "dry_run": True,
            "step_type": step_type,
            "device": device_id,
            "action": action,
            "simulated": True,
            "timestamp": time.time()
        }
        
    def set_dry_run(self, enabled: bool) -> None:
        self.dry_run = enabled
        self.logger.info(f"Режим dry run: {'включен' if enabled else 'выключен'}")
        
    def set_replay_mode(self, enabled: bool) -> None:
        self.replay_mode = enabled
        self.logger.info(f"Режим replay: {'включен' if enabled else 'выключен'}")
        
    def validate_pipeline(self, pipeline: List[Dict[str, Any]]) -> List[str]:
        errors = []
        
        for i, step in enumerate(pipeline):
            step_errors = self._validate_step(i + 1, step)
            errors.extend(step_errors)
            
        return errors
        
    def _validate_step(self, step_num: int, step: Dict[str, Any]) -> List[str]:
        errors = []
        
        if "step" not in step:
            errors.append(f"Шаг {step_num}: отсутствует поле 'step'")
            return errors
            
        step_type = step["step"]
        
        if step_type in ["capture", "move", "init", "custom_command"]:
            if "device" not in step:
                errors.append(f"Шаг {step_num}: отсутствует поле 'device' для типа '{step_type}'")
            else:
                device_id = step["device"]
                try:
                    self.device_manager.get(device_id)
                except ValueError:
                    errors.append(f"Шаг {step_num}: устройство '{device_id}' не найдено")
                    
        elif step_type == "wait":
            if "duration" not in step:
                errors.append(f"Шаг {step_num}: отсутствует поле 'duration' для типа 'wait'")
            elif not isinstance(step["duration"], (int, float)):
                errors.append(f"Шаг {step_num}: поле 'duration' должно быть числом")
                
        elif step_type == "save":
            if "filepath" not in step:
                errors.append(f"Шаг {step_num}: отсутствует поле 'filepath' для типа 'save'")
                
        return errors
