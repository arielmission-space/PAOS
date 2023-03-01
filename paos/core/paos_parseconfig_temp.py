import os
import sys

import numpy as np
import pandas as pd

from paos import logger
from paos.classes.abcd import ABCD
from paos.util.material import Material


def read_config(filename):
    """
    Given the input file name, it parses the simulation parameters and returns a dictionary.
    The input file is an Excel spreadsheet which contains three data sheets named 'general',
    'LD' and 'field'. 'general' contains the simulation wavelength, grid size and zoom, defined
    as the ratio of grid size to initial beam size in unit of pixel. 'LD' is the lens data and
    contains the sequence of surfaces for the simulation mimicking a Zemax lens data editor:
    supported surfaces include coordinate break, standard surface, obscuration, zernike,
    paraxial lens, slit and prism.

    Returns
    -------
    dict
        dictionary with the parsed input parameters for the simulation.

    Examples
    --------

    >>> from paos.paos_parseconfig_temp import read_config
    >>> simulation_parameters = read_config('path/to/conf/file')

    """

    parameters = {"general": {}, "LD": None, "field": {}}

    if not os.path.exists(filename) or not os.path.isfile(filename):
        logger.error(
            "Input file {} does not exist or is not a file. Quitting..".format(
                filename
            )
        )
        sys.exit()

    with pd.ExcelFile(filename, engine="openpyxl") as xls:
        wb = pd.read_excel(xls, "General")
        for key, val in zip(wb["INIT"], wb["Value"]):
            parameters["general"][key] = val
        wb = pd.read_excel(xls, "Lens Data")
        parameters["LD"] = wb

        wb = pd.read_excel(xls, "Fields")
        for field, x, y in zip(wb["Field"], wb["X"], wb["Y"]):
            parameters["field"][str(field)] = {
                "us": np.tan(np.deg2rad(x)),
                "ut": np.tan(np.deg2rad(y)),
            }

    return parameters


def ParseConfig(filename):
    """
    It parses the input file name and returns the input pupil diameter and three dictionaries for the simulation:
    one for the general parameters, one for the input fields and one for the optical chain.

    Returns
    -------
    dict
        the input pupil diameter, the general parameters, the input fields and the optical chain.

    Examples
    --------

    >>> from paos.paos_parseconfig_temp import ParseConfig
    >>> pupil_diameter, general, fields, optical_chain = ParseConfig('path/to/conf/file')

    """
    parameters = read_config(filename)

    wl = parameters["general"]["wavelength"]
    glasslib = Material(wl)

    n1 = None  # Refractive index
    pup_diameter = None  # input pupil pup_diameter

    opt_chain = {}

    for index, element in parameters["LD"].iterrows():

        chain_step = element["Surface num"]

        if element["Ignore"] == 1:
            continue

        if element["Surface Type"] == "INIT":
            n1 = 1.0  # propagation starts in free space
            xpup = element["XRADIUS"]
            ypup = element["YRADIUS"]

            if np.isfinite(xpup) and np.isfinite(ypup):
                pup_diameter = 2.0 * max(xpup, ypup)
            else:
                logger.error("Pupil wrongly defined")
                raise ValueError("Pupil wrongly defined")

            continue

        if n1 is None or pup_diameter is None:
            logger.error("INIT is not the first surface in Lens Data.")
            raise ValueError("INIT is not the first surface in Lens Data.")

        _data_ = {
            "num": element["Surface num"],
            "type": element["Surface Type"],
            "is_stop": True if element["Stop"] == 1 else False,
            "save": True if element["Save"] == 1 else False,
            "name": element["Comment"],
            "R": element["Radius"],
            "T": element["Thickness"],
            "material": element["Material"],
            "xrad": element["XRADIUS"],
            "yrad": element["YRADIUS"],
            "xdec": element["XDECENTER"],
            "ydec": element["YDECENTER"],
            "xrot": element["TiltAboutX"],
            "yrot": element["TiltAboutY"],
            "Mx": element["MagnificationX"],
            "My": element["MagnificationY"],
        }

        if element["Surface Type"] == "Zernike":
            sheet, stmp = element["Range"].split(".")
            colrange = "".join([i for i in stmp if not i.isdigit()])
            rowrange = "".join(
                [i for i in stmp if i.isdigit() or i == ":"]
            ).split(":")
            rowstart = int(rowrange[0])
            nrows = int(rowrange[1]) - rowstart + 1

            with pd.ExcelFile(filename, engine="openpyxl") as xls:
                wb0 = pd.read_excel(xls, sheet, header=None, nrows=3)
                wb1 = pd.read_excel(
                    xls,
                    sheet,
                    skiprows=rowstart - 1,
                    usecols="A," + colrange,
                    nrows=nrows,
                    header=None,
                )
            _data_.update(
                {
                    "Zindex": wb1[0].to_numpy(dtype=int),
                    "Z": wb1[1].to_numpy(dtype=float),
                    "Zradius": max(_data_["xrad"], _data_["yrad"]),
                    "Zwavelength": float(wb0[1][0]),
                    "Zordering": wb0[1][1].lower(),
                    "Znormalize": wb0[1][2],
                    "ABCDt": ABCD(),
                    "ABCDs": ABCD(),
                    "Zorigin": "x"  # this is the default origin for the angles: from x axis, counted
                    # positive counterclockwise
                }
            )

            opt_chain[chain_step] = _data_

        else:
            thickness = _data_["T"] if np.isfinite(_data_["T"]) else 0.0
            Mx = _data_["Mx"] if np.isfinite(_data_["Mx"]) else 1.0
            My = _data_["My"] if np.isfinite(_data_["My"]) else 1.0
            if _data_["type"] == "Coordinate Break":
                C = 0.0
                n2 = n1
            elif _data_["type"] == "Paraxial Lens":
                C = 1.0 / _data_["R"] if np.isfinite(_data_["R"]) else 0.0
                n2 = n1
            elif _data_["type"] in ("Standard", "Slit", "Obscuration"):
                C = 1.0 / _data_["R"] if np.isfinite(_data_["R"]) else 0.0
                if _data_["material"] == "MIRROR":
                    n2 = -n1
                elif _data_["material"] in glasslib.materials.keys():
                    n2 = glasslib.nmat(_data_["material"])[1] * np.sign(n1)
                else:
                    n2 = 1.0 * np.sign(n1)
            elif _data_["type"] == "Prism":
                C = 0.0
                n2 = n1
            else:
                logger.error(
                    "Surface Type not recognised: {:s}".format(
                        str(_data_["type"])
                    )
                )
                raise ValueError(
                    "Surface Type not recognised: {:s}".format(
                        str(_data_["type"])
                    )
                )

            _data_["ABCDt"] = ABCD(thickness, C, n1, n2, My)
            _data_["ABCDs"] = ABCD(thickness, C, n1, n2, Mx)

            logger.debug(
                "name: {}, curvature: {:4f}, thickness: {:.4f}, material: {}, n1: {:4f}, n2: {:4f}".format(
                    _data_["name"],
                    _data_["ABCDt"].power,
                    _data_["ABCDt"].thickness,
                    _data_["material"],
                    n1,
                    n2,
                )
            )

            n1 = n2
            opt_chain[chain_step] = _data_

    return pup_diameter, parameters["general"], parameters["field"], opt_chain
