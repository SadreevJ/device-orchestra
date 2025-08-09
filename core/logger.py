import logging
import sys
import os
from datetime import datetime
from typing import Optional


class UCDFLogger:
    def __init__(self):
        self._setup_logger()

    def _setup_logger(self):
        os.makedirs("logs", exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        root_logger = logging.getLogger("ucdf")
        root_logger.setLevel(logging.INFO)

        root_logger.handlers.clear()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        log_file = f"logs/ucdf_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info("UCDF Logger инициализирован")

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(f"ucdf.{name}")


_logger_instance: Optional[UCDFLogger] = None


def get_logger(name: str = "main") -> logging.Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = UCDFLogger()
    return _logger_instance.get_logger(name)
