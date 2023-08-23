import numpy as np
import photutils

from paos import logger
from paos.classes.zernike import Zernike


class WFO:
    """
    Physical optics wavefront propagation.
    Implements the paraxial theory described in
    `Lawrence et al., Applied Optics and Optical Engineering, Volume XI (1992) <https://ui.adsabs.harvard.edu/abs/1992aooe...11..125L>`_

    All units are meters.

    Parameters
    ----------
    beam_diameter: scalar
        the input beam diameter. Note that the input beam is always circular, regardless of
        whatever non-circular apodization the input pupil might apply.
    wl: scalar
        the wavelength
    grid_size: scalar
        grid size must be a power of 2
    zoom: scalar
        linear scaling factor of input beam.

    Attributes
    ----------
    wl: scalar
        the wavelength
    z: scalar
        current beam position along the z-axis (propagation axis).
        Initial value is 0
    w0: scalar
        pilot Gaussian beam waist.
        Initial value is beam_diameter/2
    zw0: scalar
        z-coordinate of the Gaussian beam waist.
        initial value is 0
    zr: scalar
        Rayleigh distance: :math:`\\pi w_{0}^{2} / \\lambda`
    rayleigh_factor: scalar
        Scale factor multiplying zr to determine 'I' and 'O' regions.
        Built in value is 2
    dx: scalar
        pixel sampling interval along x-axis
    dy: scalar
        pixel sampling interval along y-axis
    C: scalar
        curvature of the reference surface at beam position
    fratio: scalar
        pilot Gaussian beam f-ratio
    wfo: array [gridsize, gridsize], complex128
        the wavefront complex array
    amplitude: array [gridsize, gridsize], float64
        the wavefront amplitude array
    phase: array [gridsize, gridsize], float64
        the wavefront phase array in radians
    wz: scalar
        the Gaussian beam waist w(z) at current beam position
    distancetofocus: scalar
        the distance to focus from current beam position
    extent: tuple
        the physical coordinates of the wavefront bounding box (xmin, xmax, ymin, ymax).
        Can be used directly in im.set_extent.

    Returns
    -------
    out: an instance of wfo

    Example
    -------
    >>> import paos
    >>> import matplotlib.pyplot as plt
    >>> beam_diameter = 1.0  # m
    >>> wavelength = 3.0  # micron
    >>> grid_size = 512
    >>> zoom = 4
    >>> xdec, ydec = 0.0, 0.0
    >>> fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
    >>> wfo = paos.WFO(beam_diameter, 1.0e-6 * wavelength, grid_size, zoom)
    >>> wfo.aperture(xc=xdec, yc=ydec, r=beam_diameter/2, shape='circular')
    >>> wfo.make_stop()
    >>> ax0.imshow(wfo.amplitude)
    >>> wfo.lens(lens_fl=1.0)
    >>> wfo.propagate(dz=1.0)
    >>> ax1.imshow(wfo.amplitude)
    >>> plt.show()

    """

    def __init__(self, beam_diameter, wl, grid_size, zoom):

        assert np.log2(grid_size).is_integer(), "Grid size should be 2**n"
        assert zoom > 0, "zoom factor should be positive"
        assert beam_diameter > 0, "beam diameter should be positive"
        assert wl > 0, "a wavelength should be positive"

        self._wl = wl
        self._z = 0.0  # current beam z coordinate
        self._w0 = beam_diameter / 2.0  # beam waist
        self._zw0 = 0.0  # beam waist z coordinate
        self._zr = np.pi * self.w0**2 / wl  # Rayleigh distance

        self._rayleigh_factor = 2.0
        self._dx = beam_diameter * zoom / grid_size  # pixel size
        self._dy = beam_diameter * zoom / grid_size  # pixel size
        self._C = 0.0  # beam curvature, start with a planar wf
        self._fratio = np.inf  # Gaussian beam f-ratio

        grid_size = np.uint(grid_size)
        self._wfo = np.ones((grid_size, grid_size), dtype=np.complex128)

    @property
    def wl(self):
        return self._wl

    @property
    def z(self):
        return self._z

    @property
    def w0(self):
        return self._w0

    @property
    def zw0(self):
        return self._zw0

    @property
    def zr(self):
        return self._zr

    @property
    def rayleigh_factor(self):
        return self._rayleigh_factor

    @property
    def dx(self):
        return self._dx

    @property
    def dy(self):
        return self._dy

    @property
    def C(self):
        return self._C

    @property
    def fratio(self):
        return self._fratio

    @property
    def wfo(self):
        return self._wfo.copy()

    @property
    def amplitude(self):
        return np.abs(self._wfo)

    @property
    def phase(self):
        return np.angle(self._wfo)

    @property
    def wz(self):
        return self.w0 * np.sqrt(1.0 + ((self.z - self.zw0) / self.zr) ** 2)

    @property
    def distancetofocus(self):
        return self.zw0 - self.z

    @property
    def extent(self):
        return (
            -self._wfo.shape[1] // 2 * self.dx,
            (self._wfo.shape[1] // 2 - 1) * self.dx,
            -self._wfo.shape[0] // 2 * self.dy,
            (self._wfo.shape[0] // 2 - 1) * self.dy,
        )

    def make_stop(self):
        """
        Make current surface a stop.
        Stop here just means that the wf at current position is normalised to unit energy.
        """
        norm2 = np.sum(np.abs(self._wfo) ** 2)
        self._wfo /= np.sqrt(norm2)

    def aperture(
        self,
        xc,
        yc,
        hx=None,
        hy=None,
        r=None,
        shape="elliptical",
        tilt=None,
        obscuration=False,
    ):
        """
        Apply aperture mask

        Parameters
        ----------
        xc: scalar
            x-centre of the aperture
        yc: scalar
            y-centre of the aperture
        hx, hy: scalars
            semi-axes of shape 'elliptical' aperture, or full dimension of shape 'rectangular' aperture
        r: scalar
            radius of shape 'circular' aperture
        shape: string
            defines aperture shape. Can be 'elliptical', 'circular', 'rectangular'
        tilt: scalar
            tilt angle in degrees. Applies to shapes 'elliptical' and 'rectangular'.
        obscuration: boolean
            if True, aperture mask is converted into obscuration mask.

        """

        ixc = xc / self.dx + self._wfo.shape[1] / 2
        iyc = yc / self.dy + self._wfo.shape[0] / 2

        if shape == "elliptical":
            if hx is None or hy is None:
                logger.error("Semi major/minor axes not defined")
                raise AssertionError("Semi major/minor axes not defined")
            ihx = hx / self.dx
            ihy = hy / self.dy
            theta = 0.0 if tilt is None else np.deg2rad(tilt)
            aperture = photutils.aperture.EllipticalAperture(
                (ixc, iyc), ihx, ihy, theta=theta
            )
            mask = aperture.to_mask(method="exact").to_image(self._wfo.shape)
        elif shape == "circular":
            if r is None:
                logger.error("Radius not defined")
                raise AssertionError("Radius not defined")
            ihx = r / self.dx
            ihy = r / self.dy
            theta = 0.0
            aperture = photutils.aperture.EllipticalAperture(
                (ixc, iyc), ihx, ihy, theta=theta
            )
            mask = aperture.to_mask(method="exact").to_image(self._wfo.shape)
        elif shape == "rectangular":
            if hx is None or hy is None:
                logger.error("Semi major/minor axes not defined")
                raise AssertionError("Semi major/minor axes not defined")
            ihx = hx / self.dx
            ihy = hy / self.dy
            theta = 0.0 if tilt is None else np.deg2rad(tilt)
            aperture = photutils.aperture.RectangularAperture(
                (ixc, iyc), ihx, ihy, theta=theta
            )
            # Exact method not implemented in photutils 1.0.2
            mask = aperture.to_mask(method="subpixel", subpixels=32).to_image(
                self._wfo.shape
            )
        else:
            logger.error("Aperture {:s} not defined yet.".format(shape))
            raise ValueError("Aperture {:s} not defined yet.".format(shape))

        if obscuration:
            self._wfo *= 1 - mask
        else:
            self._wfo *= mask

        return aperture

    def insideout(self, z=None):
        """
        Check if z position is within the Rayleigh distance

        Parameters
        ----------
        z: scalar
            beam coordinate long propagation axis

        Returns
        -------
            out: string
                'I' if :math:`|z - z_{w0}| < z_{r}` else 'O'
        """
        if z is None:
            delta_z = self.z - self.zw0
        else:
            delta_z = z - self.zw0

        if np.abs(delta_z) < self.rayleigh_factor * self.zr:
            return "I"
        else:
            return "O"

    def lens(self, lens_fl):
        """
        Apply wavefront phase from paraxial lens

        Parameters
        ----------
        lens_fl: scalar
            Lens focal length. Positive for converging lenses. Negative for diverging lenses.

        Note
        ----------
            A paraxial lens imposes a quadratic phase shift.
        """

        wz = self.w0 * np.sqrt(1.0 + ((self.z - self.zw0) / self.zr) ** 2)
        delta_z = self.z - self.zw0

        propagator = self.insideout()

        # estimate Gaussian beam curvature after lens
        gCobj = delta_z / (
            delta_z**2 + self.zr**2
        )  # Gaussian beam curvature before lens
        gCima = gCobj - 1.0 / lens_fl  # Gaussian beam curvature after lens

        # update Gaussian beam parameters
        self._w0 = wz / np.sqrt(1.0 + (np.pi * wz**2 * gCima / self.wl) ** 2)
        self._zw0 = (
            -gCima / (gCima**2 + (self.wl / (np.pi * wz**2)) ** 2) + self.z
        )
        self._zr = np.pi * self.w0**2 / self.wl

        propagator = propagator + self.insideout()

        if propagator[0] == "I" or self.C == 0.0:
            Cobj = 0.0
        else:
            Cobj = 1 / delta_z

        delta_z = self.z - self.zw0

        if propagator[1] == "I":
            Cima = 0.0
        else:
            Cima = 1 / delta_z

        self._C = Cima

        if propagator == "II":
            lens_phase = 1.0 / lens_fl
        elif propagator == "IO":
            lens_phase = 1 / lens_fl + Cima
        elif propagator == "OI":
            lens_phase = 1.0 / lens_fl - Cobj
        elif propagator == "OO":
            lens_phase = 1.0 / lens_fl - Cobj + Cima

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        qphase = -(xx**2 + yy**2) * (0.5 * lens_phase / self.wl)

        self._fratio = np.abs(delta_z) / (2 * wz)
        self._wfo = self._wfo * np.exp(2.0j * np.pi * qphase)

    def Magnification(self, My, Mx=None):
        """
        Given the optical magnification along one or both directions, updates the sampling along both directions,
        the beam semi-diameter, the Rayleigh distance, the distance to focus, and the beam focal ratio

        Parameters
        ----------
        My: scalar
            optical magnification along tangential direction
        Mx: scalar
            optical magnification along sagittal direction

        Returns
        -------
        out: None
            updates the wfo parameters

        """
        if Mx is None:
            Mx = My

        assert Mx > 0.0, "Negative magnification not implemented yet."
        assert My > 0.0, "Negative magnification not implemented yet."

        self._dx *= Mx
        self._dy *= My

        if np.abs(Mx - 1.0) < 1.0e-8 or Mx is None:
            logger.trace(
                "Does not do anything if magnification x is close to unity."
            )
            return

        logger.warning(
            "Gaussian beam magnification is implemented, but has not been tested."
        )

        # Current distance to focus (before magnification)
        delta_z = self.z - self.zw0
        # Current w(z) (before magnification)
        wz = self.w0 * np.sqrt(1.0 + ((self.z - self.zw0) / self.zr) ** 2)

        # Apply magnification following ABCD Gaussian beam prescription
        # i.e. w'(z) = Mx*w(z), R'(z) = Mx**2 * R(z)

        delta_z *= Mx**2
        wz *= Mx
        self._w0 *= Mx  # From Eq 56, Lawrence (1992)
        self._zr *= Mx**2
        self._zw0 = self.z - delta_z
        self._fratio = np.abs(delta_z) / (2 * wz)

    def ChangeMedium(self, n1n2):
        """
        Given the ratio of refractive indices n1/n2 for light propagating from a medium with refractive index n1,
        into a medium with refractive index n2, updates the Rayleigh distance, the wavelength, the distance to focus,
        and the beam focal ratio

        Parameters
        ----------
        n1n2

        Returns
        -------
        out: None
            updates the wfo parameters

        """
        _n1n2 = np.abs(n1n2)

        # Current distance to focus (before magnification)
        delta_z = self.z - self.zw0

        delta_z /= n1n2
        self._zr /= n1n2
        self._wl *= n1n2
        self._zw0 = self.z - delta_z
        self._fratio /= n1n2

    def ptp(self, dz):
        """
        Plane-to-plane (far field) wavefront propagator

        Parameters
        ----------
        dz: scalar
            propagation distance
        """
        if np.abs(dz) < 0.001 * self.wl:
            logger.debug(
                "Thickness smaller than 1/1000 wavelength. Returning.."
            )
            return

        if self.C != 0:
            logger.error("PTP wavefront should be planar")
            raise ValueError("PTP wavefront should be planar")

        wf = np.fft.ifftshift(self._wfo)
        wf = np.fft.fft2(wf, norm="ortho")
        fx = np.fft.fftfreq(wf.shape[1], d=self.dx)
        fy = np.fft.fftfreq(wf.shape[0], d=self.dy)
        fxx, fyy = np.meshgrid(fx, fy)
        qphase = (np.pi * self.wl * dz) * (fxx**2 + fyy**2)
        wf = np.fft.ifft2(np.exp(-1.0j * qphase) * wf, norm="ortho")

        self._z = self._z + dz

        self._wfo = np.fft.fftshift(wf)

    def stw(self, dz):
        """
        Spherical-to-waist (near field to far field) wavefront propagator

        Parameters
        ----------
        dz: scalar
            propagation distance
        """
        if np.abs(dz) < 0.001 * self.wl:
            logger.debug(
                "Thickness smaller than 1/1000 wavelength. Returning.."
            )
            return

        if self.C == 0.0:
            logger.error("STW wavefront should not be planar")
            raise ValueError("STW wavefront should not be planar")

        s = "forward" if dz >= 0 else "reverse"

        wf = np.fft.ifftshift(self._wfo)
        if s == "forward":
            wf = np.fft.fft2(wf, norm="ortho")
        elif s == "reverse":
            wf = np.fft.ifft2(wf, norm="ortho")

        fx = np.fft.fftfreq(wf.shape[1], d=self.dx)
        fy = np.fft.fftfreq(wf.shape[0], d=self.dy)
        fxx, fyy = np.meshgrid(fx, fy)

        qphase = (np.pi * self.wl * dz) * (fxx**2 + fyy**2)

        self._z = self._z + dz
        self._C = 0.0
        self._dx = (fx[1] - fx[0]) * self.wl * np.abs(dz)
        self._dy = (fy[1] - fy[0]) * self.wl * np.abs(dz)
        self._wfo = np.fft.fftshift(np.exp(1.0j * qphase) * wf)

    def wts(self, dz):
        """
        Waist-to-spherical (far field to near field) wavefront propagator

        Parameters
        ----------
        dz: scalar
            propagation distance
        """
        if np.abs(dz) < 0.001 * self.wl:
            logger.debug(
                "Thickness smaller than 1/1000 wavelength. Returning.."
            )
            return

        if self.C != 0.0:
            logger.error("WTS wavefront should be planar")
            raise ValueError("WTS wavefront should be planar")

        s = "forward" if dz >= 0 else "reverse"

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        qphase = (np.pi / (dz * self.wl)) * (xx**2 + yy**2)
        wf = np.fft.ifftshift(np.exp(1.0j * qphase) * self._wfo)
        if s == "forward":
            wf = np.fft.fft2(wf, norm="ortho")
        elif s == "reverse":
            wf = np.fft.ifft2(wf, norm="ortho")

        self._z = self._z + dz
        self._C = 1 / (self.z - self.zw0)
        self._dx = self.wl * np.abs(dz) / (wf.shape[1] * self.dx)
        self._dy = self.wl * np.abs(dz) / (wf.shape[1] * self.dy)
        self._wfo = np.fft.fftshift(wf)

    def propagate(self, dz):
        """
        Wavefront propagator. Selects the appropriate propagation primitive and applies the wf propagation

        Parameters
        ----------
        dz: scalar
            propagation distance
        """
        propagator = self.insideout() + self.insideout(self.z + dz)
        z1 = self.z
        z2 = self.z + dz

        if propagator == "II":
            self.ptp(dz)
        elif propagator == "OI":
            self.stw(self.zw0 - z1)
            self.ptp(z2 - self.zw0)
        elif propagator == "IO":
            self.ptp(self.zw0 - z1)
            self.wts(z2 - self.zw0)
        elif propagator == "OO":
            self.stw(self.zw0 - z1)
            self.wts(z2 - self.zw0)

    def zernikes(
        self, index, Z, ordering, normalize, radius, offset=0.0, origin="x"
    ):
        """
        Add a WFE represented by a Zernike expansion

        Parameters
        ----------
        index: array of integers
            Sequence of zernikes to use. It should be a continuous sequence.
        Z : array of floats
            The coefficients of the Zernike polynomials in meters.
        ordering: string
            Can be 'ansi', 'noll', 'fringe', or 'standard'.
        normalize: bool
            Polynomials are normalised to RMS=1 if True, or to unity at radius if False.
        radius: float
            The radius of the circular aperture over which the polynomials are calculated.
        offset: float
            Angular offset in degrees.
        origin: string
            Angles measured counter-clockwise positive from x axis by default (origin='x').
            Set origin='y' for angles measured clockwise-positive from the y-axis.

        Returns
        -------
        out: masked array
            the WFE
        """
        assert not np.any(
            np.diff(index) - 1
        ), "Zernike sequence should be continuous"

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        rho = np.sqrt(xx**2 + yy**2) / radius

        if origin == "x":
            phi = np.arctan2(yy, xx) + np.deg2rad(offset)
        elif origin == "y":
            phi = np.arctan2(xx, yy) + np.deg2rad(offset)
        else:
            logger.error(
                "Origin {} not recognised. Origin shall be either x or y".format(
                    origin
                )
            )
            raise ValueError(
                "Origin {} not recognised. Origin shall be either x or y".format(
                    origin
                )
            )
        zernike = Zernike(
            len(index), rho, phi, ordering=ordering, normalize=normalize
        )
        zer = zernike()
        wfe = (zer.T * Z).T.sum(axis=0)
        self._wfo = self._wfo * np.exp(
            2.0 * np.pi * 1j * wfe / self._wl
        ).filled(0)

        return wfe


if __name__ == "__main__":
    pass
