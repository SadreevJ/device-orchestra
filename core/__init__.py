from .device_base import DeviceBase
from .device_manager import DeviceManager
from .device_factory import device_factory
from .config_loader import ConfigLoader
from .events import event_bus, EventBus, DeviceEvent
from .logger import get_logger


def register_default_devices():
    from devices.camera_opencv import OpenCVCamera
    from devices.motor_stepper import StepperMotor
    from debug_tools.fake_device import FakeDevice
    
    device_factory.register("OpenCVCamera", OpenCVCamera)
    device_factory.register("StepperMotor", StepperMotor)
    device_factory.register("FakeDevice", FakeDevice)


register_default_devices()

__all__ = [
    'DeviceBase',
    'DeviceManager', 
    'device_factory',
    'ConfigLoader',
    'event_bus',
    'EventBus',
    'DeviceEvent',
    'get_logger'
]