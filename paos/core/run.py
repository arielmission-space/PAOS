import gc
from copy import deepcopy

import numpy as np

from paos import logger
from paos.classes.abcd import ABCD
from paos.classes.wfo import WFO
from paos.core.coordinateBreak import coordinate_break


def push_results(wfo):
    retval = {
        "amplitude": wfo.amplitude,
        "wz": wfo.wz,
        "distancetofocus": wfo.distancetofocus,
        "fratio": wfo.fratio,
        "phase": wfo.phase,
        "dx": wfo.dx,
        "dy": wfo.dy,
        "wfo": wfo.wfo,
        "wl": wfo.wl,
        "extent": wfo.extent,
    }

    return retval


def run(pupil_diameter, wavelength, gridsize, zoom, field, opt_chain):
    """
    Run the POP.

    Parameters
    ----------
    pupil_diameter: scalar
        input pupil diameter in meters
    wavelength: scalar
        wavelength in meters
    gridsize: scalar
        the size of the simulation grid. It has to be a power of 2
    zoom: scalar
        zoom factor
    field: dictionary
        contains the slopes in the tangential and sagittal planes as field={'vt': slopey, 'vs': slopex}
    opt_chain: list
        the list of the optical elements parsed by paos.core.parseConfig.parse_config

    Returns
    -------
    out: dict
        dictionary containing the results of the POP

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.plot import simple_plot
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/conf/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * wavelengths[0], parameters['grid_size'], parameters['zoom'], fields[0], opt_chains[0])

    """

    assert isinstance(opt_chain, dict), "opt_chain must be a dict"

    retval = {}

    vt = np.array([0.0, field["ut"]])
    vs = np.array([0.0, field["us"]])

    ABCDt = ABCD()
    ABCDs = ABCD()

    wfo = WFO(pupil_diameter, wavelength, gridsize, zoom)

    for index, item in opt_chain.items():

        logger.trace("Surface: {}".format(item["name"]))

        if item["type"] == "Coordinate Break":
            logger.trace("Apply coordinate break.")
            vt, vs = coordinate_break(
                vt,
                vs,
                item["xdec"],
                item["ydec"],
                item["xrot"],
                item["yrot"],
                0.0,
            )

        _retval_ = {"aperture": None}

        # Check if aperture needs to be applied
        if "aperture" in item:
            xdec = (
                item["aperture"]["xc"]
                if np.isfinite(item["aperture"]["xc"])
                else vs[0]
            )
            ydec = (
                item["aperture"]["yc"]
                if np.isfinite(item["aperture"]["yc"])
                else vt[0]
            )
            xrad = item["aperture"]["xrad"]
            yrad = item["aperture"]["yrad"]
            xrad *= np.sqrt(1 / (vs[1] ** 2 + 1))
            yrad *= np.sqrt(1 / (vt[1] ** 2 + 1))
            xaper = xdec - vs[0]
            yaper = ydec - vt[0]

            obscuration = (
                False if item["aperture"]["type"] == "aperture" else True
            )

            if np.all(np.isfinite([xrad, yrad])):
                logger.trace("Apply aperture")
                aper = wfo.aperture(
                    xaper,
                    yaper,
                    hx=xrad,
                    hy=yrad,
                    shape=item["aperture"]["shape"],
                    obscuration=obscuration,
                )
                _retval_["aperture"] = aper

        # if item['type'] in ['Standard', 'Paraxial Lens', 'Slit', 'Obscuration']:
        #     xdec = item['xdec'] if np.isfinite(item['xdec']) else vs[0]
        #     ydec = item['ydec'] if np.isfinite(item['ydec']) else vt[0]
        #     xrad = item['xrad']
        #     yrad = item['yrad']
        #     xrad *= np.sqrt(1 / (vs[1] ** 2 + 1))
        #     yrad *= np.sqrt(1 / (vt[1] ** 2 + 1))
        #     xaper = xdec - vs[0]
        #     yaper = ydec - vt[0]
        #
        #     aperture_shape = 'rectangular' if item['type'] == 'Slit' else 'elliptical'
        #     obscuration = True if item['type'] == 'Obscuration' else False
        #     if np.all(np.isfinite([xrad, yrad])):
        #         logger.trace('Apply aperture')
        #         aper = wfo.aperture(xaper, yaper, hx=xrad, hy=yrad,
        #                             shape=aperture_shape, obscuration=obscuration)
        #         _retval_['aperture'] = aper

        # Check if this is a stop surface
        if item["is_stop"]:
            logger.trace("Apply stop")
            wfo.make_stop()

        if item["type"] == "Zernike":
            radius = (
                item["Zradius"] if np.isfinite(item["Zradius"]) else wfo.wz
            )
            wfo.zernikes(
                item["Zindex"],
                item["Z"],
                item["Zordering"],
                item["Znormalize"],
                radius,
                origin=item["Zorigin"],
            )

        _retval_.update(push_results(wfo))

        Ms = item["ABCDs"].M
        Mt = item["ABCDt"].M

        fl = (
            np.inf
            if (item["ABCDt"].power == 0)
            else item["ABCDt"].cout / item["ABCDt"].power
        )
        T = item["ABCDt"].cout * item["ABCDt"].thickness
        n1n2 = item["ABCDt"].n1n2
        logger.trace("n1n2: {:.4f}".format(n1n2))

        if Mt != 1.0 or Ms != 1.0:
            logger.trace("Apply magnification")
            wfo.Magnification(Mt, Ms)

        if np.abs(n1n2) != 1.0:
            logger.trace("Apply medium change")
            wfo.ChangeMedium(n1n2)

        if np.isfinite(fl):
            logger.trace("Apply lens")
            wfo.lens(fl)

        if np.isfinite(T) and np.abs(T) > 1e-10:
            logger.trace("Apply propagation thickness: T: {:.4f}".format(T))
            wfo.propagate(T)

        vt = item["ABCDt"]() @ vt
        vs = item["ABCDs"]() @ vs
        ABCDt = item["ABCDt"] * ABCDt
        ABCDs = item["ABCDs"] * ABCDs

        logger.debug(
            "F num: {:2f}, distance to focus: {:.6f}".format(
                _retval_["fratio"], wfo.distancetofocus
            )
        )

        _retval_["ABCDt"] = ABCDt
        _retval_["ABCDs"] = ABCDs

        if item["save"]:
            logger.trace("Save optical surface to output dict")
            retval[item["num"]] = deepcopy(_retval_)
        del _retval_

    _ = gc.collect()

    return retval
