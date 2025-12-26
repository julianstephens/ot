from datetime import datetime

import typer
from rich import print
from rich.panel import Panel

from ot.utils.errors import InvalidDateStringError

from .constants import DATE_FORMAT, MONTH_FORMAT


def print_info(message: str, with_icon=True) -> None:
    print(f"{':information: ' if with_icon else ''}{message}")


def print_success(message: str) -> None:
    print(Panel(message, title="Success", style="bold green"))


def print_warning(message: str) -> None:
    print(f"[bold yellow]:warning:[/bold yellow] {message}")


def print_error(message: str) -> None:
    print(Panel(message, title="Error", style="bold red"))


def validate(date_string: str, format_code: str) -> datetime:
    try:
        datetime_object = datetime.strptime(date_string, format_code)
        if date_string != datetime_object.strftime(format_code):
            raise InvalidDateStringError(date_string, format_code)
    except ValueError as ex:
        raise InvalidDateStringError(date_string, format_code) from ex
    else:
        return datetime_object


def validate_date_string(date: str | None) -> str | None:
    """Validates a date string in YYYY-MM-DD format.

    Args:
        date (str | None): The date string to validate.

    Raises:
        typer.BadParameter: If the date string is not valid.
    """

    if date is None:
        return None
    try:
        validated_date = validate(date, DATE_FORMAT)
    except InvalidDateStringError as ex:
        raise typer.BadParameter(str(ex)) from ex
    else:
        return validated_date.strftime(DATE_FORMAT)


def validate_month_string(month: str | None) -> str | None:
    """Validates a month string in YYYY-MM format.

    Args:
        month (str | None): The month string to validate.

    Raises:
        typer.BadParameter: If the month string is not valid.
    """

    if month is None:
        return None
    try:
        validated_date = validate(month, MONTH_FORMAT)
    except InvalidDateStringError as ex:
        raise typer.BadParameter(str(ex)) from ex
    else:
        return validated_date.strftime(MONTH_FORMAT)
