import typer

from ot.cli import app
from ot.services import get_storage
from ot.utils import (
    DayDoneError,
    DayUnsetError,
    StorageNotInitializedError,
    print_error,
    print_success,
)


@app.command("skip", help="Mark today's commitment as skipped.")
def skip(date: str | None = None) -> None:
    storage = get_storage()

    try:
        curr_date, data = storage.complete_day(date=date, skipped=True)
    except StorageNotInitializedError as ex:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1) from ex
    except DayUnsetError:
        print(f"No commitment set for {date if date is not None else 'today'}")
        return
    except DayDoneError:
        print(
            f"Commitment for {date if date is not None else 'today'} is already marked as done."
        )
        return
    except Exception as ex:
        print_error(f"Error marking commitment as skipped: {ex}")
        raise typer.Exit(code=1) from ex

    print_success(f"Commitment for {curr_date} skipped: {data.title}")
