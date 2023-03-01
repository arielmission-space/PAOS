import logging

import paos.__version__ as version
from paos import logger
from paos.core.pipeline import pipeline
from paos.log import addLogFile
from paos.log import setLogLevel


def main():
    import os
    from pathlib import Path
    import argparse

    parser = argparse.ArgumentParser(description="PAOS {}".format(version))
    parser.add_argument(
        "-c",
        "--configuration",
        dest="conf",
        type=str,
        required=True,
        help="Input configuration file to pass",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        required=False,
        default=None,
        help="Output file",
    )
    parser.add_argument(
        "-lo",
        "--light_output",
        dest="light_output",
        required=False,
        default=False,
        help="If True, saves only at last optical surface",
        action="store_true",
    )
    parser.add_argument(
        "-wl",
        "--wavelength",
        dest="wavelengths",
        type=str,
        default=None,
        required=False,
        help="A list of wavelengths at which to run "
        "the simulation, in micron. ex: 1.95,3.9",
    )
    parser.add_argument(
        "-wlg",
        "--wavelength_grid",
        dest="wl_grid",
        type=str,
        default=None,
        required=False,
        help="A list with wl_min, wl_max, R to build "
        "a wavelength grid at which to run the simulation, "
        "in micron. ex: 1.95,3.9,100",
    )
    parser.add_argument(
        "-wfe",
        "--wfe_simulation",
        dest="wfe",
        type=str,
        default=None,
        required=False,
        help="Supported wfe realization file and user defined "
        "column with the zernike coefficients "
        "to simulate an aberrated wavefront. "
        "ex: path/to/wfe_realization.csv,0",
    )
    parser.add_argument(
        "-keys",
        "--keys_to_keep",
        dest="store_keys",
        type=str,
        default="amplitude,dx,dy,wl",
        required=False,
        help="A list with the output dictionary keys to save",
    )
    parser.add_argument(
        "-n",
        "--nThreads",
        dest="n_jobs",
        default=1,
        type=int,
        required=False,
        help="number of threads for parallel processing",
    )
    parser.add_argument(
        "-p",
        "--plot",
        dest="plot",
        default=False,
        required=False,
        help="save output plots",
        action="store_true",
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

    args = parser.parse_args()

    if args.output is None:
        """Defaults to the same directory as the configuration file.
        The output file name is the same as the configuration file name with the extension .h5"""
        args.output = os.path.join(
            os.path.dirname(args.conf), Path(args.conf).stem + ".h5"
        )

    passvalue = {
        "conf": args.conf,
        "output": args.output,
        "light_output": args.light_output,
        "wavelengths": args.wavelengths,
        "wl_grid": args.wl_grid,
        "wfe": args.wfe,
        "store_keys": args.store_keys,
        "n_jobs": args.n_jobs,
        "plot": args.plot,
        "debug": args.debug,
    }

    if not os.path.isdir(os.path.dirname(args.output)):
        logger.info(
            "folder {} not found in directory tree. Creating..".format(
                os.path.dirname(args.output)
            )
        )
        Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

    if args.debug:
        setLogLevel(logging.DEBUG)
    if args.log:
        if isinstance(args.output, str):
            input_fname = Path(args.conf).stem
            fname = f"{os.path.dirname(args.output)}/{input_fname}.log"
            logger.info("log file name: {}".format(fname))
            addLogFile(fname=fname)
        else:
            addLogFile()

    logger.info("code version {}".format(version))
    pipeline(passvalue)

    logger.info("Paos simulation completed.")

    return


if __name__ == "__main__":
    main()
