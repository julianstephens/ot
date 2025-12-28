from typing import Annotated

import typer
from rich import print

from ot.cli import app
from ot.services import StorageService
from ot.utils import RichHelpPanel, StorageNotInitializedError


@app.command(
    name="edit",
    help="Edit an existing commitment's title (alias: e)",
    rich_help_panel=RichHelpPanel.COMMITMENT_MANAGEMENT.value,
)
@app.command("e", hidden=True)
def edit(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="New title for the commitment")],
    date: Annotated[
        str | None, typer.Option("--date", "-d", help="Date of the commitment to edit")
    ] = None,
):
    storage: StorageService = ctx.obj.storage

    try:
        curr_date, _ = storage.modify_day(new_title=title, date=date)
        date_str = curr_date if date is not None else "today"
        print(f"Commitment for {date_str} updated to: {title}")
    except StorageNotInitializedError as ex:
        print("Storage is not initialized. Please run 'ot config init' first.")
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        print(f"Failed to edit commitment: {ex}")
        raise typer.Exit(code=1) from ex
