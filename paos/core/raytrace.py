import numpy as np

from paos import logger
from paos.core.coordinateBreak import coordinate_break


def raytrace(field, opt_chain, x=0.0, y=0.0):
    """
    Diagnostic function that implements the Paraxial ray-tracing and prints the output for each surface of the optical
    chain as the ray positions and slopes in the tangential and sagittal planes.

    Parameters
    ----------
    field: dict
        contains the slopes in the tangential and sagittal planes as field={'vt': slopey, 'vs': slopex}
    opt_chain: dict
        the dict of the optical elements returned by paos.parse_config
    x: float
        X-coordinate of the initial ray position
    y: float
        Y-coordinate of the initial ray position

    Returns
    -----
    out: list[str]
        A list of strings where each list item is the raytrace at a given surface.

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.raytrace import raytrace
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/conf/file')
    >>> raytrace(fields[0], opt_chains[0])

    """
    vt = np.array([y, field["ut"]])
    vs = np.array([x, field["us"]])
    ostr = []
    for key, item in opt_chain.items():
        if item["type"] == "Coordinate Break":
            vt, vs = coordinate_break(
                vt,
                vs,
                item["xdec"],
                item["ydec"],
                item["xrot"],
                item["yrot"],
                0.0,
            )

        vt = item["ABCDt"]() @ vt
        vs = item["ABCDs"]() @ vs
        _ostr_ = "S{:02d} - {:15s} y:{:7.3f}mm ut:{:10.3e} rad x:{:7.3f}mm us:{:10.3e} rad".format(
            key, item["name"], 1000 * vt[0], vt[1], 1000 * vs[0], vs[1]
        )
        logger.debug(_ostr_)
        ostr.append(_ostr_)

    return ostr
