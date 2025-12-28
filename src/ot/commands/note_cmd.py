from typing import Annotated

import typer

from ot.cli import app
from ot.services.storage import StorageService
from ot.utils import (
    DayUnsetError,
    RichHelpPanel,
    StorageNotInitializedError,
    StrictModeViolationError,
    print_error,
    print_success,
    prompt_set_commitment,
    validate_date_string,
)


@app.command(
    "note",
    help="Add a note to the current operation (alias: n)",
    rich_help_panel=RichHelpPanel.COMMITMENT_MANAGEMENT.value,
)
@app.command("n", hidden=True)
def note(
    ctx: typer.Context,
    message: Annotated[str, typer.Argument(help="The note message to be added")],
    date: Annotated[
        str | None,
        typer.Option(
            "--date",
            "-d",
            help="A specific date in YYYY-MM-DD format to add a note to",
            callback=validate_date_string,
        ),
    ] = None,
) -> None:
    storage: StorageService = ctx.obj.storage
    try:
        storage.add_note(message=message, date=date)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except StrictModeViolationError as ex:
        print_error(f"Cannot add note due to stringent mode violation: {ex}")
        raise typer.Exit(code=1) from ex
    except DayUnsetError as ex:
        if storage.settings.auto_prompt_on_empty:
            prompt_set_commitment(storage)
            try:
                storage.add_note(message=message, date=date)
            except Exception as ex:
                print_error(f"Error adding note after setting commitment: {ex}")
                raise typer.Exit(code=1) from ex
        else:
            print_error("Cannot add note to day without a commitment set")
            raise typer.Exit(code=1) from ex
    except Exception as ex:
        print_error(f"Error adding note: {ex}")
        raise typer.Exit(code=1) from ex

    print_success(f"Note added: {message}")
