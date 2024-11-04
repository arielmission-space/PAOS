import os
import sys
import time

from shiny import run_app

from paos import __pkg_name__
from paos import __version__

from paos import logger
from paos.log.logger import setLogLevel
from paos.log.logger import addLogFile


def main():
    """
    This function is the entry point for the command line interface of the PAOS GUI.
    It sets up the logging and the app path, and then runs the shiny app.

    Optional commands
    -----------------
    -d, --debug:
        run the app in debug mode.

    -l, --logfile:
        redirect the log output to a file.

    -h, --help:
        show this help message and exit.
    """
    if "-h" in sys.argv or "--help" in sys.argv:
        print(main.__doc__)
        sys.exit(0)

    reload = False
    if "-d" in sys.argv or "--debug" in sys.argv:
        reload = True

    if "-l" in sys.argv or "--logfile" in sys.argv:
        fname = f"{__pkg_name__}_{time.strftime('%Y%m%d_%H%M%S')}.log"
        logger.debug(f"Logging to file {fname}")
        addLogFile(fname=fname)

    app = os.path.realpath(os.path.dirname(__file__)) + "/app.py"
    logger.info(f"Running app: {__pkg_name__} GUI v{__version__}")
    run_app(app, reload=reload, launch_browser=True, dev_mode=False)


if __name__ == "__main__":
    main()
