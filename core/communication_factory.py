from typing import Dict, Any, Type
from .communication_interface import CommunicationInterface


class CommunicationFactory:
    """
    Фабрика для создания адаптеров связи.
    
    Позволяет регистрировать и создавать различные типы адаптеров связи
    по их названию и конфигурации.
    """
    
    _adapters: Dict[str, Type[CommunicationInterface]] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: Type[CommunicationInterface]) -> None:
        """
        Регистрация нового адаптера связи.
        
        Args:
            name: Уникальное имя адаптера
            adapter_class: Класс адаптера (должен наследоваться от CommunicationInterface)
            
        Raises:
            ValueError: Если адаптер с таким именем уже зарегистрирован
        """
        if name in cls._adapters:
            raise ValueError(f"Адаптер с именем '{name}' уже зарегистрирован")
        
        if not issubclass(adapter_class, CommunicationInterface):
            raise ValueError(f"Класс {adapter_class} должен наследоваться от CommunicationInterface")
        
        cls._adapters[name] = adapter_class
    
    @classmethod
    def create(cls, adapter_type: str, config: Dict[str, Any]) -> CommunicationInterface:
        """
        Создание адаптера связи по типу.
        
        Args:
            adapter_type: Тип адаптера (имя зарегистрированного адаптера)
            config: Конфигурация для создания адаптера
            
        Returns:
            Экземпляр адаптера связи
            
        Raises:
            ValueError: Если адаптер с таким типом не найден
        """
        if adapter_type not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Неизвестный тип адаптера связи: '{adapter_type}'. "
                f"Доступные типы: {available}"
            )
        
        adapter_class = cls._adapters[adapter_type]
        return adapter_class(config)
    
    @classmethod
    def list_available(cls) -> list:
        """
        Получение списка доступных адаптеров.
        
        Returns:
            Список имен зарегистрированных адаптеров
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_registered(cls, adapter_type: str) -> bool:
        """
        Проверка регистрации адаптера.
        
        Args:
            adapter_type: Тип адаптера для проверки
            
        Returns:
            True если адаптер зарегистрирован
        """
        return adapter_type in cls._adapters
    
    @classmethod
    def get_adapter_class(cls, adapter_type: str) -> Type[CommunicationInterface]:
        """
        Получение класса адаптера по типу.
        
        Args:
            adapter_type: Тип адаптера
            
        Returns:
            Класс адаптера
            
        Raises:
            ValueError: Если адаптер не найден
        """
        if adapter_type not in cls._adapters:
            raise ValueError(f"Адаптер '{adapter_type}' не найден")
        
        return cls._adapters[adapter_type]
    
    @classmethod
    def unregister(cls, adapter_type: str) -> bool:
        """
        Удаление регистрации адаптера.
        
        Args:
            adapter_type: Тип адаптера для удаления
            
        Returns:
            True если адаптер был удален, False если не найден
        """
        if adapter_type in cls._adapters:
            del cls._adapters[adapter_type]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """
        Очистка всех зарегистрированных адаптеров.
        """
        cls._adapters.clear()
