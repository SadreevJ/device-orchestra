import argparse
import sys
import os
import json
from core import DeviceManager, get_logger
from runners.pipeline_runner import PipelineRunner


def status_command(args):
    logger = get_logger("cli")

    try:
        manager = DeviceManager()
        manager.load_config("config")

        devices = manager.list()

        print("Состояние устройств UCDF:")
        print("-" * 50)

        if not devices:
            print("Устройства не найдены")
            return

        for device in devices:
            device_id = device.get("id", "unknown")
            device_type = device.get("type", "unknown")
            status = device.get("status", {})

            print(f"ID: {device_id}")
            print(f"Тип: {device_type}")
            print(f"Статус: {status}")
            print("-" * 30)

    except Exception as e:
        logger.error(f"Ошибка команды status: {e}")
        print(f"Ошибка: {e}")
        sys.exit(1)


def test_command(args):
    device_id = args.device_id
    logger = get_logger("cli")

    try:
        manager = DeviceManager()
        manager.load_config("config")

        device = manager.get(device_id)

        print(f"Тестирование устройства: {device_id}")
        print("-" * 40)

        print("1. Запуск устройства...")
        manager.start(device_id)
        print("✓ Устройство запущено")

        print("2. Проверка статуса...")
        status = device.status()
        print(f"✓ Статус: {status}")

        print("3. Выполнение тестовой команды...")
        if device.type == "OpenCVCamera":
            result = device.send_command("capture")
            print(f"✓ Команда capture выполнена: {result}")
        elif device.type == "StepperMotor":
            result = device.send_command("get_position")
            print(f"✓ Команда get_position выполнена: {result}")
        elif device.type == "FakeDevice":
            result = device.send_command("ping")
            print(f"✓ Команда ping выполнена: {result}")
        else:
            print("✓ Специальные тесты для этого типа устройства не реализованы")

        print("4. Остановка устройства...")
        manager.stop(device_id)
        print("✓ Устройство остановлено")

        print("\nТест завершен успешно!")

    except Exception as e:
        logger.error(f"Ошибка команды test: {e}")
        print(f"Ошибка: {e}")
        sys.exit(1)


def run_pipeline_command(args):
    pipeline_file = args.pipeline_file
    logger = get_logger("cli")

    try:
        if not os.path.exists(pipeline_file):
            print(f"Файл пайплайна не найден: {pipeline_file}")
            sys.exit(1)

        manager = DeviceManager()
        manager.load_config("config")

        runner = PipelineRunner(manager)

        if args.dry_run:
            runner.set_dry_run(True)
            print("Режим DRY RUN включен")

        print(f"Выполнение пайплайна: {pipeline_file}")
        print("-" * 50)

        pipeline = runner.load_pipeline(pipeline_file)

        print("Валидация пайплайна...")
        errors = runner.validate_pipeline(pipeline)
        if errors:
            print("Ошибки валидации:")
            for error in errors:
                print(f"  ❌ {error}")
            sys.exit(1)
        print("✓ Пайплайн валиден")

        devices_to_start = set()
        for step in pipeline:
            if "device" in step:
                devices_to_start.add(step["device"])

        print("Запуск устройств...")
        for device_id in devices_to_start:
            try:
                manager.start(device_id)
                print(f"✓ Устройство {device_id} запущено")
            except Exception as e:
                print(f"❌ Ошибка запуска {device_id}: {e}")

        result = runner.run_pipeline(pipeline)

        print("Остановка устройств...")
        for device_id in devices_to_start:
            try:
                manager.stop(device_id)
                print(f"✓ Устройство {device_id} остановлено")
            except Exception as e:
                print(f"❌ Ошибка остановки {device_id}: {e}")

        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ ПАЙПЛАЙНА")
        print("=" * 50)
        print(f"Всего шагов: {result['total_steps']}")
        print(f"Выполнено: {result['executed_steps']}")
        print(f"Успешно: {result['successful_steps']}")
        print(f"Ошибок: {result['failed_steps']}")
        print(f"Время выполнения: {result['total_duration']:.3f}с")

        if result["errors"]:
            print("\nОШИБКИ:")
            for error in result["errors"]:
                print(f"  Шаг {error['step_index']}: {error['error']}")

        if args.save_result:
            with open(args.save_result, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nРезультат сохранен в: {args.save_result}")

        if result["failed_steps"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ошибка команды run-pipeline: {e}")
        print(f"Ошибка: {e}")
        sys.exit(1)


def debug_command(args):
    device_id = args.device_id
    log_level = args.log_level

    logger = get_logger("cli")

    if log_level:
        import logging

        level = getattr(logging, log_level.upper(), logging.INFO)
        logging.getLogger("ucdf").setLevel(level)
        print(f"Уровень логирования установлен: {log_level}")

    try:
        manager = DeviceManager()
        manager.load_config("config")

        device = manager.get(device_id)

        print(f"Режим отладки для устройства: {device_id}")
        print("-" * 40)

        manager.start(device_id)
        print("Устройство запущено")

        print("\nВведите команды для устройства (quit для выхода):")

        while True:
            try:
                command = input(f"{device_id}> ").strip()

                if command.lower() in ["quit", "exit", "q"]:
                    break

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0]
                args_dict = {}

                for part in parts[1:]:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        try:
                            if "." in value:
                                args_dict[key] = float(value)
                            else:
                                args_dict[key] = int(value)
                        except ValueError:
                            args_dict[key] = value

                result = device.send_command(cmd, **args_dict)
                print(f"Результат: {result}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Ошибка команды: {e}")

        manager.stop(device_id)
        print("Устройство остановлено")

    except Exception as e:
        logger.error(f"Ошибка команды debug: {e}")
        print(f"Ошибка: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="UCDF - Universal Device Control & Debug Framework", prog="ucdf")

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    status_parser = subparsers.add_parser("status", help="Показать состояние устройств")

    test_parser = subparsers.add_parser("test", help="Выполнить тест устройства")
    test_parser.add_argument("device_id", help="ID устройства для тестирования")

    pipeline_parser = subparsers.add_parser("run-pipeline", help="Выполнить пайплайн")
    pipeline_parser.add_argument("pipeline_file", help="Путь к файлу пайплайна")
    pipeline_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Режим симуляции (без реального выполнения)",
    )
    pipeline_parser.add_argument("--save-result", help="Сохранить результат в файл")

    debug_parser = subparsers.add_parser("debug", help="Режим отладки устройства")
    debug_parser.add_argument("device_id", help="ID устройства для отладки")
    debug_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="debug",
        help="Уровень логирования",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "status":
        status_command(args)
    elif args.command == "test":
        test_command(args)
    elif args.command == "run-pipeline":
        run_pipeline_command(args)
    elif args.command == "debug":
        debug_command(args)
    else:
        print(f"Неизвестная команда: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
