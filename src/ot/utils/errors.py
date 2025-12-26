class StorageNotInitializedError(RuntimeError):
    """Raised when the storage service has not been initialized yet."""

    pass


class StorageAlreadyInitializedError(SystemError):
    """Raised when attempting to initialize storage that is already initialized."""

    pass


class DayUnsetError(ValueError):
    """Raised when attempting to access a day that is not set."""

    pass


class DayCollisionError(ValueError):
    """Raised when attempting to add a day that already exists."""

    pass


class DayDoneError(ValueError):
    """Raised when attempting to mark a day as done that is already marked as done."""

    pass


class InvalidDateStringError(ValueError):
    """Raised when a date string is not in the expected format."""

    def __init__(self, date_string: str, format_code: str) -> None:
        super().__init__(f"Date '{date_string}' does not match format '{format_code}'")
