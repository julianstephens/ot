from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

import typer

from ot.cli import app
from ot.services import Status, get_storage
from ot.utils import MONTH_FORMAT, StorageNotInitializedError, print_error


@app.command("report", help="Generate a report of commitments")
def report(
    month: Annotated[str | None, typer.Option(help="Month in YYYY-MM format")] = None,
) -> None:
    storage = get_storage()

    month = (
        month
        if month is not None
        else datetime.now(tz=ZoneInfo(storage.tz)).strftime(MONTH_FORMAT)
    )
    try:
        month_days = storage.get_month_days(month)
    except StorageNotInitializedError:
        print_error("Storage is not initialized. Please run 'ot init' first.")
        raise typer.Exit(code=1)
    except Exception as ex:
        print_error(f"Failed to retrieve data for month {month}: {ex}")
        raise typer.Exit(code=1) from ex

    days_with_commitments = [
        day for day in month_days.values() if day.title != "(no commitment)"
    ]

    print(f"Report for {month}")
    print("")

    print(f"Days with a commitment: {len(days_with_commitments)}")

    done_days = [day for day in days_with_commitments if day.status == Status.DONE]
    skipped_days = [
        day for day in days_with_commitments if day.status == Status.SKIPPED
    ]
    pending_days = [
        day for day in days_with_commitments if day.status == Status.PENDING
    ]

    print(f"  {Status.DONE.value.lower()}: {len(done_days)}")
    print(f"  {Status.SKIPPED.value.lower()}: {len(skipped_days)}")
    print(f"  {Status.PENDING.value.lower()}: {len(pending_days)}")
    print("")

    print(f"Completeion rate ({Status.DONE.value.lower()} / commitment days): ", end="")
    completion_rate = (
        (len(done_days) / len(days_with_commitments)) * 100
        if len(days_with_commitments) > 0
        else 0.0
    )
    print(f"{completion_rate:.2f}%")
