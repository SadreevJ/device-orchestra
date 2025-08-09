import psutil
import time
import threading
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class PerformanceMetric:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    device_id: Optional[str] = None
    operation: Optional[str] = None


class PerformanceMonitor:
    
    def __init__(self, max_history: int = 1000, sample_interval: float = 1.0):
        self.max_history = max_history
        self.sample_interval = sample_interval
        self.logger = logging.getLogger("ucdf.perf_monitor")
        
        self.metrics_history: deque = deque(maxlen=max_history)
        self.device_metrics: Dict[str, deque] = {}
        
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def start_monitoring(self) -> bool:
        if self.monitoring:
            return False
            
        try:
            self.monitoring = True
            self.stop_event.clear()
            
            self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info(f"Мониторинг производительности запущен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска мониторинга: {e}")
            self.monitoring = False
            return False
            
    def stop_monitoring(self) -> bool:
        if not self.monitoring:
            return False
            
        try:
            self.monitoring = False
            self.stop_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5.0)
                
            self.logger.info("Мониторинг производительности остановлен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки мониторинга: {e}")
            return False
            
    def _monitor_worker(self):
        while self.monitoring and not self.stop_event.is_set():
            try:
                metric = self._collect_metrics()
                
                self.metrics_history.append(metric)
                
            except Exception as e:
                if self.monitoring:
                    self.logger.error(f"Ошибка сбора метрик: {e}")
                    
            if self.stop_event.wait(self.sample_interval):
                break
                
    def _collect_metrics(self) -> PerformanceMetric:
        current_time = time.time()
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        return PerformanceMetric(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb
        )
        
    def record_device_operation(self, device_id: str, operation: str):
        try:
            metric = self._collect_metrics()
            metric.device_id = device_id
            metric.operation = operation
            
            if device_id not in self.device_metrics:
                self.device_metrics[device_id] = deque(maxlen=self.max_history)
                
            self.device_metrics[device_id].append(metric)
            
        except Exception as e:
            self.logger.error(f"Ошибка записи метрики устройства: {e}")
            
    def get_current_metrics(self) -> Optional[PerformanceMetric]:
        try:
            return self._collect_metrics()
        except Exception as e:
            self.logger.error(f"Ошибка получения текущих метрик: {e}")
            return None
            
    def get_metrics_history(self, device_id: str = None) -> List[PerformanceMetric]:
        if device_id:
            return list(self.device_metrics.get(device_id, []))
        else:
            return list(self.metrics_history)
            
    def get_average_metrics(self, device_id: str = None, 
                           last_minutes: int = 5) -> Dict[str, float]:
        cutoff_time = time.time() - (last_minutes * 60)
        
        if device_id:
            metrics = [m for m in self.device_metrics.get(device_id, []) 
                      if m.timestamp > cutoff_time]
        else:
            metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
        if not metrics:
            return {}
            
        return {
            'cpu_percent': sum(m.cpu_percent for m in metrics) / len(metrics),
            'memory_percent': sum(m.memory_percent for m in metrics) / len(metrics),
            'memory_used_mb': sum(m.memory_used_mb for m in metrics) / len(metrics),
            'sample_count': len(metrics),
            'time_period_minutes': last_minutes
        }
        
    def get_system_info(self) -> Dict[str, Any]:
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            
            return {
                'cpu_count': cpu_count,
                'memory_total_gb': memory.total / (1024**3),
                'memory_available_gb': memory.available / (1024**3)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о системе: {e}")
            return {}
            
    def clear_history(self, device_id: str = None):
        if device_id:
            if device_id in self.device_metrics:
                self.device_metrics[device_id].clear()
        else:
            self.metrics_history.clear()
            self.device_metrics.clear()
            
    def get_stats(self) -> Dict[str, Any]:
        return {
            'monitoring': self.monitoring,
            'sample_interval': self.sample_interval,
            'max_history': self.max_history,
            'total_metrics': len(self.metrics_history),
            'device_metrics_count': {device_id: len(metrics) 
                                   for device_id, metrics in self.device_metrics.items()}
        }