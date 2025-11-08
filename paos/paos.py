import os
from pathlib import Path

import click
import rich_click as rich_click
from rich.console import Console
from rich_click import RichCommand

from paos import __pkg_name__, __version__, logger
from paos.core.pipeline import pipeline
from paos.log.logger import addLogFile, setLogLevel

rich_click.rich_click.USE_RICH_MARKUP = True
rich_click.rich_click.SHOW_ARGUMENTS = True
rich_click.rich_click.SHOW_METAVARS_COLUMN = True
rich_click.rich_click.MAX_WIDTH = None

console = Console()


@click.command(
    cls=RichCommand, context_settings={"help_option_names": ["-h", "--help"]}
)
@click.version_option(version=__version__, prog_name=__pkg_name__)
@click.option(
    "-c",
    "--configuration",
    "conf",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Input configuration file to pass.",
)
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(dir_okay=False, path_type=str),
    default=None,
    show_default=True,
    help="Output file. Defaults to <configuration>.h5 next to the input file.",
)
@click.option(
    "-lo",
    "--light_output",
    "light_output",
    is_flag=True,
    default=False,
    show_default=True,
    help="If enabled, saves only the last optical surface.",
)
@click.option(
    "-wfe",
    "--wfe_simulation",
    "wfe",
    type=str,
    default=None,
    show_default=True,
    help=(
        "WFE realisation file and column with Zernike coefficients to simulate an "
        "aberrated wavefront, e.g. 'path/to/wfe_realization.csv,0'."
    ),
)
@click.option(
    "-keys",
    "--store_keys",
    "store_keys",
    type=str,
    default="amplitude,dx,dy,wl",
    show_default=True,
    help="Comma separated list with the output dictionary keys to save.",
)
@click.option(
    "-n",
    "--n_jobs",
    "n_jobs",
    type=int,
    default=1,
    show_default=True,
    help="Number of threads for parallel processing.",
)
@click.option(
    "-p",
    "--plot",
    is_flag=True,
    default=False,
    show_default=True,
    help="Save output plots.",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable debug mode.",
)
@click.option(
    "-l",
    "--logger",
    "logfile",
    is_flag=True,
    default=False,
    show_default=True,
    help="Save a log file next to the output.",
)
def cli(
    conf,
    output,
    light_output,
    wfe,
    store_keys,
    n_jobs,
    plot,
    debug,
    logfile,
):
    """PAOS CLI - Physical Optics Simulator."""
    setLogLevel("INFO")

    if output is None:
        output = os.path.join(os.path.dirname(conf), f"{Path(conf).stem}.h5")

    passvalue = {
        "conf": conf,
        "output": output,
        "light_output": light_output,
        "wfe": wfe,
        "store_keys": store_keys,
        "n_jobs": n_jobs,
        "save": True,
        "plot": plot,
        "debug": debug,
    }

    output_dir = os.path.dirname(output)
    if output_dir and not os.path.isdir(output_dir):
        logger.info(f"folder {output_dir} not found in directory tree. Creating..")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    if debug:
        setLogLevel("DEBUG")

    if logfile:
        if isinstance(output, str):
            input_fname = Path(conf).stem
            fname = f"{os.path.dirname(output)}/{input_fname}.log"
            logger.info(f"log file name: {fname}")
            addLogFile(fname=fname)
        else:
            addLogFile()

    console.rule(f"[bold cyan]{__pkg_name__} v{__version__}")
    logger.log("Announce", f"Starting {__pkg_name__} v{__version__}...")

    pipeline(passvalue)

    logger.info(f"{__pkg_name__} simulation completed.")
    console.print(f":sparkles: [bold green]{__pkg_name__} simulation completed.[/]")


def main():
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
