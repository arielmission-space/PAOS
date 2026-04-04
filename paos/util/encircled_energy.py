import numpy as np
from photutils.aperture import EllipticalAperture, aperture_photometry 

def compute_elliptical_flux(
    data: np.ndarray, 
    xc: float, yc: float, 
    a: float, b: float = None, 
    theta: float = None) -> float:
    """
    Estimates the sum of the flux in a circular or elliptical aperture.

    Uses the photutils package (https://photutils.readthedocs.io/en/latest/)
    to compute the flux within an elliptical aperture.

    Parameters
    ----------
    data : numpy.ndarray
        The 2D image (e.g., science frame) from which the flux will be
        computed.
    xc : float
        The x-coordinate of the center of the aperture.
    yc : float
        The y-coordinate of the center of the aperture.
    a : float
        The semi-major axis of the ellipse.
    b : float
        The semi-minor axis of the ellipse.
    theta : float, optional
        The position angle (in degrees) of the semi-major axis of the
        ellipse measured counter-clockwise from the positive x-axis.
        If `theta` is not provided, then it is set to 0.

    Returns
    -------
    datasum : float
        The sum of the flux within the elliptical aperture.

    Raises
    ------
    ValueError
        If `data` is not a 2D `numpy.ndarray`.
    ValueError
        If `data` is empty.
    ValueError
        If `a` or `b` are not positive.
    ValueError
        If `xc` or `yc` are not within the image.
    """
    if not isinstance(data, np.ndarray):
        raise ValueError("data should be a numpy ndarray")
    if data.size == 0:
        raise ValueError("data should not be empty")
    if data.ndim != 2:
        raise ValueError("data should be a 2D numpy ndarray")

    # Check if values a and b are positive
    if b == None: b = a
    if a <= 0 or b <= 0:
        raise ValueError("a and b should be positive")
    # Check if values xc and yc are within the image
    if xc < 0 or xc > data.shape[0] or yc < 0 or yc > data.shape[1]:
        raise ValueError("xc and yc should be within the image")
    # Handle case where theta is not provided
    if theta is None:
        theta = 0

    # Create an aperture object
    aperture = EllipticalAperture((xc, yc), a, b, theta)

    # Compute the aperture photometry inside the aperture
    datasum = aperture_photometry(data, aperture)

    return datasum["aperture_sum"][0]