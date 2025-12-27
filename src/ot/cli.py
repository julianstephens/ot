import logging
from typing import Annotated

import typer

from ot.services import get_storage
from ot.utils import get_logger

app = typer.Typer(
    name="ot",
    help=(
        "CLI for choosing one non-negotiable commitment per day and tracking whether it"
        " happens"
    ),
    no_args_is_help=True,
)


class CLIContext:
    def __init__(
        self,
        debug=False,
    ):
        self.debug: bool = False
        self.log_level = logging.DEBUG if debug else logging.CRITICAL
        self.logger = get_logger(level=self.log_level)
        self.storage = get_storage(log_level=self.log_level)


@app.callback()
def main(
    ctx: typer.Context,
    debug: Annotated[bool, typer.Option(help="Enable debug logging")] = False,
):
    ctx.obj = CLIContext(debug=debug)


import ot.commands  # noqa: E402, F401
from ot.commands.config_cmd import app as cfg_app  # noqa: E402

app.add_typer(cfg_app)
