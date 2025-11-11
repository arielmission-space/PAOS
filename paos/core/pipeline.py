import gc
import os
import time
import warnings
from pathlib import Path

import numpy as np
from astropy.io import ascii
from joblib import Parallel, delayed
from rich.console import Console
from tqdm import TqdmExperimentalWarning
from tqdm.rich import tqdm

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

from paos import logger
from paos.core.parseConfig import parse_config
from paos.core.plot import plot_pop
from paos.core.raytrace import raytrace
from paos.core.run import run
from paos.core.saveOutput import save_datacube
from paos.log.logger import addLogFile, setLogLevel

console = Console()
RULE = {"style": "dim white", "characters": "╌"}


def pipeline(passvalue):
    """
    Pipeline to run a POP simulation and save the results, given the input dictionary.
    This pipeline parses the lens file, performs a diagnostic ray tracing (optional),
    sets up the optical chain for the POP run automatizing the input of an aberration (optional),
    runs the POP in parallel or using a single thread and produces an output where all
    (or a subset) of the products are stored. If indicated, the output includes plots.

    Parameters
    ------------
    passvalue: dict
        input dictionary for the simulation

    Returns
    -------
    None or dict or list of dict
        If indicated, returns the simulation output dictionary or a list with a dictionary for
        each simulation. Otherwise, returns None.

    Examples
    --------

    >>> from paos.core.pipeline import pipeline
    >>> pipeline(passvalue={'conf':'path/to/conf/file',
    >>>                     'output': 'path/to/output/file',
    >>>                     'save': True,
    >>>                     'plot': True,
    >>>                     'loglevel': 'debug',
    >>>                     'n_jobs': 2,
    >>>                     'store_keys': 'amplitude,dx,dy,wl',
    >>>                     'return': False})
    """

    logger.debug("Set up logger")

    if "loglevel" in passvalue.keys():
        if passvalue["loglevel"] in ["debug", "trace", "info"]:
            setLogLevel(passvalue["loglevel"].upper())
        else:
            logger.error("loglevel shall be one of debug, trace or info")

    if "logfile" in passvalue.keys():
        logger.info(f"log file name: {passvalue['logfile']}")
        addLogFile(fname=passvalue["logfile"])

    logger.debug("Set pipeline defaults")

    if "save" not in passvalue.keys():
        passvalue["save"] = True
    if "plot" not in passvalue.keys():
        passvalue["plot"] = False
    if "n_jobs" not in passvalue.keys():
        passvalue["n_jobs"] = 1
    if "store_keys" not in passvalue.keys():
        passvalue["store_keys"] = "amplitude,dx,dy,wl"
    if "return" not in passvalue.keys():
        passvalue["return"] = False

    logger.debug("passvalue keys are {}".format(list(passvalue.keys())))

    console.rule(**RULE)
    logger.info("Parse lens file")
    pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(
        passvalue["conf"]
    )

    if "debug" in passvalue.keys() and passvalue["debug"]:
        console.rule(**RULE)
        logger.debug("Perform a diagnostic ray tracing")
        raytrace(fields[0], opt_chains[0])

    console.rule(**RULE)
    logger.info("Set up the POP")

    logger.debug(f"Wavelengths: {wavelengths}")
    logger.debug(f"Using field f1 = {fields[0]} from configuration file")
    field = fields[0]
    logger.debug("Set up the optical chain for the POP run")

    optc = {}
    for idx, opt_chain in enumerate(opt_chains):
        optc[idx] = {}
        for key, item in opt_chain.items():
            optc[idx][key] = item
            if "light_output" in passvalue.keys() and passvalue["light_output"] is True:
                optc[idx][key]["save"] = False
                if item["name"] == "IMAGE_PLANE":
                    optc[idx][key]["save"] = True
            if (
                item["name"] == "Z1"
                and "wfe" in passvalue.keys()
                and passvalue["wfe"] is not None
            ):
                wfe_file, column = passvalue["wfe"].split(",")
                logger.debug(f"Wfe realization file: {wfe_file}; column: {column}")
                wfe = ascii.read(wfe_file)
                optc[idx][key]["Zordering"] = "standard"
                optc[idx][key]["Znormalize"] = "True"
                optc[idx][key]["Zorigin"] = "x"
                Ck = wfe["col%i" % (float(column) + 4)].data * 1.0e-9
                optc[idx][key]["Z"] = np.append(np.zeros(3), Ck)
                logger.debug(f"Wfe coefficients: {optc[idx][key]['Z']}")

    console.rule(**RULE)
    logger.info("Run the POP")

    if passvalue["n_jobs"] > 1:
        logger.info("Start POP in parallel...")
    else:
        logger.info("Start POP using a single thread...")

    start_time = time.time()
    retval = Parallel(n_jobs=passvalue["n_jobs"])(
        delayed(run)(
            pup_diameter,
            1.0e-6 * wavelengths[key],
            parameters["grid_size"],
            parameters["zoom"],
            field,
            opt_chain,
        )
        for key, opt_chain in tqdm(optc.items())
    )
    end_time = time.time()
    logger.info(f"POP completed in {(end_time - start_time):g} s")
    _ = gc.collect()

    group_tags = list(map(str, wavelengths))
    logger.debug(f"group tags: {group_tags}")
    if passvalue["save"]:
        console.rule(**RULE)
        logger.info(
            f"Save POP simulation output .h5 file to {Path(passvalue['output']).resolve()}"
        )
        store_keys = None
        if passvalue["store_keys"] is not None:
            store_keys = passvalue["store_keys"].split(",")
        logger.debug(f"Store keys: {store_keys}")
        save_datacube(
            retval,
            passvalue["output"],
            group_tags,
            keys_to_keep=store_keys,
            overwrite=True,
        )

    if passvalue["plot"]:
        console.rule(**RULE)
        logger.info("Save POP simulation output plot")

        plots_dir = Path(passvalue["output"]).parent / "plots"
        if not os.path.isdir(plots_dir):
            logger.warning(
                f"folder {Path(plots_dir).resolve()} not found in directory tree. Creating.."
            )
            Path(plots_dir).mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        fig_name = "".join(
            [
                os.path.basename(os.path.splitext(passvalue["conf"])[0]),
                "_pop_plot",
            ]
        )
        fig_name = os.path.join(plots_dir, fig_name)

        logger.debug(f"fig base name: {fig_name}")

        _ = Parallel(n_jobs=passvalue["n_jobs"])(
            delayed(plot_pop)(
                _retval_,
                ima_scale="log",
                ncols=2,
                figname="".join([fig_name, f"_{tag}_um", ".png"]),
            )
            for _retval_, tag in zip(tqdm(retval), group_tags)
        )
        end_time = time.time()
        logger.info(f"Plotting completed in {(end_time - start_time):g} s")

    if not passvalue["return"]:
        console.rule(**RULE)
        logger.debug("Not returning output dict")
        return

    logger.debug("Returning output dict")
    return retval
