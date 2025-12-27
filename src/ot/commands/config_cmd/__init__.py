import typer

app = typer.Typer(
    name="config", help="Configure settings for the ot CLI", no_args_is_help=True
)

from .set_cmd import set  # noqa: E402
from .view_cmd import view  # noqa: E402

__all__ = ["app", "set", "view"]
