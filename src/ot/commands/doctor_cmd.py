import typer
from rich import print

from ot.cli import app
from ot.services import StorageService
from ot.utils import print_success


@app.command(name="doctor", help="Check and repair the storage state")
def doctor(ctx: typer.Context) -> None:
    storage: StorageService = ctx.obj.storage

    remedy, message, exit_code = storage.doctor()
    ctx.obj.logger.debug(
        f"doctor command result: remedy={remedy}, exit_code={exit_code}"
    )

    if exit_code == 0:
        print_success(message)
        return

    print(message)
    raise typer.Exit(code=exit_code)
