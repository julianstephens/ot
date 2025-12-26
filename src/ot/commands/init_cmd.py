from typing import Annotated

import typer

from ot.cli import app
from ot.services import get_storage
from ot.utils import (
    StorageAlreadyInitializedError,
    print_error,
    print_success,
    print_warning,
)


@app.command("init", help="Initialize storage for commitments")
def init(
    ctx: typer.Context,
    force: Annotated[
        bool, typer.Option(help="Overwrite stored data if it already exists")
    ] = False,
):
    if force:
        print_warning(
            "Force option enabled: existing storage will be overwritten if it exists."
        )

    ctx.obj.logger.debug("getting storage service...")
    storage = get_storage()
    ctx.obj.logger.debug("storage service obtained.")

    try:
        ctx.obj.logger.debug("starting storage initialization...")
        storage.initialize(force=force)
        ctx.obj.logger.debug("storage initialization completed.")
    except StorageAlreadyInitializedError as ex:
        ctx.obj.logger.exception("storage already initialized.")
        print_error("Storage is already initialized. Use --force to overwrite.")
        raise typer.Exit(code=1) from ex
    except Exception as ex:
        ctx.obj.logger.exception("storage initialization failed.")
        print_error("Failed to initialize storage.")
        raise typer.Exit(code=1) from ex

    print_success("Storage initialized successfully.")
