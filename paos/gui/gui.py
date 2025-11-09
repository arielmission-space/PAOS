import os

import click
import rich_click as rich_click
from rich.console import Console
from rich_click import RichCommand
from shiny import run_app

from paos import __pkg_name__, __version__

rich_click.rich_click.USE_RICH_MARKUP = True
rich_click.rich_click.SHOW_ARGUMENTS = True
rich_click.rich_click.SHOW_METAVARS_COLUMN = True
rich_click.rich_click.MAX_WIDTH = None

console = Console()


@click.command(
    cls=RichCommand, context_settings={"help_option_names": ["-h", "--help"]}
)
@click.version_option(version=__version__, prog_name=f"{__pkg_name__} GUI")
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run the Shiny app in debug (auto-reload) mode.",
)
def cli(debug):
    """PAOS GUI launcher."""

    console.rule(f"[bold magenta]{__pkg_name__} GUI v{__version__}")
    app = os.path.realpath(os.path.dirname(__file__)) + "/app.py"
    run_app(app, reload=bool(debug), launch_browser=True, dev_mode=False)


def main():
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
