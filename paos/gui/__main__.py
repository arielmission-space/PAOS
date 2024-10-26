import os

from shiny import run_app

from paos import logger

from paos import __pkg_name__
from paos import __version__


def main():
    app = os.path.realpath(os.path.dirname(__file__)) + "/app.py"
    logger.info(f"Running app: {__pkg_name__} v{__version__}")
    run_app(app, reload=True, launch_browser=True)


if __name__ == "__main__":
    main()
