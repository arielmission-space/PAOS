import astropy.units as u
import numpy as np
import sympy

from paos import logger


class PSD:
    """
    Generates a surface error field (SFE) with a given power spectral density (PSD) and surface roughness (SR).

    The PSD is given by the following expression:

    :math:`\\displaystyle PSD(f) = \\frac{A}{B + (f/f_{knee})^C}`

    Parameters
    ----------
    pupil : array like
        The pupil for which the SFE is generated.
    A : float
        The amplitude of the PSD.
    B : float
        PSD parameter. If B = 0, the PSD is a power law.
    C : float
        PSD parameter. It sets the slope of the PSD.
    f : array like
        The frequency grid.
    fknee : float
        The knee frequency of the PSD.
    fmin : float
        The minimum frequency of the PSD.
    fmax : float
        The maximum frequency of the PSD.
    SR : float
        The rms of the surface roughness.
    units : astropy.units
        The units of the SFE. Default is meters.

    Returns
    -------
    wfe : array like
        The generated surface error field.

    Example
    -------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import astropy.units as u

    >>> phi_x = 110.0  # mm
    >>> phi_y = 73.0  # mm
    >>> zoom = 4
    >>> wl = 0.550
    >>> D = zoom * np.max([phi_x, phi_y])
    >>> grid = 1024
    >>> delta = D / grid

    >>> A, B, C, fknee, fmin, fmax = 7.0, 0.0, 1.5, 1.0, 1 / 20, 1 / 2
    >>> SR = 0.0

    >>> x = y = np.arange(-grid // 2, grid // 2) * delta
    >>> xx, yy = np.meshgrid(x, y)
    >>> pupil = np.zeros((grid, grid))

    >>> mask = (2 * xx / phi_x) ** 2 + (2 * yy / phi_y) ** 2 <= 1
    >>> pupil[mask] = 1.0
    >>> wfo = np.ma.masked_array(pupil, mask=~mask)

    >>> fx = np.fft.fftfreq(wfo.shape[0], delta)
    >>> fxx, fyy = np.meshgrid(fx, fx)
    >>> f = np.sqrt(fxx**2 + fyy**2)
    >>> f[f == 0] = 1e-100

    >>> wfo_ = PSD(wfo, A, B, C, f, fknee, fmin, fmax, SR, units=u.nm)

    >>> plt.figure()
    >>> plt.imshow(wfo_(), cmap="jet", origin="lower")
    >>> plt.xlim(grid // 2 - grid // (2 * zoom), grid // 2 + grid // (2 * zoom))
    >>> plt.ylim(grid // 2 - grid // (2 * zoom), grid // 2 + grid // (2 * zoom))
    >>> plt.colorbar()
    >>> plt.show()

    """

    def __init__(
        self,
        pupil,
        A=10.0,
        B=0.0,
        C=0.0,
        f=None,
        fknee=1.0,
        fmin=None,
        fmax=None,
        SR=0.0,
        units=u.m,
    ):

        # get the grid size
        Nx, Ny = pupil.shape

        # get the mask if it is a masked array
        if isinstance(pupil, np.ma.MaskedArray):
            mask = pupil.mask
        else:
            mask = np.zeros((Nx, Ny)).astype(bool)

        # compute the desired std for psd
        sfe_rms = self.sfe_rms(A, B, C, fknee, fmin, fmax)
        logger.debug(f"Desired std for PSD: {sfe_rms} {units}")

        # generate random field
        self.wfe = np.random.randn(Nx, Ny)

        # FFT
        ft_wfe = np.fft.fft2(self.wfe)

        dfx = f[0, 2] - f[0, 1]
        dfy = f[2, 0] - f[1, 0]

        # compute 2D PSD
        psd2d = A / (B + (f / fknee) ** C) / (2 * np.pi * f) * (dfx * dfy)

        # apply PSD to FT of random field
        ft_wfe *= np.sqrt(psd2d) * np.sqrt(Nx * Ny)

        # frequency mask
        idx = np.logical_or(f < fmin, f > fmax)
        ft_wfe[idx] = 0.0

        # inverse FFT
        self.wfe = np.fft.ifft2(ft_wfe).real

        # to masked array
        self.wfe = np.ma.masked_array(self.wfe, mask=mask)

        # current std
        current_std = self.wfe.std()
        logger.debug(f"Current std for PSD: {current_std} {units}")

        # add surface roughness
        self.wfe += SR * np.random.randn(Nx, Ny)

        # from sfe to wfe
        self.wfe *= 2

        # convert to meters using astropy.units
        self.wfe *= units.to(u.m)

    def __call__(self):

        return self.wfe

    @staticmethod
    def sfe_rms(A, B, C, f_knee, f_min, f_max):
        """
        Method to compute the rms of the surface error field (SFE) from the power spectral density (PSD).
        It uses sympy to evaluate the integral of the PSD.
        """
        # define symbols
        f = sympy.symbols("f")
        a, b, c, fknee, fmin, fmax = sympy.symbols("a b c fknee fmin fmax")

        # define PSD
        expr = a / (b + (f / fknee) ** c)

        # evaluate integral using sympy
        integral = sympy.integrate(expr, (f, fmin, fmax))

        # substitute values
        integral = integral.subs(
            {a: A, b: B, c: C, fknee: f_knee, fmin: f_min, fmax: f_max}
        )

        # desired std for psd
        sfe_rms = np.sqrt(float(integral))

        return sfe_rms
