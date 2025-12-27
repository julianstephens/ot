import logging

from rich.logging import RichHandler


class Logger:
    def __init__(self, name: str, level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.handler = RichHandler(rich_tracebacks=True, show_time=False)
        self.handler.setLevel(level)
        self.formatter = logging.Formatter("[%(name)s] %(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    @property
    def level(self) -> int:
        return self.logger.level

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def exception(self, message: str):
        self.logger.exception(message)


_logger_instance: Logger | None = None


def get_logger(name: str = "ot", level: int = logging.INFO) -> Logger:
    """Provides a singleton Logger instance.

    Args:
        name (str, optional): Logger name. Defaults to "ot".
        level (int, optional): Logging level. Defaults to logging.INFO.

    Returns:
        Logger: The singleton Logger instance.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(name, level)
    return _logger_instance
