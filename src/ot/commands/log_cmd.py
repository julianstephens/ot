from datetime import datetime, timedelta
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
    validate_month_string,
)


@app.command(
    "log", help="Display commitment log", rich_help_panel=RichHelpPanel.REPORTING.value
)
def log(
    ctx: typer.Context,
    days: Annotated[
        int | None, typer.Option("--days", "-d", help="Number of days to display")
    ] = None,
    month: Annotated[
        str | None,
        typer.Option(
            "--month", "-m", help="Month to display", callback=validate_month_string
        ),
    ] = None,
) -> None:
    storage: StorageService = ctx.obj.storage

    all_days = storage.days

    if month is not None:
        try:
            month_days = storage.get_month_days(month)
        except StorageNotInitializedError:
            print_error("Storage is not initialized. Please run 'ot init' first.")
            raise typer.Exit(code=1)
        except Exception as ex:
            print_error(f"Failed to retrieve data for month {month}: {ex}")
            raise typer.Exit(code=1) from ex

        for date, day in month_days.items():
            print(f"{date}  {day.status.value}  {day.title}")
        return

    display_days = days if days is not None else storage.settings.default_log_days
    today = datetime.now(tz=ZoneInfo(storage.tz)).strftime(DATE_FORMAT)

    for i in range(display_days):
        date = (datetime.strptime(today, DATE_FORMAT) - timedelta(days=i)).strftime(
            DATE_FORMAT
        )
        data = all_days.get(date, None)
        status = data.status.value if data is not None else "-"
        title = data.title if data is not None else "(no commitment)"
        print(f"{date}  {status}  {title}")
