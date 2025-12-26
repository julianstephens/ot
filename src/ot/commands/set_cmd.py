from typing import Annotated

import typer

from ot.cli import app
from ot.services import Day, get_storage
from ot.utils import (
    DayCollisionError,
    StorageNotInitializedError,
    print_error,
    print_success,
    validate_date_string,
)


@app.command("set", help="Set today's non-negotiable commitment")
def set(
    title: Annotated[str, typer.Argument(help="Today's one thing")],
    date: Annotated[
        str | None,
        typer.Option(
            "-d",
            "--date",
            help="A specific date in YYYY-MM-DD format to set the commitment for",
            callback=validate_date_string,
        ),
    ] = None,
    force: Annotated[
        bool, typer.Option(help="Force overwrite if commitment already exists")
    ] = False,
) -> None:
    storage = get_storage()

    title = title.strip()
    if not title:
        print_error("Title cannot be empty.")
        raise typer.Exit(code=1)

    try:
        storage.add_day(data=Day(title=title), date=date, force=force)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except DayCollisionError as ex:
        if not force:
            print_error(
                "A commitment is already set for this date. Use --force to overwrite."
            )
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        print_error(f"Error setting commitment: {ex}")
        raise typer.Exit(code=1) from ex

    print_success(f"Commitment set for {date if date else 'today'}: {title}")
