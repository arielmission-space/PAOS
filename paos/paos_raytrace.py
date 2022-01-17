import numpy as np
from .paos_coordinatebreak import CoordinateBreak
from .paos_config import logger


def raytrace(field, opt_chain, x=0.0, y=0.0):
    """
    Diagnostic function that implements the full ray tracing
    and prints the output for each surface of the optical chain
    as the ray positions and slopes in the tangential and sagittal planes.

    Parameters
    ----------
    field: dictionary
        contains the slopes in the tangential and sagittal planes as field={'vt': slopey, 'vs': slopex}
    opt_chain: list
        the list of the optical elements returned by paos.parseconfig

    Returns
    -----
    out: list
        List of string. Each list item is the raytrace at a given surface.

    Examples
    --------

    >>> from paos.paos_parseconfig import ParseConfig
    >>> from paos.paos_raytrace import raytrace
    >>> pupil_diameter, general, fields, optical_chain = ParseConfig('path/to/conf/file')
    >>> raytrace(fields['0'], optical_chain)

    """
    vt = np.array([y, field['ut']])
    vs = np.array([x, field['us']])
    ostr = []
    for key, item in opt_chain.items():
        if item['type'] == 'Coordinate Break':
            vt, vs = CoordinateBreak(vt, vs, item['xdec'], item['ydec'], item['xrot'], item['yrot'], 0.0)

        vt = item['ABCDt']() @ vt
        vs = item['ABCDs']() @ vs
        _ostr_ = "S{:02d} - {:15s} y:{:7.3f}mm ut:{:10.3e} rad x:{:7.3f}mm us:{:10.3e} rad".format(
            key, item['name'], 1000 * vt[0], vt[1], 1000 * vs[0], vs[1])
        logger.info(_ostr_)
        ostr.append(_ostr_)

    return ostr
