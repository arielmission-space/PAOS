import numpy as np
import photutils
from paos.classes.zernike import Zernike
from paos import logger


class WFO(object):
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
    zx: scalar
        current beam position along the z-axis (propagation axis), sagittal component.
        Initial value is 0
    zy: scalar
        current beam position along the z-axis (propagation axis), tangential component.
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
        assert zoom > 0, 'zoom factor should be positive'
        assert beam_diameter > 0, 'beam diameter should be positive'
        assert wl > 0, 'a wavelength should be positive'

        self._wl = wl
        self._z_x = 0.0  # current beam z coordinate, sagittal plane
        self._z_y = 0.0  # current beam z coordinate, tangential plane
        self._w0_x = beam_diameter / 2.0  # beam waist, sagittal plane
        self._w0_y = beam_diameter / 2.0  # beam waist, tangential plane
        self._zw0_x = 0.0  # beam waist z coordinate, sagittal plane
        self._zw0_y = 0.0  # beam waist z coordinate, tangential plane
        self._zr_x = np.pi * self.w0_x ** 2 / wl  # Rayleigh distance, sagittal plane
        self._zr_y = np.pi * self.w0_y ** 2 / wl  # Rayleigh distance, tangential plane

        self._rayleigh_factor = 2.0
        self._dx = beam_diameter * zoom / grid_size  # pixel size
        self._dy = beam_diameter * zoom / grid_size  # pixel size
        self._C_x = 0.0  # beam curvature, start with a planar wf, sagittal plane
        self._C_y = 0.0  # beam curvature, start with a planar wf, tangential plane
        self._fratio_x = np.inf  # Gaussian beam f-ratio, sagittal plane
        self._fratio_y = np.inf  # Gaussian beam f-ratio, tangential plane

        grid_size = np.uint(grid_size)
        self._wfo = np.ones((grid_size, grid_size), dtype=np.complex128)

    @property
    def wl(self):
        return self._wl

    @property
    def z_x(self):
        return self._z_x

    @property
    def z_y(self):
        return self._z_y

    @property
    def w0_x(self):
        return self._w0_x

    @property
    def w0_y(self):
        return self._w0_y

    @property
    def zw0_x(self):
        return self._zw0_x

    @property
    def zw0_y(self):
        return self._zw0_y

    @property
    def zr_x(self):
        return self._zr_x

    @property
    def zr_y(self):
        return self._zr_y

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
    def C_x(self):
        return self._C_x

    @property
    def C_y(self):
        return self._C_y

    @property
    def fratio_x(self):
        return self._fratio_x

    @property
    def fratio_y(self):
        return self._fratio_y

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
    def wz_x(self):
        return self.w0_x * np.sqrt(1.0 + ((self.z_x - self.zw0_x) / self.zr_x) ** 2)

    @property
    def wz_y(self):
        return self.w0_y * np.sqrt(1.0 + ((self.z_y - self.zw0_y) / self.zr_y) ** 2)

    @property
    def distancetofocus_x(self):
        return self.zw0_x - self.z_x

    @property
    def distancetofocus_y(self):
        return self.zw0_y - self.z_y

    @property
    def extent(self):
        return (-self._wfo.shape[1] // 2 * self.dx, (self._wfo.shape[1] // 2 - 1) * self.dx,
                -self._wfo.shape[0] // 2 * self.dy, (self._wfo.shape[0] // 2 - 1) * self.dy)

    def make_stop(self):
        """
        Make current surface a stop.
        Stop here just means that the wf at current position is normalised to unit energy.
        """
        norm2 = np.sum(np.abs(self._wfo) ** 2)
        self._wfo /= np.sqrt(norm2)

    def aperture(self, xc, yc, hx=None, hy=None, r=None,
                 shape='elliptical', tilt=None, obscuration=False):
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

        if shape == 'elliptical':
            if hx is None or hy is None:
                logger.error('Semi major/minor axes not defined')
                raise AssertionError('Semi major/minor axes not defined')
            ihx = hx / self.dx
            ihy = hy / self.dy
            theta = 0.0 if tilt is None else np.deg2rad(tilt)
            aperture = photutils.aperture.EllipticalAperture((ixc, iyc), ihx, ihy, theta=theta)
            mask = aperture.to_mask(method='exact').to_image(self._wfo.shape)
        elif shape == 'circular':
            if r is None:
                logger.error('Radius not defined')
                raise AssertionError('Radius not defined')
            ihx = r / self.dx
            ihy = r / self.dy
            theta = 0.0
            aperture = photutils.aperture.EllipticalAperture((ixc, iyc), ihx, ihy, theta=theta)
            mask = aperture.to_mask(method='exact').to_image(self._wfo.shape)
        elif shape == 'rectangular':
            if hx is None or hy is None:
                logger.error('Semi major/minor axes not defined')
                raise AssertionError('Semi major/minor axes not defined')
            ihx = hx / self.dx
            ihy = hy / self.dy
            theta = 0.0 if tilt is None else np.deg2rad(tilt)
            aperture = photutils.aperture.RectangularAperture((ixc, iyc), ihx, ihy, theta=theta)
            # Exact method not implemented in photutils 1.0.2
            mask = aperture.to_mask(method='subpixel', subpixels=32).to_image(self._wfo.shape)
        else:
            logger.error('Aperture {:s} not defined yet.'.format(shape))
            raise ValueError('Aperture {:s} not defined yet.'.format(shape))

        if obscuration:
            self._wfo *= 1 - mask
        else:
            self._wfo *= mask

        return aperture

    def insideout(self, z_x=None, z_y=None):
        """
        Check if z position is within the Rayleigh distance.
        Both sagittal and tangential planes are checked.

        Parameters
        ----------
        z_x: scalar
            beam coordinate along propagation axis, sagittal plane
        z_y: scalar
            beam coordinate along propagation axis, tangential plane

        Returns
        -------
            out: string
                'I' if :math:`|z - z_{w0}| < z_{r}` else 'O'
        """
        if z_x is None:
            delta_z_x = self.z_x - self.zw0_x
        else:
            delta_z_x = z_x - self.zw0_x

        if z_y is None:
            delta_z_y = self.z_y - self.zw0_y
        else:
            delta_z_y = z_y - self.zw0_y

        if np.abs(delta_z_x) < self.rayleigh_factor * self.zr_x:
            insideout_x = 'I'
        else:
            insideout_x = 'O'

        if np.abs(delta_z_y) < self.rayleigh_factor * self.zr_y:
            insideout_y = 'I'
        else:
            insideout_y = 'O'

        assert insideout_x == insideout_y, 'Sagittal and tangential planes are not in the same state'
        return insideout_x

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

        wz_x = self.w0_x * np.sqrt(1.0 + ((self.z_x - self.zw0_x) / self.zr_x) ** 2)
        wz_y = self.w0_y * np.sqrt(1.0 + ((self.z_y - self.zw0_y) / self.zr_y) ** 2)
        delta_z_x = self.z_x - self.zw0_x
        delta_z_y = self.z_y - self.zw0_y

        propagator = self.insideout()

        # estimate Gaussian beam curvature after lens
        gCobj_x = delta_z_x / (delta_z_x ** 2 + self.zr_x ** 2)  # Gaussian beam curvature before lens. Sagittal plane
        gCobj_y = delta_z_y / (delta_z_y ** 2 + self.zr_y ** 2)  # Gaussian beam curvature before lens. Tangential plane
        gCima_x = gCobj_x - 1.0 / lens_fl  # Gaussian beam curvature after lens. Sagittal plane
        gCima_y = gCobj_y - 1.0 / lens_fl  # Gaussian beam curvature after lens. Tangential plane

        # update Gaussian beam parameters
        self._w0_x = wz_x / np.sqrt(1.0 + (np.pi * wz_x ** 2 * gCima_x / self.wl) ** 2)
        self._w0_y = wz_y / np.sqrt(1.0 + (np.pi * wz_y ** 2 * gCima_y / self.wl) ** 2)
        self._zw0_x = -gCima_x / (gCima_x ** 2 + (self.wl / (np.pi * wz_x ** 2)) ** 2) + self.z_x
        self._zw0_y = -gCima_y / (gCima_y ** 2 + (self.wl / (np.pi * wz_y ** 2)) ** 2) + self.z_y
        self._zr_x = np.pi * self.w0_x ** 2 / self.wl
        self._zr_y = np.pi * self.w0_y ** 2 / self.wl

        propagator = propagator + self.insideout()

        if propagator[0] == 'I' or self.C_x == 0.0:
            Cobj_x = Cobj_y = 0.0
        else:
            Cobj_x = 1 / delta_z_x
            Cobj_y = 1 / delta_z_y

        delta_z_x = self.z_x - self.zw0_x
        delta_z_y = self.z_y - self.zw0_y

        if propagator[1] == 'I':
            Cima_x = Cima_y = 0.0
        else:
            Cima_x = 1 / delta_z_x
            Cima_y = 1 / delta_z_y

        self._C_x = Cima_x
        self._C_y = Cima_y

        if propagator == 'II':
            lens_phase_x = lens_phase_y = 1.0 / lens_fl
        elif propagator == 'IO':
            lens_phase_x = 1 / lens_fl + Cima_x
            lens_phase_y = 1 / lens_fl + Cima_y
        elif propagator == 'OI':
            lens_phase_x = 1.0 / lens_fl - Cobj_x
            lens_phase_y = 1.0 / lens_fl - Cobj_y
        elif propagator == 'OO':
            lens_phase_x = 1.0 / lens_fl - Cobj_x + Cima_x
            lens_phase_y = 1.0 / lens_fl - Cobj_y + Cima_y
        else:
            logger.error('Propagation direction not defined.')
            raise ValueError('Propagation direction not defined.')

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        qphase = -(xx ** 2 * lens_phase_x + yy ** 2 * lens_phase_y) * (0.5 / self.wl)

        self._fratio_x = np.abs(delta_z_x) / (2 * wz_x)
        self._fratio_y = np.abs(delta_z_y) / (2 * wz_y)
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

        assert Mx > 0.0, 'Negative magnification not implemented yet.'
        assert My > 0.0, 'Negative magnification not implemented yet.'

        self._dx *= Mx
        self._dy *= My

        if np.abs(Mx - 1.0) < 1.0e-8 or Mx is None or np.abs(My - 1.0) < 1.0e-8 or My is None:
            logger.trace('Does not do anything if magnification x is close to unity.')
            return

        logger.warning("Gaussian beam magnification is implemented, but has not been tested.")

        # Current distance to focus (before magnification)
        delta_z_x = self.z_x - self.zw0_x
        delta_z_y = self.z_y - self.zw0_y
        # Current w(z) (before magnification)
        wz_x = self.w0_x * np.sqrt(1.0 + ((self.z_x - self.zw0_x) / self.zr_x) ** 2)
        wz_y = self.w0_y * np.sqrt(1.0 + ((self.z_y - self.zw0_y) / self.zr_y) ** 2)

        # Apply magnification following ABCD Gaussian beam prescription
        # i.e. w'(z) = Mx*w(z), R'(z) = Mx**2 * R(z)

        delta_z_x *= Mx ** 2
        delta_z_y *= My ** 2
        wz_x *= Mx
        wz_y *= My
        self._w0_x *= Mx  # From Eq 56, Lawrence (1992)
        self._w0_y *= My  # From Eq 56, Lawrence (1992)
        self._zr_x *= Mx ** 2
        self._zr_y *= My ** 2
        self._zw0_x = self.z_x - delta_z_x
        self._zw0_y = self.z_y - delta_z_y
        self._fratio_x = np.abs(delta_z_x) / (2 * wz_x)
        self._fratio_y = np.abs(delta_z_y) / (2 * wz_y)

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
        delta_z_x = self.z_x - self.zw0_x
        delta_z_y = self.z_y - self.zw0_y

        delta_z_x /= n1n2
        delta_z_y /= n1n2
        self._zr_x /= n1n2
        self._zr_y /= n1n2
        self._wl *= n1n2
        self._zw0_x = self.z_x - delta_z_x
        self._zw0_y = self.z_y - delta_z_y
        self._fratio_x /= n1n2
        self._fratio_y /= n1n2

    def ptp(self, dz_x, dz_y):
        """
        Plane-to-plane (far field) wavefront propagator

        Parameters
        ----------
        dz_x: scalar
            propagation distance for sagittal component
        dz_y: scalar
            propagation distance for tangential component
        """
        if np.abs(dz_x) < 0.001 * self.wl or np.abs(dz_y) < 0.001 * self.wl:
            logger.debug('Thickness smaller than 1/1000 wavelength. Returning..')
            return

        if self.C_x != 0 or self.C_y != 0:
            logger.error("PTP wavefront should be planar")
            raise ValueError("PTP wavefront should be planar")

        wf = np.fft.ifftshift(self._wfo)
        wf = np.fft.fft2(wf, norm="ortho")
        fx = np.fft.fftfreq(wf.shape[1], d=self.dx)
        fy = np.fft.fftfreq(wf.shape[0], d=self.dy)
        fxx, fyy = np.meshgrid(fx, fy)
        qphase = (np.pi * self.wl) * (dz_x * fxx ** 2 + dz_y * fyy ** 2)
        wf = np.fft.ifft2(np.exp(-1.0j * qphase) * wf, norm="ortho")

        self._z_x = self._z_x + dz_x
        self._z_y = self._z_y + dz_y

        self._wfo = np.fft.fftshift(wf)

    def stw(self, dz_x, dz_y):
        """
        Spherical-to-waist (near field to far field) wavefront propagator

        Parameters
        ----------
        dz_x: scalar
            propagation distance for sagittal component
        dz_y: scalar
            propagation distance for tangential component
        """

        if np.abs(dz_x) < 0.001 * self.wl or np.abs(dz_y) < 0.001 * self.wl:
            logger.debug('Thickness smaller than 1/1000 wavelength. Returning..')
            return

        if self.C_x == 0.0 or self.C_y == 0.0:
            logger.error('STW wavefront should not be planar')
            raise ValueError('STW wavefront should not be planar')

        s = 'forward' if dz_x >= 0 else 'reverse'

        wf = np.fft.ifftshift(self._wfo)
        if s == 'forward':
            wf = np.fft.fft2(wf, norm="ortho")
        elif s == 'reverse':
            wf = np.fft.ifft2(wf, norm="ortho")

        fx = np.fft.fftfreq(wf.shape[1], d=self.dx)
        fy = np.fft.fftfreq(wf.shape[0], d=self.dy)
        fxx, fyy = np.meshgrid(fx, fy)

        qphase = (np.pi * self.wl) * (dz_x * fxx ** 2 + dz_y * fyy ** 2)

        self._z_x = self._z_x + dz_x
        self._z_y = self._z_y + dz_y
        self._C_x = 0.0
        self._C_y = 0.0
        self._dx = (fx[1] - fx[0]) * self.wl * np.abs(dz_x)
        self._dy = (fy[1] - fy[0]) * self.wl * np.abs(dz_y)
        self._wfo = np.fft.fftshift(np.exp(1.0j * qphase) * wf)

    def wts(self, dz_x, dz_y):
        """
        Waist-to-spherical (far field to near field) wavefront propagator

        Parameters
        ----------
        dz_x: scalar
            propagation distance for sagittal component
        dz_y: scalar
            propagation distance for tangential component
        """

        if np.abs(dz_x) < 0.001 * self.wl or np.abs(dz_y) < 0.001 * self.wl:
            logger.debug('Thickness smaller than 1/1000 wavelength. Returning..')
            return

        if self.C_x != 0.0 or self.C_y != 0.0:
            logger.error('WTS wavefront should be planar')
            raise ValueError('WTS wavefront should be planar')

        s = 'forward' if dz_x >= 0 else 'reverse'

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        qphase = (np.pi / self.wl) * (xx ** 2 / dz_x + yy ** 2 / dz_y)
        wf = np.fft.ifftshift(np.exp(1.0j * qphase) * self._wfo)
        if s == 'forward':
            wf = np.fft.fft2(wf, norm="ortho")
        elif s == 'reverse':
            wf = np.fft.ifft2(wf, norm="ortho")

        self._z_x = self._z_x + dz_x
        self._z_y = self._z_y + dz_y
        self._C_x = 1 / (self.z_x - self.zw0_x)
        self._C_y = 1 / (self.z_y - self.zw0_y)
        self._dx = self.wl * np.abs(dz_x) / (wf.shape[1] * self.dx)
        self._dy = self.wl * np.abs(dz_y) / (wf.shape[1] * self.dy)
        self._wfo = np.fft.fftshift(wf)

    def propagate(self, dz_x, dz_y):
        """
        Wavefront propagator. Selects the appropriate propagation primitive and applies the wf propagation

        Parameters
        ----------
        dz_x: scalar
            propagation distance for sagittal component
        dz_y: scalar
            propagation distance for tangential component
        """

        assert np.sign(dz_x) == np.sign(dz_y), 'Sagittal and tangential propagation distances must have the same sign.'

        insideout = self.insideout(self.z_x + dz_x, self.z_y + dz_y)
        propagator = self.insideout() + insideout

        z1_x = self.z_x
        z1_y = self.z_y
        z2_x = self.z_x + dz_x
        z2_y = self.z_y + dz_y

        if propagator == 'II':
            self.ptp(dz_x, dz_y)
        elif propagator == 'OI':
            self.stw(self.zw0_x - z1_x, self.zw0_y - z1_y)
            self.ptp(z2_x - self.zw0_x, z2_y - self.zw0_y)
        elif propagator == 'IO':
            self.ptp(self.zw0_x - z1_x, self.zw0_y - z1_y)
            self.wts(z2_x - self.zw0_x, z2_y - self.zw0_y)
        elif propagator == 'OO':
            self.stw(self.zw0_x - z1_x, self.zw0_y - z1_y)
            self.wts(z2_x - self.zw0_x, z2_y - self.zw0_y)

    def zernikes(self, index, Z, ordering, normalize, radius, offset=0.0, origin='x'):
        """
        Add a WFE represented by a Zernike expansion

        Parameters
        ----------
        index: array of integers
            Sequence of zernikes to use. It should be a continuous sequence.
        Z : array of floats
            The coefficients of the Zernike polynomials in meters
        ordering: string
            Can be 'ansi', 'noll', 'fringe'
        normalize: bool
            Polynomials are normalised to RMS=1 if True, or to unity at radius if false
        radius: float
            the radius of the circular aperture over which the polynomials are calculated
        offset: float
            angular offset in degrees
        origin: string
            angles measured counter-clockwise positive from x axis by default (origin='x').
            Set origin='y' for angles measured clockwise-positive from the y-axis.

        Returns
        -------
        out: masked array
            the WFE
        """
        assert not np.any(np.diff(index) - 1), "Zernike sequence should be continuous"

        x = (np.arange(self._wfo.shape[1]) - self._wfo.shape[1] // 2) * self.dx
        y = (np.arange(self._wfo.shape[0]) - self._wfo.shape[0] // 2) * self.dy

        xx, yy = np.meshgrid(x, y)
        rho = np.sqrt(xx ** 2 + yy ** 2) / radius

        if origin == 'x':
            phi = np.arctan2(yy, xx) + np.deg2rad(offset)
        elif origin == 'y':
            phi = np.arctan2(xx, yy) + np.deg2rad(offset)
        else:
            logger.error('Origin {} not recognised. Origin shall be either x or y'.format(origin))
            raise ValueError('Origin {} not recognised. Origin shall be either x or y'.format(origin))
        zernike = Zernike(len(index), rho, phi, ordering=ordering, normalize=normalize)
        zer = zernike()
        wfe = (zer.T * Z).T.sum(axis=0)
        self._wfo = self._wfo * np.exp(2.0 * np.pi * 1j * wfe / self._wl).filled(0)

        return wfe


if __name__ == "__main__":
    pass
