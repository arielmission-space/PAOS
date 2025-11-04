import configparser
import os
import sys
from typing import List

import astropy.units as u
import numpy as np

from paos import logger
from paos.classes.abcd import ABCD
from paos.util.material import Material


def getfloat(value):
    try:
        return np.float64(value)
    except:
        return np.nan


def getaperture(aperture, _data_):
    aperture = aperture.split(",")
    aperture_shape, aperture_type = aperture[0].split()
    _data_["aperture"] = {
        "shape": aperture_shape,
        "type": aperture_type,
        "xrad": getfloat(aperture[1]),
        "yrad": getfloat(aperture[2]),
        "xc": getfloat(aperture[3]),
        "yc": getfloat(aperture[4]),
    }
    return _data_


def parse_config(filename):
    """
    Parse an ini lens file

    Parameters
    ----------
    filename: string
        full path to ini file

    Returns
    -------
    pup_diameter: float
        pupil diameter in lens units
    parameters: dict
        Dictionary with parameters defined in the section 'general' of the ini file
    field: List
        list of fields
    wavelengths: List
        list of wavelengths
    opt_chain_list: List
        Each list entry is a dictionary of the optical surfaces in the .ini file, estimated at the given wavelength.
        (Relevant only for diffractive components)

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/ini/file')

    """
    config = configparser.ConfigParser()
    filename = os.path.expanduser(filename)
    if not os.path.exists(filename) or not os.path.isfile(filename):
        logger.error(
            f"Input file {filename} does not exist or is not a file. Quitting..."
        )
        sys.exit()
    config.read(filename)

    # Parse parameters in section 'general'
    allowed_grid_size = [64, 128, 256, 512, 1024, 2048, 4096]
    allowed_zoom_val = [1, 2, 4, 8, 16]
    parameters = {
        "project": config["general"]["project"],
        "version": config["general"]["version"],
    }
    dtmp = config["general"].getint("grid_size")
    if dtmp not in allowed_grid_size:
        logger.error(f"Grid size not allowed. Allowed values are {allowed_grid_size}")
        raise ValueError(
            f"Grid size not allowed. Allowed values are {allowed_grid_size}"
        )
    parameters["grid_size"] = dtmp
    dtmp = config["general"].getint("zoom")
    if dtmp not in allowed_zoom_val:
        logger.error(f"Zoom value not allowed. Allowed values are {allowed_zoom_val}")
        raise ValueError(
            f"Zoom value not allowed. Allowed values are {allowed_zoom_val}"
        )
    elif dtmp == 1:
        logger.warning(
            "Zoom value is 1, i.e. the beam width occupies the whole of the grid width. "
            "This will result a PSF that is not Nyquist sampled."
        )
    parameters["zoom"] = dtmp

    lens_unit = config["general"].get("lens_unit", "")
    if lens_unit != "m":
        logger.error("Verify lens_unit=m in ini file")
        raise ValueError("Verify lens_unit=m in ini file")

    Tambient = config["general"].getfloat("Tambient")
    parameters["Tambient"] = Tambient
    Pambient = config["general"].getfloat("Pambient")
    parameters["Pambient"] = Pambient

    # Parse section 'wavelengths'
    wavelengths = []
    num = 1
    while True:
        _wl_ = config["wavelengths"].getfloat(f"w{num:d}")
        if _wl_:
            wavelengths.append(_wl_)
        else:
            break

        num += 1

    # Parse section 'fields'
    fields = []
    num = 1

    while True:
        _fld_ = config["fields"].get(f"f{num:d}")
        if _fld_:
            _fld_ = np.fromstring(_fld_, sep=",")
            _fld_ = np.tan(np.deg2rad(_fld_))
            fields.append({"us": _fld_[0], "ut": _fld_[1]})
        else:
            break

        num += 1

    # Parse sections 'lens_??'
    opt_chain_list = []
    pup_diameter = None  # input pupil pup_diameter
    for _wl_ in wavelengths:
        n1, n2 = None, None  # Refractive index
        glasslib = Material(_wl_, Tambient=Tambient, Pambient=Pambient)
        opt_chain = {}
        lens_num = 1
        while f"lens_{lens_num:02d}" in config:
            _data_ = {"num": lens_num}

            element = config[f"lens_{lens_num:02d}"]
            lens_num += 1

            if element.getboolean("Ignore"):
                continue

            _data_["type"] = element.get("SurfaceType", None)
            _data_["R"] = getfloat(element.get("Radius", ""))
            _data_["T"] = getfloat(element.get("Thickness", ""))
            _data_["material"] = element.get("Material", None)

            _data_["is_stop"] = element.getboolean("Stop", False)
            _data_["save"] = element.getboolean("Save", False)
            _data_["name"] = element.get("Comment", "")

            if _data_["type"] == "INIT":
                n1 = 1.0
                aperture = element.get("aperture", "").split(",")
                aperture_shape, aperture_type = aperture[0].split()
                if aperture_shape == "elliptical" and aperture_type == "aperture":
                    xpup = getfloat(aperture[2])
                    ypup = getfloat(aperture[3])
                    pup_diameter = 2.0 * max(xpup, ypup)

                continue

            if n1 is None or pup_diameter is None:
                logger.error("INIT is not the first surface in Lens Data.")
                raise ValueError("INIT is not the first surface in Lens Data.")

            if _data_["type"] == "Zernike":
                thickness = 0.0
                curvature = 0.0
                n2 = n1
                wave = 1.0e-6 * getfloat(element.get("Par1", ""))
                _data_["Zordering"] = element.get("Par2", "").lower()
                _data_["Znormalize"] = element.getboolean("Par3")
                _data_["Zradius"] = getfloat(element.get("Par4", ""))
                _data_["Zorigin"] = element.get("Par5", "x")
                _data_["Zorthonorm"] = element.get("Par6", "False").lower() == "true"
                _data_["Zindex"] = np.fromstring(
                    element.get("Zindex", ""), sep=",", dtype=np.int64
                )
                _data_["Z"] = (
                    np.fromstring(element.get("Z", ""), sep=",", dtype=np.float64)
                    * wave
                )
                aperture = element.get("aperture", "")
                if aperture:
                    getaperture(aperture, _data_)

                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            elif _data_["type"] == "Grid Sag":
                thickness = 0.0
                curvature = 0.0
                n2 = n1

                wave = 1.0e-6 * getfloat(element.get("Par1", ""))
                _data_["nx"] = getfloat(element.get("Par2", ""))
                _data_["ny"] = getfloat(element.get("Par3", ""))
                _data_["delx"] = getfloat(element.get("Par4", ""))
                _data_["dely"] = getfloat(element.get("Par5", ""))
                _data_["xdec"] = getfloat(element.get("Par6", ""))
                _data_["ydec"] = getfloat(element.get("Par7", ""))
                grid_sag_path = element.get("Par8", "")
                if not os.path.exists(grid_sag_path):
                    logger.error(f"Grid sag file does not exist: {grid_sag_path}")
                    raise ValueError(f"Grid sag file does not exist: {grid_sag_path}")
                with open(grid_sag_path, "rb") as f:
                    grid_sag = np.load(f, allow_pickle=True).item()
                assert (
                    "data" in grid_sag.keys()
                ), "The .npy file must contain a dictionary with a 'data' key"

                def input_params(key, grid_sag, _data_):
                    if key in grid_sag.keys():
                        logger.debug(
                            f"Setting {key} from grid_sag file: {grid_sag[key]}"
                        )
                        _data_[key] = grid_sag[key]

                for par in ["nx", "ny", "delx", "dely", "xdec", "ydec"]:
                    input_params(par, grid_sag, _data_)

                _data_["grid_sag"] = grid_sag["data"] * wave

                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            elif _data_["type"] == "PSD":
                thickness = 0.0
                curvature = 0.0
                n2 = n1
                _data_["A"] = getfloat(element.get("Par1", ""))
                _data_["B"] = getfloat(element.get("Par2", ""))
                _data_["C"] = getfloat(element.get("Par3", ""))
                _data_["fknee"] = getfloat(element.get("Par4", ""))
                _data_["fmin"] = getfloat(element.get("Par5", ""))
                _data_["fmax"] = getfloat(element.get("Par6", ""))
                _data_["SR"] = getfloat(element.get("Par7", ""))
                _data_["units"] = u.Unit(element.get("Par8", ""))

                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            elif _data_["type"] == "Coordinate Break":
                thickness = _data_["T"] if np.isfinite(_data_["T"]) else 0.0
                curvature = 0.0
                n2 = n1
                _data_["xdec"] = getfloat(element.get("Par1", ""))
                _data_["ydec"] = getfloat(element.get("Par2", ""))
                _data_["xrot"] = getfloat(element.get("Par3", ""))
                _data_["yrot"] = getfloat(element.get("Par4", ""))

                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            elif _data_["type"] == "Paraxial Lens":
                focal_length = getfloat(element.get("Par1", ""))
                thickness = _data_["T"] if np.isfinite(_data_["T"]) else 0.0
                curvature = 1 / focal_length if np.isfinite(focal_length) else 0.0
                n2 = n1
                aperture = element.get("aperture", "")
                if aperture:
                    getaperture(aperture, _data_)
                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            elif _data_["type"] == "ABCD":
                thickness = _data_["T"] if np.isfinite(_data_["T"]) else 0.0
                Ax = getfloat(element.get("Par1", ""))
                Bx = getfloat(element.get("Par2", ""))
                Cx = getfloat(element.get("Par3", ""))
                Dx = getfloat(element.get("Par4", ""))
                Ay = getfloat(element.get("Par5", ""))
                By = getfloat(element.get("Par6", ""))
                Cy = getfloat(element.get("Par7", ""))
                Dy = getfloat(element.get("Par8", ""))
                ABCDs = ABCD(thickness=thickness, curvature=0.0, n1=n1, n2=n1, M=1.0)
                ABCDt = ABCD(thickness=thickness, curvature=0.0, n1=n1, n2=n1, M=1.0)
                _ABCDs = np.array([[Ax, Bx], [Cx, Dx]])
                _ABCDt = np.array([[Ay, By], [Cy, Dy]])
                ABCDs.ABCD = ABCDs() @ _ABCDs
                ABCDt.ABCD = ABCDt() @ _ABCDt
                aperture = element.get("aperture", "")
                if aperture:
                    getaperture(aperture, _data_)
                _data_["ABCDt"] = ABCDt
                _data_["ABCDs"] = ABCDs

            elif _data_["type"] == "Standard":
                thickness = _data_["T"] if np.isfinite(_data_["T"]) else 0.0
                curvature = 1 / _data_["R"] if np.isfinite(_data_["R"]) else 0.0
                aperture = element.get("aperture", "")
                if aperture:
                    getaperture(aperture, _data_)

                if _data_["material"] == "MIRROR":
                    n2 = -n1
                elif _data_["material"] in glasslib.materials.keys():
                    n2 = glasslib.nmat(_data_["material"])[1] * np.sign(n1)
                else:
                    n2 = 1.0 * np.sign(n1)

                _data_["ABCDt"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )
                _data_["ABCDs"] = ABCD(
                    thickness=thickness,
                    curvature=curvature,
                    n1=n1,
                    n2=n2,
                    M=1.0,
                )

            else:
                logger.error(f"Surface Type not recognised: {str(_data_['type']):s}")
                raise ValueError(
                    f"Surface Type not recognised: {str(_data_['type']):s}"
                )

            opt_chain[_data_["num"]] = _data_
            n1 = n2

        opt_chain_list.append(opt_chain)

    return pup_diameter, parameters, wavelengths, fields, opt_chain_list
