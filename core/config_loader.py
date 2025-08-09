import json
import os
from typing import Dict, Any, List
import logging


class ConfigLoader:
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger("ucdf.config_loader")
        
    def load_devices_config(self, filename: str = "devices.json") -> List[Dict[str, Any]]:
        try:
            config_path = os.path.join(self.config_dir, filename)
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            devices = []
            if isinstance(data, dict):
                for device_id, device_config in data.items():
                    device = {
                        "id": device_id,
                        "type": device_config.get("type", ""),
                        "params": {k: v for k, v in device_config.items() if k not in ["type"]}
                    }
                    devices.append(device)
            elif isinstance(data, list):
                devices = data
                
            self.logger.info(f"Загружена конфигурация: {len(devices)} устройств")
            return devices
            
        except FileNotFoundError:
            self.logger.error(f"Файл конфигурации не найден: {config_path}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка формата JSON в {config_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            return []
