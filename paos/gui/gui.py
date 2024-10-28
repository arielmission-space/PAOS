import os

from shiny import run_app

from paos import logger

from paos import __pkg_name__
from paos import __version__


def main():
    """
    This function is the entry point for the command line interface of the PAOS GUI.
    It sets up the logging and the app path, and then runs the shiny app.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    app = os.path.realpath(os.path.dirname(__file__)) + "/app.py"
    logger.info(f"Running app: {__pkg_name__} GUI v{__version__}")
    run_app(app, reload=True, launch_browser=True)


if __name__ == "__main__":
    main()
