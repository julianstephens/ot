import typer
from rich import print

from ot.cli import app
from ot.services import StorageService
from ot.utils import (
    RichHelpPanel,
    Status,
    StorageNotInitializedError,
    print_success,
    prompt_set_commitment,
)


@app.command(
    name="nudge",
    help="Remind about today's commitment (alias: r)",
    rich_help_panel=RichHelpPanel.COMMITMENT_MANAGEMENT.value,
)
@app.command("r", hidden=True)
def nudge(ctx: typer.Context):
    storage: StorageService = ctx.obj.storage

    try:
        _, day = storage.get_day()
    except StorageNotInitializedError as ex:
        print("Storage is not initialized. Please run 'ot config init' first.")
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
        raise typer.Exit(code=1) from ex

    if day is None:
        if storage.settings.auto_prompt_on_empty:
            day = prompt_set_commitment(storage)
        if day is None:
            print("No commitment set for today.")
        else:
            print_success(f"Commitment set: {day.title}")
        return

    if day.status == Status.PENDING:
        print(f"Pending today: '{day.title}'")
        return
