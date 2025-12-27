from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

import typer
from rich import print

from ot.cli import app
from ot.services import StorageService
from ot.utils import (
    DATE_FORMAT,
    RichHelpPanel,
    StorageNotInitializedError,
    print_error,
    prompt_set_commitment,
    validate_date_string,
)


@app.command(
    "today",
    help="Display today's commitments (alias: t)",
    rich_help_panel=RichHelpPanel.COMMITMENT_MANAGEMENT.value,
)
@app.command("t", hidden=True)
def today(
    ctx: typer.Context,
    date: Annotated[
        str | None,
        typer.Option(
            "--date",
            "-d",
            help="A specific date in YYYY-MM-DD format to inspect",
            callback=validate_date_string,
        ),
    ] = None,
) -> None:
    storage: StorageService = ctx.obj.storage
    try:
        curr_date, data = storage.get_day(date)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        print_error(f"Error retrieving data for {date}: {ex}")
        raise typer.Exit(code=1) from ex

    if data is None:
        if curr_date == datetime.now(tz=ZoneInfo(storage.tz)).strftime(DATE_FORMAT):
            if storage.settings.auto_prompt_on_empty:
                try:
                    data = prompt_set_commitment(storage)
                except StorageNotInitializedError as ex:
                    print_error(
                        "Storage is not initialized. Please run 'ot init' first."
                    )
                    raise typer.Exit(code=1) from ex
                except Exception as ex:
                    print_error(f"Unable to add commitment for today: {ex}")
                    raise typer.Exit(code=1) from ex
                if data is not None:
                    print(f"{curr_date} - {data.status.value}")
                    print(f"  {data.title}")
                    return

            print(f"{curr_date} - no commitment set")
        else:
            print(f"{curr_date} - no commitment set")
        return

    print(f"{curr_date} - {data.status.value}")
    print(f"  {data.title}")
    if data.note is not None:
        print(f"  {data.note}")
