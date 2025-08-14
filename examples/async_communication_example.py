#!/usr/bin/env python3
"""
Пример использования асинхронных компонентов связи device-orchestra.

Демонстрирует:
- Создание адаптеров через фабрику
- Асинхронное подключение и отключение
- Отправку команд с версионированием протоколов
- Обработку ошибок
"""

import asyncio
import logging
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication_factory import CommunicationFactory
from adapters.async_serial_adapter import AsyncSerialAdapter


async def demo_basic_usage():
    """Демонстрация базового использования асинхронного адаптера."""
    print("\n=== Демонстрация базового использования ===")
    
    # Адаптер уже зарегистрирован в adapters/__init__.py
    print("Адаптер 'serial' уже зарегистрирован в фабрике")
    
    # Создаем адаптер через фабрику
    config = {
        "port": "/dev/ttyUSB0",
        "baudrate": 115200,
        "timeout": 1.0,
        "protocol_version": "2.0"
    }
    
    adapter = CommunicationFactory.create("serial", config)
    print(f"Создан адаптер: {type(adapter).__name__}")
    print(f"Конфигурация: {adapter.get_config()}")
    
    try:
        # Подключаемся
        print("Подключение к устройству...")
        await adapter.connect()
        print(f"Статус подключения: {adapter.get_status()}")
        
        # Отправляем команды
        commands = [
            ("PING", {}),
            ("STATUS", {}),
            ("MOVE", {"steps": 100, "speed": "fast"}),
            ("GET_POSITION", {})
        ]
        
        for command, params in commands:
            print(f"\nОтправка команды: {command} с параметрами: {params}")
            try:
                response = await adapter.send_command(command, **params)
                print(f"Ответ: {response}")
            except Exception as e:
                print(f"Ошибка команды {command}: {e}")
        
        # Проверяем здоровье соединения
        print(f"\nПроверка здоровья соединения...")
        is_healthy = await adapter.health_check()
        print(f"Соединение здорово: {is_healthy}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
    
    finally:
        # Отключаемся
        print("\nОтключение от устройства...")
        await adapter.disconnect()
        print("Отключение завершено")


async def demo_protocol_versions():
    """Демонстрация работы с версиями протоколов."""
    print("\n=== Демонстрация версий протоколов ===")
    
    # Создаем адаптеры с разными версиями протоколов
    adapters = {}
    
    for version in ["1.0", "2.0", "3.0"]:
        config = {
            "port": f"/dev/ttyUSB{version.split('.')[0]}",
            "protocol_version": version
        }
        adapter = AsyncSerialAdapter(config)
        adapters[version] = adapter
    
    try:
        # Подключаем все адаптеры
        for version, adapter in adapters.items():
            print(f"Подключение адаптера версии {version}...")
            await adapter.connect()
        
        # Отправляем одинаковую команду через разные версии
        command = "MOVE"
        params = {"steps": 50}
        
        for version, adapter in adapters.items():
            print(f"\nОтправка команды через протокол версии {version}")
            response = await adapter.send_command(command, **params)
            print(f"Ответ: {response}")
            print(f"Использованная версия: {adapter.protocol_version.value}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
    
    finally:
        # Отключаем все адаптеры
        for version, adapter in adapters.items():
            print(f"Отключение адаптера версии {version}...")
            await adapter.disconnect()


async def demo_error_handling():
    """Демонстрация обработки ошибок."""
    print("\n=== Демонстрация обработки ошибок ===")
    
    # Создаем адаптер с неверным портом
    config = {
        "port": "/dev/nonexistent",
        "baudrate": 115200
    }
    
    adapter = AsyncSerialAdapter(config)
    
    # Попытка подключения к несуществующему порту
    print("Попытка подключения к несуществующему порту...")
    try:
        await adapter.connect()
    except Exception as e:
        print(f"Ожидаемая ошибка подключения: {e}")
    
    # Попытка отправки команды без подключения
    print("\nПопытка отправки команды без подключения...")
    try:
        await adapter.send_command("PING")
    except Exception as e:
        print(f"Ожидаемая ошибка отправки: {e}")
    
    # Проверка статуса
    status = adapter.get_status()
    print(f"Статус адаптера: {status}")


async def demo_factory_features():
    """Демонстрация возможностей фабрики."""
    print("\n=== Демонстрация возможностей фабрики ===")
    
    # Показываем доступные адаптеры
    print("Доступные адаптеры:")
    print(CommunicationFactory.list_available())
    
    # Проверяем регистрацию
    is_registered = CommunicationFactory.is_registered("serial")
    print(f"Адаптер 'serial' зарегистрирован: {is_registered}")
    
    # Создаем адаптер
    config = {"port": "/dev/ttyUSB0"}
    adapter = CommunicationFactory.create("serial", config)
    print(f"Создан адаптер через фабрику: {type(adapter).__name__}")
    
    # Показываем класс адаптера
    adapter_class = CommunicationFactory.get_adapter_class("serial")
    print(f"Класс адаптера 'serial': {adapter_class}")
    
    # Демонстрируем регистрацию нового адаптера
    print(f"\nДемонстрация регистрации нового адаптера...")
    try:
        CommunicationFactory.register("test_serial", AsyncSerialAdapter)
        print("Зарегистрирован новый адаптер 'test_serial'")
        print("Доступные адаптеры после регистрации:")
        print(CommunicationFactory.list_available())
        
        # Удаляем тестовую регистрацию
        CommunicationFactory.unregister("test_serial")
        print("Удалена тестовая регистрация 'test_serial'")
    except Exception as e:
        print(f"Ошибка при демонстрации: {e}")


async def main():
    """Основная функция демонстрации."""
    print("🚀 Демонстрация асинхронных компонентов связи device-orchestra")
    print("=" * 60)
    
    try:
        # Демонстрация базового использования
        await demo_basic_usage()
        
        # Демонстрация версий протоколов
        await demo_protocol_versions()
        
        # Демонстрация обработки ошибок
        await demo_error_handling()
        
        # Демонстрация возможностей фабрики
        await demo_factory_features()
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Демонстрация завершена!")


if __name__ == "__main__":
    # Запуск демонстрации
    asyncio.run(main())
