import datetime
import os
from copy import deepcopy as dc

import h5py
import numpy as np

from paos import __author__
from paos import __version__
from paos import logger


def remove_keys(dictionary, keys):
    """
    Removes item at specified index from dictionary.

    Parameters
    ----------
    dictionary: dict
        input dictionary
    keys:
        keys to remove from the input dictionary

    Returns
    -------
    None
        Updates the input dictionary by removing specific keys

    Examples
    -------
    >>> from paos.core.saveOutput import remove_keys
    >>> my_dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    >>> print(my_dict)
    >>> keys_to_drop = ['a', 'c', 'e']
    >>> remove_keys(my_dict, keys_to_drop)
    >>> print(my_dict)

    """
    for k in keys:
        dictionary.pop(k, "key not found")
    return


def save_recursively_to_hdf5(dictionary, outgroup):
    """
    Given a dictionary and a hdf5 object, saves the dictionary to the hdf5 object.

    Parameters
    ----------
    dictionary: dict
        a dictionary instance to be stored in a hdf5 file
    outgroup
        a hdf5 file object in which to store the dictionary instance

    Returns
    -------
    None
        Save the dictionary recursively to the hdf5 output file

    """

    for key, data in dictionary.items():
        if isinstance(data, dict):
            sub_outgroup = outgroup.create_group(key)
            save_recursively_to_hdf5(data, sub_outgroup)
        elif isinstance(data, (str, int, float, tuple)):
            outgroup.create_dataset(key, data=data)
        elif isinstance(data, np.ndarray):
            outgroup.create_dataset(
                key, data=data, shape=data.shape, dtype=data.dtype
            )
        elif isinstance(data, list):
            asciiList = [n.encode("ascii", "ignore") for n in data]
            outgroup.create_dataset(
                key, data=asciiList, shape=(len(asciiList), 1), dtype="S10"
            )
        elif data is None:
            logger.warning("key {} is None".format(key))
            continue
        else:
            logger.error("data type for {} not supported".format(key))
            raise NameError("data type not supported")


def save_info(file_name, out):
    """
    Inspired by a similar function from ExoRad2.
    Given a hdf5 file name and a hdf5 file object, saves the information about the
    paos package to the hdf5 file object. This information includes the file name,
    the time of creation, the package creator names, the package name, the package
    version, the hdf5 package version and the h5py version.

    Parameters
    ----------
    file_name: str
        the hdf5 file name for saving the POP simulation
    out
        the hdf5 file object

    Returns
    -------
    None
        Saves the paos package information to the hdf5 output file

    """

    attrs = {
        "file_name": file_name,
        "file_time": datetime.datetime.now().isoformat(),
        "creator": __author__,
        "program_name": __package__.upper(),
        "program_version": __version__,
        "HDF5_Version": h5py.version.hdf5_version,
        "h5py_version": h5py.version.version,
    }

    info_group = out.create_group("info")
    save_recursively_to_hdf5(attrs, info_group)

    return


def save_retval(retval, keys_to_keep, out):
    """
    Given the POP simulation output dictionary, the keys to store at each surface and the
    hdf5 file object, it saves the output dictionary to a hdf5 file.

    Parameters
    ----------
    retval: dict
        POP simulation output dictionary to be saved into hdf5 file
    keys_to_keep: list
        dictionary keys to store at each surface. example: ['amplitude', 'dx', 'dy']
    out: `~h5py.File`
        instance of hdf5 file object

    Returns
    -------
    None
        Saves the POP simulation output dictionary to the hdf5 output file

    """

    for index in retval.keys():

        group_name = "S{:02d}".format(index)
        logger.trace("saving {}".format(group_name))

        item = dc(retval[index])

        if item["aperture"] is not None:
            item["aperture"] = item["aperture"].__dict__

        item["ABCDs"] = item["ABCDs"].__dict__
        item["ABCDt"] = item["ABCDt"].__dict__

        if keys_to_keep is None:
            keys_to_keep = item.keys()

        keys_to_drop = [key for key in item.keys() if key not in keys_to_keep]
        remove_keys(item, keys_to_drop)

        outgroup = out.create_group(group_name)
        save_recursively_to_hdf5(item, outgroup)

    return


