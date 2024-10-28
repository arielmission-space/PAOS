import numpy as np
from scipy.spatial.transform import Rotation as R

from paos import logger


def coordinate_break(vt, vs, xdec, ydec, xrot, yrot, zrot, order=0):
    """
    Performs a coordinate break and estimates the new :math:`\\vec{v_{t}}=(y, u_{y})`
    and :math:`\\vec{v_{s}}=(x, u_{x})`.

    Parameters
    ----------
    vt: array
        vector :math:`\\vec{v_{t}}=(y, u_{y})` describing a ray propagating in the tangential plane
    vs: array
        vector :math:`\\vec{v_{s}}=(x, u_{x})` describing a ray propagating in the sagittal plane
    xdec: float
        x coordinate of the decenter to be applied
    ydec: float
        y coordinate of the decenter to be applied
    xrot: float
        tilt angle around the X axis to be applied
    yrot: float
        tilt angle around the Y axis to be applied
    zrot: float
        tilt angle around the Z axis to be applied
    order: int
        order of the coordinate break, defaults to 0.

    Returns
    -------
    tuple
        two arrays representing the new :math:`\\vec{v_{t}}=(y, u_{y})`
        and :math:`\\vec{v_{s}}=(x, u_{x})`.

    Note
    ----
    When order=0, first a coordinate decenter is applied, followed by a XYZ rotation.
    Coordinate break orders other than 0 not implemented yet.

    """

    if order != 0:
        logger.error("Coordinate break orders other than 0 not implemented yet")
        raise ValueError("Coordinate break orders other than 0 not implemented yet")

    if not np.isfinite(xdec):
        xdec = 0.0
    if not np.isfinite(ydec):
        ydec = 0.0
    if not np.isfinite(xrot):
        xrot = 0.0
    if not np.isfinite(yrot):
        yrot = 0.0
    if not np.isfinite(zrot):
        zrot = 0.0

    # Rotation matrix, intrinsic
    U = R.from_euler("xyz", [xrot, yrot, zrot], degrees=True)

    r0 = [vs[0] - xdec, vt[0] - ydec, 0.0]
    n0 = [vs[1], vt[1], 1]
    n1 = U.inv().apply(n0)
    n1 /= n1[2]
    r1_ln1 = U.inv().apply(r0)
    r1 = r1_ln1 - n1 * r1_ln1[2] / n1[2]

    vt1 = np.array([r1[1], n1[1]])
    vs1 = np.array([r1[0], n1[0]])

    return vt1, vs1
