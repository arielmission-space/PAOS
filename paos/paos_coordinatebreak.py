import numpy as np
from scipy.spatial.transform import Rotation as R
from .paos_config import logger


def CoordinateBreak(vt, vs, xdec, ydec, xrot, yrot, zrot, order=0):
    """
    Performs a coordinate break and estimates the new vt=(y0, uy) and vs=(x0, ux).

    Note
    ----------
    When order=0, first a coordinate decenter is applied, followed by a XYZ rotation.
    Coordinate break orders other than 0 not implemented yet.
    """

    if order != 0:
        logger.error('Coordinate break orders other than 0 not implemented yet')
        raise ValueError('Coordinate break orders other than 0 not implemented yet')

    if not np.isfinite(xdec): xdec = 0.0
    if not np.isfinite(ydec): ydec = 0.0
    if not np.isfinite(xrot): xrot = 0.0
    if not np.isfinite(yrot): yrot = 0.0
    if not np.isfinite(zrot): zrot = 0.0

    # Rotation matrix, intrinsic
    U = R.from_euler('xyz', [xrot, yrot, zrot], degrees=True)

    r0 = [vs[0] - xdec, vt[0] - ydec, 0.0]
    n0 = [vs[1], vt[1], 1]
    n1 = U.inv().apply(n0)
    n1 /= n1[2]
    r1_ln1 = U.inv().apply(r0)
    r1 = r1_ln1 - n1 * r1_ln1[2] / n1[2]

    vt1 = np.array([r1[1], n1[1]])
    vs1 = np.array([r1[0], n1[0]])

    return vt1, vs1
