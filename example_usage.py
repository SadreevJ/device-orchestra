import os
import sys
from core import DeviceManager, get_logger
from runners.pipeline_runner import PipelineRunner
from debug_tools.device_tester import DeviceTester


def main():
    logger = get_logger("example")

    print("=" * 60)
    print("UCDF - Universal Device Control & Debug Framework")
    print("Демонстрация основных возможностей")
    print("=" * 60)

    print("\n1. Инициализация менеджера устройств...")
    manager = DeviceManager()
    manager.load_config("config")

    print("\n2. Список загруженных устройств:")
    devices = manager.list()
    for device in devices:
        print(f"  - {device['id']} ({device['type']})")

    if not devices:
        print("  Устройства не найдены. Проверьте config/devices.json")
        return

    print("\n3. Тестирование устройств...")
    tester = DeviceTester(manager)

    for device in devices:
        device_id = device["id"]
        print(f"\nТестирование {device_id}:")

        try:
            results = tester.test_device(device_id)
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)

            print(f"  Результат: {success_count}/{total_count} тестов прошли")

            for result in results:
                status = "✓" if result.success else "✗"
                print(f"    {status} {result.test_name} ({result.duration:.3f}s)")
                if not result.success:
                    print(f"      Ошибка: {result.error_message}")

        except Exception as e:
            print(f"  Ошибка тестирования: {e}")

    print("\n4. Выполнение примера пайплайна...")

    if os.path.exists("config/pipeline_example.json"):
        runner = PipelineRunner(manager)

        try:
            pipeline = runner.load_pipeline("config/pipeline_example.json")
            errors = runner.validate_pipeline(pipeline)

            if errors:
                print("  Ошибки валидации пайплайна:")
                for error in errors:
                    print(f"    ❌ {error}")
            else:
                print("  ✓ Пайплайн валиден")

                print("  Выполнение в режиме симуляции...")
                runner.set_dry_run(True)
                result = runner.run_pipeline(pipeline)

                print(
                    f"  Результат: {result['successful_steps']}/{result['total_steps']} шагов выполнено"
                )
                print(f"  Время выполнения: {result['total_duration']:.3f}с")

        except Exception as e:
            print(f"  Ошибка выполнения пайплайна: {e}")
    else:
        print("  Файл pipeline_example.json не найден")

    print("\n5. Демонстрация работы с FakeDevice...")

    fake_device_id = None
    for device in devices:
        if device["type"] == "FakeDevice":
            fake_device_id = device["id"]
            break

    if fake_device_id:
        try:
            device = manager.get(fake_device_id)

            print(f"  Запуск устройства {fake_device_id}...")
            manager.start(fake_device_id)

            print("  Получение статуса...")
            status = device.status()
            print(f"    Статус: {status}")

            print("  Выполнение команды...")
            device_type = device.params.get("device_type", "generic")

            if device_type == "camera":
                result = device.send_command("capture")
                print(f"    Результат capture: {result}")
            elif device_type == "motor":
                result = device.send_command("move", steps=5)
                print(f"    Результат move: {result}")
            else:
                result = device.send_command("ping")
                print(f"    Результат ping: {result}")

            print(f"  Остановка устройства {fake_device_id}...")
            manager.stop(fake_device_id)

        except Exception as e:
            print(f"  Ошибка работы с устройством: {e}")
    else:
        print("  FakeDevice не найдено в конфигурации")

    print("\n" + "=" * 60)
    print("Демонстрация завершена!")
    print("\nДля дальнейшего изучения:")
    print("  - Изучите CLI: python cli.py --help")
    print("  - Запустите тесты: pytest tests/ -v")
    print("  - Изучите конфигурацию: config/devices.json")
    print("  - Создайте свой пайплайн: config/my_pipeline.json")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nДемонстрация прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)