def save_output(retval, file_name, keys_to_keep=None, overwrite=True):
    """
    Given the POP simulation output dictionary, a hdf5 file name and the keys to store
    at each surface, it saves the output dictionary along with the paos package information
    to the hdf5 output file. If indicated, overwrites past output file.

    Parameters
    ----------
    retval: dict
        POP simulation output dictionary to be saved into hdf5 file
    file_name: str
        the hdf5 file name for saving the POP simulation
    keys_to_keep: list
        dictionary keys to store at each surface. example: ['amplitude', 'dx', 'dy']
    overwrite: bool
        if True, overwrites past output file

    Returns
    -------
    None
        Saves the POP simulation output dictionary along with the paos package information
        to the hdf5 output file

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.saveOutput import save_output
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/ini/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * wavelengths[0], parameters['grid size'],
    >>>              parameters['zoom'], fields[0], opt_chains[0])
    >>> save_output(ret_val, 'path/to/hdf5/file', keys_to_keep=['wfo', 'dx', 'dy'], overwrite=True)

    """
    assert isinstance(retval, dict), "parameter retval must be a dict"
    assert isinstance(file_name, str), "parameter file_name must be a string"
    if keys_to_keep is not None:
        assert isinstance(
            keys_to_keep, list
        ), "parameter keys_to_keep must be a list of strings"

    logger.info("saving {} started...".format(file_name))

    if overwrite:
        logger.info("removing old file")
        if os.path.isfile(file_name):
            os.remove(file_name)

    with h5py.File(file_name, "a") as out:

        save_info(file_name, out)
        save_retval(retval, keys_to_keep, out)

    logger.info("saving ended.")

    return


def save_datacube(
    retval_list, file_name, group_names, keys_to_keep=None, overwrite=True
):
    """
    Given a list of dictionaries with POP simulation output, a hdf5 file name, a list of
    identifiers to tag each simulation and the keys to store at each surface, it saves the
    outputs to a data cube along with the paos package information to the hdf5 output file.
    If indicated, overwrites past output file.

    Parameters
    ----------
    retval_list: list
        list of dictionaries with POP simulation outputs to be saved into a single hdf5 file
    file_name: str
        the hdf5 file name for saving the POP simulation
    group_names: list
        list of strings with unique identifiers for each POP simulation. example: for one
        optical chain run at different wavelengths, use each wavelength as identifier.
    keys_to_keep: list
        dictionary keys to store at each surface. example: ['amplitude', 'dx', 'dy]
    overwrite: bool
        if True, overwrites past output file

    Returns
    -------
    None
        Saves a list of dictionaries with the POP simulation outputs to a single hdf5 file
        as a datacube with group tags (e.g. the wavelengths) to identify each simulation,
        along with the paos package information.

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.saveOutput import save_datacube
    >>> from joblib import Parallel, delayed
    >>> from tqdm import tqdm
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/ini/file')
    >>> ret_val_list = Parallel(n_jobs=2)(delayed(run)(pup_diameter, 1.0e-6 * wl, parameters['grid size'],
    >>>               parameters['zoom'], fields[0], opt_chains[0]) for wl in tqdm(wavelengths))
    >>> group_tags = list(map(str, wavelengths))
    >>> save_datacube(ret_val_list, 'path/to/hdf5/file', group_tags,
    >>>               keys_to_keep=['amplitude', 'dx', 'dy'], overwrite=True)

    """

    assert isinstance(
        retval_list, list
    ), "parameter retval_list must be a list"
    assert isinstance(file_name, str), "parameter file_name must be a string"
    assert isinstance(
        group_names, list
    ), "parameter group_names must be a list of strings"

    if keys_to_keep is not None:
        assert isinstance(
            keys_to_keep, list
        ), "parameter keys_to_keep must be a list of strings"

    logger.info("Saving {} started...".format(file_name))

    if overwrite:
        logger.info("Remove old file")
        if os.path.exists(file_name) and os.path.isfile(file_name):
            os.remove(file_name)

    with h5py.File(file_name, "a") as cube:

        save_info(file_name, cube)

        for group_name, retval in zip(group_names, retval_list):

            out = cube.create_group(group_name)
            logger.trace("saving group {}".format(out))

            save_retval(retval, keys_to_keep, out)

    logger.info("Saving ended.")

    return
