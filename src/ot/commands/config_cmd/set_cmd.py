from typing import Annotated

import typer
from rich.prompt import Confirm, Prompt

from ot.services import StorageService
from ot.utils import (
    SETTINGS_FIELDS,
    SettingsKeys,
    StorageNotInitializedError,
    print_error,
    print_success,
)

from . import app


def set_default_log_days(storage: StorageService) -> None:
    settings = storage.settings
    default_days = Prompt.ask(
        "Enter default number of days to show in log", default="7"
    )
    days_int = int(default_days)
    if days_int <= 0:
        raise ValueError
    settings.default_log_days = days_int
    storage.modify_settings(settings)


def set_prompt_on_empty(storage: StorageService) -> None:
    settings = storage.settings
    prompt_value = Confirm.ask("Prompt on empty commitment?", default=True)
    settings.auto_prompt_on_empty = prompt_value
    storage.modify_settings(settings)


def set_strict_mode(storage: StorageService) -> None:
    settings = storage.settings
    strict_value = Confirm.ask("Enable strict mode?", default=settings.strict_mode)
    settings.strict_mode = strict_value
    storage.modify_settings(settings)


@app.command("set", help="Set configuration options for the ot CLI")
def set(
    ctx: typer.Context,
    key: Annotated[
        SettingsKeys,  # type: ignore
        typer.Argument(autocompletion=lambda: SETTINGS_FIELDS),
    ],
) -> None:
    storage: StorageService = ctx.obj.storage

    match key:
        case "default_log_days":
            try:
                set_default_log_days(storage)
            except ValueError:
                print_error("Please enter a valid positive integer for days.")
                raise typer.Exit(code=1)
            except StorageNotInitializedError as ex:
                print_error("Storage is not initialized. Please run 'ot init' first.")
                raise typer.Exit(code=1) from ex
            except Exception as ex:
                print_error(f"Error setting default_log_days: {ex}")
                raise typer.Exit(code=1) from ex
        case "auto_prompt_on_empty":
            try:
                set_prompt_on_empty(storage)
            except StorageNotInitializedError as ex:
                print_error("Storage is not initialized. Please run 'ot init' first.")
                raise typer.Exit(code=1) from ex
            except Exception as ex:
                print_error(f"Error setting prompt_on_empty: {ex}")
                raise typer.Exit(code=1) from ex
        case "strict_mode":
            try:
                set_strict_mode(storage)
            except StorageNotInitializedError as ex:
                print_error("Storage is not initialized. Please run 'ot init' first.")
                raise typer.Exit(code=1) from ex
            except Exception as ex:
                print_error(f"Error setting strict_mode: {ex}")
                raise typer.Exit(code=1) from ex
        case _:
            print_error(f"Setting '{key}' is not recognized.")
            raise typer.Exit(code=1)

    print_success(f"Configuration '{key}' updated successfully.")
