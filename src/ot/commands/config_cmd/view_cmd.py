import typer

from ot.services import StorageService
from ot.utils.cli import print_error

from . import app


@app.command("view", help="View current configuration settings.")
def view(ctx: typer.Context) -> None:
    storage: StorageService = ctx.obj.storage

    try:
        settings = storage.settings
    except Exception as ex:
        print_error(f"Error retrieving settings: {ex}")
        raise typer.Exit(code=1) from ex

    print("Current Configuration Settings:")
    print(f"  Default Log Days      : {settings.default_log_days}")
    print(f"  Auto Prompt on Empty  : {settings.auto_prompt_on_empty}")
    print(f"  Strict Mode           : {settings.strict_mode}")
