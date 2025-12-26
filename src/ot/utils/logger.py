import logging


class Logger:
    def __init__(self, name: str, level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(level)
        self.formatter = logging.Formatter("[%(name)s] %(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    @property
    def level(self) -> int:
        return self.logger.level

    def debug(self, message: str):
        self.logger.debug("DEBUG: %s", message)

    def info(self, message: str):
        self.logger.info("INFO: %s", message)

    def warning(self, message: str):
        self.logger.warning("WARNING: %s", message)

    def error(self, message: str):
        self.logger.error("ERROR: %s", message)

    def exception(self, message: str):
        self.logger.exception("ERROR: %s", message)


_logger_instance: Logger | None = None


def get_logger(name: str = "ot", level: int = logging.INFO) -> Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(name, level)
    return _logger_instance
