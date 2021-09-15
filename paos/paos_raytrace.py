import numpy as np
from .paos_coordinatebreak import CoordinateBreak


def raytrace(field, opt_chain):
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
    None
        prints the output of the full ray tracing

    """
    vt = np.array([0.0, field['ut']])
    vs = np.array([0.0, field['us']])
    for key, item in opt_chain.items():
        if item['type'] == 'Coordinate Break':
            vt, vs = CoordinateBreak(vt, vs, item['xdec'], item['ydec'], item['xrot'], item['yrot'], 0.0)

        vt = item['ABCDt']() @ vt
        vs = item['ABCDs']() @ vs
        print("S{:02d} - {:15s} y:{:7.3f}mm ut:{:10.3e} rad x:{:7.3f}mm us:{:7.3f} rad".format(
            key, item['name'], 1000 * vt[0], vt[1], 1000 * vs[0], vs[1]))

    return
