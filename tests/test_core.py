import pytest
import tempfile
import json
import os
from core import DeviceManager, device_factory, ConfigLoader
from debug_tools.fake_device import FakeDevice


class TestConfigLoader:
    
    def test_load_devices_config(self):
        test_config = [
            {
                "id": "test_device",
                "type": "FakeDevice",
                "params": {"device_type": "camera"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "devices.json")
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
                
            loader = ConfigLoader(temp_dir)
            devices = loader.load_devices_config()
            
            assert len(devices) == 1
            assert devices[0]["id"] == "test_device"
            assert devices[0]["type"] == "FakeDevice"
            
    def test_load_nonexistent_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = ConfigLoader(temp_dir)
            devices = loader.load_devices_config()
            
            assert devices == []


class TestDeviceFactory:
    
    def test_register_and_create(self):
        device = device_factory.create("FakeDevice", "test_id", {"device_type": "camera"})
        
        assert device is not None
        assert device.id == "test_id"
        assert device.type == "FakeDevice"
        
    def test_create_unknown_type(self):
        with pytest.raises(ValueError):
            device_factory.create("UnknownDevice", "test_id", {})
            
    def test_get_registered_types(self):
        types = device_factory.get_registered_types()
        assert "FakeDevice" in types


class TestDeviceManager:
    
    def setup_method(self):
        self.manager = DeviceManager()
        
        test_config = [
            {
                "id": "fake_cam",
                "type": "FakeDevice", 
                "params": {"device_type": "camera"}
            },
            {
                "id": "fake_motor",
                "type": "FakeDevice",
                "params": {"device_type": "motor"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "devices.json")
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
                
            self.manager.load_config(temp_dir)
        
    def test_load_config(self):
        devices = self.manager.list()
        assert len(devices) == 2
        
        device_ids = [d["id"] for d in devices]
        assert "fake_cam" in device_ids
        assert "fake_motor" in device_ids
        
    def test_get_device(self):
        device = self.manager.get("fake_cam")
        assert device.id == "fake_cam"
        assert device.type == "FakeDevice"
        
    def test_get_nonexistent_device(self):
        with pytest.raises(ValueError):
            self.manager.get("nonexistent")
            
    def test_start_stop_device(self):
        device_id = "fake_cam"
        
        self.manager.start(device_id)
        device = self.manager.get(device_id)
        status = device.status()
        assert status["started"] is True
        
        self.manager.stop(device_id)
        status = device.status()
        assert status["started"] is False
        
    def test_register_device_instance(self):
        device = FakeDevice("manual_device", {"device_type": "sensor"})
        self.manager.register_device_instance(device)
        
        retrieved = self.manager.get("manual_device")
        assert retrieved.id == "manual_device"


class TestFakeDevice:
    
    def setup_method(self):
        self.device = FakeDevice("test_fake", {
            "device_type": "camera",
            "simulation_mode": "normal",
            "base_delay": 0.01,
            "error_probability": 0.0
        })
        
    def test_start_stop(self):
        assert not self.device._started
        
        self.device.start()
        assert self.device._started
        
        self.device.stop()
        assert not self.device._started
        
    def test_status(self):
        status = self.device.status()
        
        assert status["id"] == "test_fake"
        assert status["type"] == "FakeDevice"
        assert status["device_type"] == "camera"
        assert "started" in status
        
    def test_camera_commands(self):
        self.device.start()
        
        result = self.device.send_command("capture")
        assert "image_id" in result
        assert "timestamp" in result
        
        frame = self.device.send_command("get_frame")
        assert frame is not None
        
        self.device.stop()
        
    def test_motor_commands(self):
        motor_device = FakeDevice("test_motor", {
            "device_type": "motor",
            "base_delay": 0.01,
            "error_probability": 0.0
        })
        
        motor_device.start()
        
        result = motor_device.send_command("move", steps=10)
        assert "steps_moved" in result
        assert result["steps_moved"] == 10
        
        result = motor_device.send_command("home")
        assert result["status"] == "homed"
        
        motor_device.stop()
        
    def test_command_without_start(self):
        with pytest.raises(RuntimeError):
            self.device.send_command("capture")
            
    def test_error_simulation(self):
        error_device = FakeDevice("error_device", {
            "device_type": "camera",
            "base_delay": 0.01,
            "error_probability": 1.0
        })
        
        with pytest.raises(RuntimeError):
            error_device.start()


if __name__ == "__main__":
    pytest.main([__file__])
