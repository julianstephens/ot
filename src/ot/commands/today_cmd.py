from typing import Annotated

import typer
from rich import print

from ot.cli import app
from ot.services import get_storage
from ot.utils import (
    StorageNotInitializedError,
    print_error,
    validate_date_string,
)


@app.command("today", help="Display today's commitments")
def today(
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
    storage = get_storage()
    try:
        curr_date, data = storage.get_day(date)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        print_error(f"Error retrieving data for {date}: {ex}")
        raise typer.Exit(code=1) from ex

    if data is None:
        print(f"{curr_date} - no commitment set")
        return

    print(f"{curr_date} - {data.status.value}")
    print(f"  {data.title}")
