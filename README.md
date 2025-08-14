# Device Orchestra — Universal Device Control & Debug Framework by Udav

Легкая и расширяемая OOP-система для управления оборудованием и отладки CV-пайплайнов.

## Содержание

- [Зачем это нужно?](#зачем-это-нужно)
  - [Главная проблема - ХАОС в автоматизации](#главная-проблема---хаос-в-автоматизации)
  - [5 ключевых преимуществ](#5-ключевых-преимуществ)
- [Простыми словами](#простыми-словами)
- [Для кого это?](#для-кого-это)
- [Конечная выгода](#конечная-выгода)
- [Быстрый старт](#быстрый-старт)
- [Архитектура проекта](#архитектура-проекта)
  - [Структура директорий](#структура-директорий)
  - [Ключевые паттерны](#ключевые-паттерны)
  - [Точки входа для разработки](#точки-входа-для-разработки)
- [Конфигурация устройств](#конфигурация-устройств)
- [Пайплайны](#пайплайны)
- [API для устройств](#api-для-устройств)
- [CLI команды](#cli-команды)
- [Тестирование](#тестирование)
- [E2E Демонстрация](#e2e-демонстрация)
- [Логирование](#логирование)
- [Требования](#требования)
- [Расширение системы](#расширение-системы)
- [Безопасность](#безопасность)
- [Дальнейшее развитие](#дальнейшее-развитие)

## Зачем это нужно?

### **Главная проблема - ХАОС в автоматизации**

**У вас есть куча инструментов, но они не дружат:**
```
📁 focus_stacking/     → свой API, свои параметры
📁 camera_control/     → свой протокол, своя логика  
📁 analytics/          → свои форматы, свои команды
📁 motor_control/      → свои интерфейсы, свои настройки
```

**Device Orchestra делает это все через единый интерфейс**
```
focus.send_command("stack", layers=30, step=0.1)
camera.send_command("capture", resolution="4K")  
analytics.send_command("detect", model="yolo")
motor.send_command("move", x=10, y=5)
```

### **5 ключевых преимуществ**

#### **PLUG & PLAY архитектура**
- Любое устройство = просто класс наследник `DeviceBase`
- Новая камера? Создали класс → добавили в JSON → работает
- Нет переписывания существующего кода

#### **CONFIG-FIRST подход**
```json
// Изменили параметры в JSON - поведение изменилось
{
  "id": "main_camera",
  "params": {
    "resolution": [4096, 3072],  // ← просто поменяли
    "exposure": 100,
    "algorithm": "auto_focus"    // ← переключили алгоритм
  }
}
```

#### **ТЕСТИРУЕМОСТЬ без железа**
```bash
# Тестируете сложный пайплайн БЕЗ реального оборудования
python cli.py run-pipeline macro_scan.json --dry-run

# Каждое устройство по отдельности
python cli.py test focus_motor --verbose
```

#### **ПЕРЕИСПОЛЬЗОВАНИЕ компонентов**
```python
# Один и тот же мотор в разных пайплайнах
focus_motor.send_command("move", steps=100)    # фокус-стекинг
focus_motor.send_command("move", steps=-50)    # возврат позиции
focus_motor.send_command("home")               # калибровка
```

#### **НАБЛЮДАЕМОСТЬ из коробки**
- Автоматические логи всех операций
- Мониторинг производительности  
- Event-система для реакции компонентов

### **Простыми словами**

**Device Orchestra превращает ваш "зоопарк скриптов" в "оркестр музыкантов"**

- **Дирижёр** = DeviceManager (управляет всеми)
- **Музыканты** = ваши устройства (каждый знает свою партию)  
- **Ноты** = JSON пайплайны (описывают что играть)
- **Концерт** = выполнение workflow

**Результат:** Вместо хаоса - слаженная работа всех компонентов! 🎉

### **Для кого это?**

- **Исследователи** - автоматизация экспериментов
- **Фотографы** - макросъёмка, фокус-стекинг
- **Робототехники** - управление множеством актуаторов
- **Автоматизаторы** - промышленные процессы
- **Мейкеры** - DIY проекты с Arduino/RaspberryPi/OrangePi

### **Конечная выгода**

- **Экономия времени** - больше не собираете workflow из кусочков
- **Меньше багов** - тестируете каждый компонент отдельно
- **Масштабируемость** - легко добавляете новые устройства
- **Командная работа** - понятная архитектура для всех
- **Переиспользование** - один раз написали, везде используете

## Быстрый старт

```bash
git clone https://github.com/SadreevJ/device-orchestra.git
cd device-orchestra
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Тестирование
python example_usage.py
pytest tests/ -v

# CLI команды
python cli.py status
python cli.py test fake_cam
python cli.py run-pipeline config/pipeline_example.json --dry-run
```

## Архитектура проекта

### Структура директорий

```
device-orchestra/
├── 📁 core/                # Ядро системы (7 файлов)
│   ├── __init__.py         # Инициализация и регистрация устройств
│   ├── device_base.py      # Базовый абстрактный класс для всех устройств
│   ├── device_manager.py   # Менеджер устройств с Factory pattern
│   ├── device_factory.py   # Фабрика для создания устройств по типам
│   ├── config_loader.py    # Загрузчик JSON конфигураций
│   ├── events.py           # Event Bus (Observer pattern)
│   └── logger.py           # Унифицированное логирование
│
├── 📁 devices/             # Реализации устройств (3 файла)
│   ├── __init__.py         # Экспорт всех устройств
│   ├── camera_opencv.py    # OpenCV камера (capture, save_frame)
│   └── motor_stepper.py    # Шаговый мотор (home, move, stop)
│
├── 📁 adapters/            # Адаптеры протоколов (2 файла)
│   ├── __init__.py         # Инициализация адаптеров
│   └── serial_adapter.py   # Serial порт (с эмуляцией для тестов)
│
├── 📁 debug_tools/         # Инструменты отладки (4 файла)
│   ├── __init__.py         # Экспорт отладочных инструментов
│   ├── fake_device.py      # Фейковые устройства для тестирования
│   ├── device_tester.py    # Автоматическое тестирование устройств
│   └── perf_monitor.py     # Монитор производительности системы
│
├── 📁 runners/             # Исполнители пайплайнов (2 файла)
│   ├── __init__.py         # Инициализация runners
│   └── pipeline_runner.py  # Выполнение JSON пайплайнов
│
├── 📁 tests/               # Тесты (2 файла)
│   ├── test_core.py        # Unit тесты для core модулей
│   └── test_pipeline.py    # Integration тесты с PipelineRunner
│
├── 📁 config/              # Конфигурация (2 файла)
│   ├── devices.json        # Описание устройств
│   └── pipeline_example.json # Пример пайплайна
│
├── 📁 logs/                # Логи (создается автоматически)
│   └── device-orchestra_YYYYMMDD.log   # Логи работы системы
│
├── cli.py                  # CLI интерфейс
├── example_usage.py        # Демонстрация возможностей
├── pyproject.toml          # Конфигурация проекта (форматирование, линтеры)
├── requirements.txt        # Зависимости Python
└── LICENSE                 # MIT лицензия
```

### Ключевые паттерны

- **Factory Pattern** — `DeviceFactory` создает устройства по типам
- **Observer Pattern** — `EventBus` для событий устройств
- **Adapter Pattern** — `SerialAdapter` для протоколов
- **Command Pattern** — `send_command()` интерфейс
- **Config-first** — все устройства описаны в JSON

### Точки входа для разработки

| Задача | Файл | Описание |
|--------|------|----------|
| Новое устройство | `devices/my_device.py` | Наследуйте от `DeviceBase` |
| Новый адаптер | `adapters/my_adapter.py` | Реализуйте протокол связи |
| Тестирование | `tests/test_my_feature.py` | Unit/Integration тесты |
| Конфигурация | `config/devices.json` | Добавьте описание устройства |
| CLI команда | `cli.py` | Расширьте интерфейс |
| Пайплайн | `config/my_pipeline.json` | JSON описание последовательности |

## Конфигурация устройств

```json
[
  {
    "id": "cam1",
    "type": "OpenCVCamera",
    "params": {
      "index": 0,
      "resolution": [1920, 1080],
      "fps": 30
    }
  },
  {
    "id": "motor1", 
    "type": "StepperMotor",
    "params": {
      "port": "/dev/ttyUSB0",
      "baudrate": 115200,
      "microstep": 16
    }
  }
]
```

## Пайплайны

```json
[
  {
    "step": "init",
    "device": "motor1",
    "action": "home"
  },
  {
    "step": "capture", 
    "device": "cam1",
    "action": "capture",
    "save_to": "images/step1.jpg"
  },
  {
    "step": "move",
    "device": "motor1", 
    "action": "move",
    "args": {"steps": 200}
  }
]
```

## API для устройств

### Базовый класс DeviceBase

```python
class DeviceBase(ABC):
    def __init__(self, id: str, params: Dict[str, Any])
    def start(self) -> None                    # Запуск устройства
    def stop(self) -> None                     # Остановка  
    def status(self) -> Dict[str, Any]         # Статус
    def send_command(self, command: str, **kwargs) -> Any  # Команды
```

### Пример устройства

```python
from core.device_base import DeviceBase

class MyDevice(DeviceBase):
    def start(self):
        # Инициализация устройства
        pass
        
    def stop(self):
        # Завершение работы
        pass
        
    def status(self):
        return {"id": self.id, "connected": True}
        
    def send_command(self, command, **kwargs):
        if command == "my_action":
            return {"result": "success"}
```

### Регистрация устройства

```python
# В core/__init__.py
from devices.my_device import MyDevice
device_factory.register("MyDevice", MyDevice)

# В config/devices.json  
{
  "id": "my_dev1",
  "type": "MyDevice",
  "params": {"param1": "value1"}
}
```

## CLI команды

```bash
python cli.py status                           # Статус всех устройств
python cli.py test <device_id>                 # Тестирование устройства  
python cli.py debug <device_id>                # Интерактивная отладка
python cli.py run-pipeline <file>              # Выполнение пайплайна
python cli.py run-pipeline <file> --dry-run    # Симуляция без реального выполнения
```

## Тестирование

```bash
# Все тесты
pytest tests/ -v

# Конкретные модули
pytest tests/test_core.py -v        # Тесты ядра системы
pytest tests/test_pipeline.py -v    # Тесты пайплайнов

# Тестирование устройств через CLI
python cli.py test fake_cam          # Тест фейковой камеры
python cli.py test fake_motor        # Тест фейкового мотора
python cli.py test cam1 --verbose    # Подробное тестирование реальной камеры

# Демонстрация возможностей
python example_usage.py             # Полная демонстрация системы

# Dry-run пайплайна (без реального выполнения)
python cli.py run-pipeline config/pipeline_example.json --dry-run
```

## E2E Демонстрация

Система включает E2E тесты, которые демонстрируют работу виртуального термометра и показывают, как архитектура обрабатывает события в реальном времени без реального железа.

### Что демонстрирует виртуальный термометр:

- **Периодическая генерация данных** — измерения температуры каждые 100-200мс
- **Event-driven архитектура** — события отправляются через `EventBus`
- **Автоматическая реакция на перегрев** — при температуре > 28°C система активирует охлаждение
- **Логирование и мониторинг** — все события сохраняются для анализа
- **Concurrent обработка** — поддержка нескольких термометров одновременно

### Запуск E2E теста:

```bash
# Полный тест-сценарий
pytest tests/e2e/test_virtual_device_flow.py -v

# Конкретный тест
pytest tests/e2e/test_virtual_device_flow.py::TestVirtualDeviceFlow::test_overheat_detection_and_cooling -v

# С подробным выводом
pytest tests/e2e/test_virtual_device_flow.py -v -s
```

> **Примечание:** Файл `test_virtual_device_flow.py` был разработан, но в настоящее время отсутствует в репозитории. Кэш PyTest показывает, что тест выполнялся ранее.

### Что проверяет E2E тест:

- ✅ **Жизненный цикл устройства** — запуск, работа, остановка
- ✅ **Генерация и обработка данных** — измерения температуры в реальном времени
- ✅ **Event Bus** — корректная отправка и получение событий
- ✅ **Система реагирования** — автоматическое охлаждение при перегреве
- ✅ **Логирование** — сохранение всех операций для анализа
- ✅ **Concurrent работа** — несколько устройств одновременно
- ✅ **Команды устройств** — управление через унифицированный API

### Альтернатива E2E тестам:

Вы можете использовать существующие инструменты демонстрации:

```bash
# Демонстрация FakeDevice с эмуляцией событий
python example_usage.py

# Интерактивное тестирование устройств
python cli.py debug fake_cam
python cli.py debug fake_motor
```

## Логирование

Device Orchestra использует структурированное логирование:

```python
from core import get_logger

logger = get_logger("my_module")
logger.info("Информационное сообщение")
logger.error("Ошибка")
```

Логи автоматически сохраняются в `logs/device-orchestra_YYYYMMDD.log`. Папка `logs/` создается автоматически при первом запуске.

## Требования

- **Python 3.11+**
- **OpenCV** для камер: `pip install opencv-python`
- **Serial** для моторов: `pip install pyserial`
- **psutil** для мониторинга: `pip install psutil`

### Linux
```bash
sudo apt install python3.11 python3.11-venv libgl1
```

### Windows  
Установите Python 3.11+ и Git for Windows.

### OrangePi/RaspberryPi
```bash
pip install python-periphery
sudo usermod -a -G dialout $USER  # Для serial портов
```

## Расширение системы

### Добавление нового устройства

1. **Создайте класс** в `devices/my_device.py`
2. **Зарегистрируйте** в `core/__init__.py`  
3. **Добавьте конфигурацию** в `config/devices.json`
4. **Напишите тесты** в `tests/test_my_device.py`

### Новый тип пайплайна

1. **Расширьте** `PipelineRunner._execute_step()`
2. **Добавьте валидацию** в `_validate_step()`
3. **Создайте пример** в `config/my_pipeline.json`

### Новый адаптер протокола

1. **Создайте класс** в `adapters/my_adapter.py`
2. **Добавьте в** `adapters/__init__.py`
3. **Используйте** в устройствах

## Демонстрация и тестирование

Проект включает встроенные инструменты для демонстрации и тестирования:

### FakeDevice - эмуляция устройств

Система поставляется с `FakeDevice` - универсальным эмулятором устройств:

```python
# Конфигурация фейковой камеры
{
  "id": "fake_cam",
  "type": "FakeDevice", 
  "params": {
    "device_type": "camera",
    "simulation_mode": "normal",
    "base_delay": 0.1,
    "error_probability": 0.02
  }
}
```

**Поддерживаемые типы устройств:**
- `camera` - имитация камеры (capture, get_frame)
- `motor` - имитация мотора (move, home, stop)
- `generic` - базовые команды (ping, status)

**Режимы симуляции:**
- `normal` - стандартная работа с задержками
- `fast` - ускоренная симуляция для тестов
- `error` - повышенная вероятность ошибок

### Полная демонстрация системы

```bash
# Запуск example_usage.py покажет:
python example_usage.py

# ✅ Загрузку и инициализацию устройств
# ✅ Автоматическое тестирование каждого устройства  
# ✅ Валидацию и выполнение пайплайна в dry-run режиме
# ✅ Интерактивную работу с FakeDevice
# ✅ Демонстрацию команд и статусов
```

## Безопасность

- ✅ `.gitignore` исключает логи и конфиденциальные файлы
- ✅ Нет хардкоженых паролей или ключей
- ✅ Все конфигурации в отдельных JSON файлах
- ✅ Обработка ошибок и логирование
- ✅ Изоляция устройств через абстракции

## Дальнейшее развитие

### 🚀 Планируемые улучшения

- [ ] **Асинхронная архитектура** — Поддержка async/await для неблокирующих операций
- [ ] **Communication Interface** — Унифицированные интерфейсы связи для разных протоколов
- [ ] **Web API** — FastAPI endpoints для HTTP управления
- [ ] **WebSocket** — Real-time события устройств  
- [ ] **Web UI** — React интерфейс управления
- [ ] **Docker** — Контейнеризация
- [ ] **Plugins** — Система плагинов для устройств
- [ ] **YAML** — Альтернативная конфигурация
- [ ] **SSH/REST** — Дополнительные адаптеры связи

## Лицензия

MIT License — см. [LICENSE](LICENSE)



## Участие в разработке

1. Fork репозитория `SadreevJ/device-orchestra`
2. Клонируйте ваш fork: `git clone https://github.com/YOUR_USERNAME/device-orchestra.git`
3. Создайте feature branch: `git checkout -b feature/amazing-feature`
4. Внесите изменения и commit: `git commit -m 'Add amazing feature'`
5. Push в ваш fork: `git push origin feature/amazing-feature`
6. Создайте Pull Request в основной репозиторий
