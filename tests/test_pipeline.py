import pytest
import tempfile
import json
import os
from core import DeviceManager
from runners.pipeline_runner import PipelineRunner


class TestPipelineRunner:

    def setup_method(self):
        self.manager = DeviceManager()

        test_config = [
            {
                "id": "test_cam",
                "type": "FakeDevice",
                "params": {
                    "device_type": "camera",
                    "simulation_mode": "normal",
                    "base_delay": 0.01,
                    "error_probability": 0.0,
                },
            },
            {
                "id": "test_motor",
                "type": "FakeDevice",
                "params": {
                    "device_type": "motor",
                    "simulation_mode": "normal",
                    "base_delay": 0.01,
                    "error_probability": 0.0,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "devices.json")
            with open(config_file, "w") as f:
                json.dump(test_config, f)

            self.manager.load_config(temp_dir)

        self.runner = PipelineRunner(self.manager)

    def test_simple_pipeline(self):
        pipeline = [
            {"step": "init", "device": "test_motor", "action": "home"},
            {"step": "capture", "device": "test_cam", "action": "capture"},
            {"step": "wait", "duration": 0.1},
        ]

        self.manager.start("test_motor")
        self.manager.start("test_cam")

        try:
            result = self.runner.run_pipeline(pipeline)

            assert result["total_steps"] == 3
            assert result["executed_steps"] == 3
            assert result["successful_steps"] == 3
            assert result["failed_steps"] == 0
            assert len(result["results"]) == 3

            for step_result in result["results"]:
                assert step_result["status"] == "success"

        finally:
            self.manager.stop("fake_motor")
            self.manager.stop("fake_cam")

    def test_pipeline_with_error(self):
        pipeline = [{"step": "capture", "device": "nonexistent_device", "action": "capture"}]

        result = self.runner.run_pipeline(pipeline)

        assert result["total_steps"] == 1
        assert result["executed_steps"] == 1
        assert result["successful_steps"] == 0
        assert result["failed_steps"] == 1
        assert len(result["errors"]) == 1

    def test_dry_run_mode(self):
        pipeline = [{"step": "capture", "device": "test_cam", "action": "capture"}]

        self.runner.set_dry_run(True)
        result = self.runner.run_pipeline(pipeline)

        assert result["dry_run"] is True
        assert result["successful_steps"] == 1

        step_result = result["results"][0]["result"]
        assert step_result["dry_run"] is True
        assert step_result["simulated"] is True

    def test_pipeline_validation(self):
        valid_pipeline = [{"step": "capture", "device": "test_cam", "action": "capture"}]

        errors = self.runner.validate_pipeline(valid_pipeline)
        assert len(errors) == 0

        invalid_pipeline = [{"device": "test_cam", "action": "capture"}]

        errors = self.runner.validate_pipeline(invalid_pipeline)
        assert len(errors) > 0
        assert "отсутствует поле 'step'" in errors[0]

        invalid_pipeline2 = [{"step": "capture", "device": "nonexistent", "action": "capture"}]

        errors = self.runner.validate_pipeline(invalid_pipeline2)
        assert len(errors) > 0
        assert "не найдено" in errors[0]

    def test_pipeline_from_file(self):
        pipeline = [{"step": "capture", "device": "test_cam", "action": "capture"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pipeline, f)
            pipeline_file = f.name

        try:
            self.manager.start("test_cam")

            result = self.runner.run_pipeline_from_file(pipeline_file)

            assert result["successful_steps"] == 1

        finally:
            self.manager.stop("test_cam")
            os.unlink(pipeline_file)

    def test_complex_pipeline(self):
        pipeline = [
            {"step": "init", "device": "test_motor", "action": "home"},
            {"step": "capture", "device": "test_cam", "action": "capture"},
            {
                "step": "move",
                "device": "test_motor",
                "action": "move",
                "args": {"steps": 10},
            },
            {"step": "wait", "duration": 0.05},
            {"step": "custom_command", "device": "test_cam", "action": "get_frame"},
        ]

        self.manager.start("test_motor")
        self.manager.start("test_cam")

        try:
            result = self.runner.run_pipeline(pipeline)

            assert result["total_steps"] == 5
            assert result["successful_steps"] == 5
            assert result["failed_steps"] == 0

            results = result["results"]

            assert results[0]["step_type"] == "init"
            assert "home" in str(results[0]["result"])

            assert results[1]["step_type"] == "capture"
            assert "image_id" in str(results[1]["result"])

            assert results[2]["step_type"] == "move"
            assert "steps_moved" in str(results[2]["result"])

            assert results[3]["step_type"] == "wait"
            assert "waited" in str(results[3]["result"])

            assert results[4]["step_type"] == "custom_command"

        finally:
            self.manager.stop("test_motor")
            self.manager.stop("test_cam")

    def test_pipeline_timing(self):
        pipeline = [{"step": "wait", "duration": 0.1}]

        result = self.runner.run_pipeline(pipeline)

        assert result["total_duration"] > 0.05
        assert result["results"][0]["duration"] > 0.05

    def test_save_step(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            save_file = f.name

        try:
            pipeline = [{"step": "save", "filepath": save_file, "data": "test data"}]

            result = self.runner.run_pipeline(pipeline)

            assert result["successful_steps"] == 1

            assert os.path.exists(save_file)

            with open(save_file, "r") as f:
                content = f.read()
                assert content == "test data"

        finally:
            if os.path.exists(save_file):
                os.unlink(save_file)


if __name__ == "__main__":
    pytest.main([__file__])
