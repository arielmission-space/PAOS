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
    "-s",
    "--save/--no-save",
    "save",
    default=True,
    show_default=True,
    help="Write results to an .h5 file. Use --no-save to skip.",
)
@click.option(
    "-p",
    "--plot/--no-plot",
    "plot",
    default=True,
    show_default=True,
    help="Generate and save output plots. Use --no-plot to skip.",
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
    save,
    plot,
    debug,
    logfile,
):
    """PAOS launcher."""
    setLogLevel("DEBUG" if debug else "INFO")

    if not conf.lower().endswith(".ini"):
        logger.error("Configuration file must be a .ini file")
        return

    conf_name = Path(conf).stem

    if output is not None and not output.lower().endswith(".h5"):
        logger.error("Output file must be an .h5 file")
        return

    if output is None:
        logger.warning("No output file provided, setting default next to input file")
        output = Path(conf).parent / f"{conf_name}.h5"

    output_path = Path(output)
    output_dir = output_path.parent

    if not output_dir.exists():
        logger.warning(
            f"folder {output_dir.resolve()} not found in directory tree. Creating.."
        )
        output_dir.mkdir(parents=True, exist_ok=True)

    if logfile:
        logfile_name = output_dir / f"{conf_name}.log"
        logger.info(f"Logging to file: {logfile_name.resolve()}")
        addLogFile(fname=str(logfile_name))

    passvalue = {
        "conf": conf,
        "output": str(output_path),
        "light_output": light_output,
        "wfe": wfe,
        "store_keys": store_keys,
        "n_jobs": n_jobs,
        "save": save,
        "plot": plot,
        "debug": debug,
    }

    console.rule(f":rocket: [bold cyan]Starting {__pkg_name__} v{__version__} :rocket:")
    logger.log("Announce", f"Starting {__pkg_name__} v{__version__}")

    pipeline(passvalue)

    logger.log("Announce", f"{__pkg_name__} simulation completed")
    console.rule(
        f":sparkles: [bold cyan]{__pkg_name__} simulation completed[/] :sparkles:"
    )


def main():
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
