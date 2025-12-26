import logging
from typing import Annotated

import typer

from ot.utils import get_logger

app = typer.Typer(
    name="ot",
    help="CLI for choosing one non-negotiable commitment per day and tracking whether it happens",
    no_args_is_help=True,
)


class CLIContext:
    def __init__(
        self,
        verbose: Annotated[bool, typer.Option(help="Enable verbose logging")] = False,
    ):
        self.verbose: bool = False
        self.logger = get_logger(level=logging.DEBUG if verbose else logging.CRITICAL)


@app.callback()
def main(ctx: typer.Context, verbose: bool = False):
    ctx.obj = CLIContext(verbose=verbose)


import ot.commands  # noqa: E402, F401
