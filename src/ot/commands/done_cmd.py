from typing import Annotated

import typer
from rich import print

from ot.cli import app
from ot.services import StorageService
from ot.utils import (
    DayDoneError,
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
    "done",
    help="Mark today's commitment as done (alias: d)",
    rich_help_panel=RichHelpPanel.COMPLETION.value,
)
@app.command("d", hidden=True)
def done(
    ctx: typer.Context,
    date: Annotated[
        str | None,
        typer.Option(
            help="Specify a date in YYYY-MM-DD format", callback=validate_date_string
        ),
    ] = None,
):
    storage: StorageService = ctx.obj.storage

    try:
        curr_date, data = storage.complete_day(date)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except StrictModeViolationError as ex:
        print_error(f"Cannot complete commitment due to strict mode violation: {ex}")
        raise typer.Exit(code=1) from ex
    except DayUnsetError:
        if storage.settings.auto_prompt_on_empty:
            prompt_set_commitment(storage)
        else:
            print(f"No commitment set for {date if date is not None else 'today'}")
        return
    except DayDoneError:
        print(
            f"Commitment for {date if date is not None else 'today'} is already marked"
            " as done."
        )
        return
    except Exception as ex:
        print_error(f"Error marking commitment as done: {ex}")
        raise typer.Exit(code=1) from ex

    print_success(f"Commitment for {curr_date} completed: {data.title}")
