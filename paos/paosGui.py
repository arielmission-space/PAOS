import argparse
import logging
import os

from paos import __version__ as version
from paos import logger
from paos.gui.paosGui import PaosGui
from paos.log import addLogFile
from paos.log import setLogLevel


def main():
    logger.info("code version {}".format(version))

    parser = argparse.ArgumentParser(description="PAOS GUI {}".format(version))
    parser.add_argument(
        "-c",
        "--configuration",
        dest="conf",
        type=str,
        required=False,
        help="Input configuration file to pass",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        default=False,
        required=False,
        help="enable debug mode",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--logger",
        dest="log",
        default=False,
        required=False,
        help="save log file",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        required=False,
        default=None,
        help="Output file path",
    )

    args = parser.parse_args()
    passvalue = {"conf": args.conf, "debug": args.debug, "output": args.output}

    if args.debug:
        setLogLevel(logging.DEBUG)

    if args.log:
        if isinstance(args.output, str):
            log_filename = "{}/paos.log".format(os.path.dirname(args.output))
            logger.info("log file name: {}".format(log_filename))
            addLogFile(fname=log_filename)
        else:
            addLogFile()

    PaosGui(passvalue=passvalue)()

    logger.info("PAOS GUI exited")
    return


if __name__ == "__main__":
    main()
