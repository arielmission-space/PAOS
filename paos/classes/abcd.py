import numpy as np

from paos import logger


class ABCD:
    """
    ABCD matrix class for paraxial ray tracing.

    Attributes
    ----------
    thickness: scalar
        optical thickness
    power: scalar
        optical power
    M: scalar
        optical magnification
    n1n2: scalar
        ratio of refractive indices n1/n2 for light propagating
        from a medium with refractive index n1, into a medium
        with refractive index n2
    c : scalar
        speed of light. Can take values +1 for light travelling left-to-right (+Z),
        and -1 for light travelling right-to-left (-Z)

    Note
    ----------
    The class properties can differ from the value of the parameters used at
    class instantiation. This because the ABCD matrix is decomposed into four primitives,
    multiplied together as discussed in :ref:`Optical system equivalent`.

    Examples
    --------

    >>> from paos.classes.abcd import ABCD
    >>> thickness = 2.695  # mm
    >>> radius = 31.850  # mm
    >>> n1, n2 = 1.0, 1.5
    >>> abcd = ABCD(thickness=thickness, curvature=1.0/radius, n1=n1, n2=n2)
    >>> (A, B), (C, D) = abcd.ABCD

    """

    def __init__(self, thickness=0.0, curvature=0.0, n1=1.0, n2=1.0, M=1.0):
        """
        Initialize the ABCD matrix.

        Parameters
        ----------
        thickness: scalar
            optical thickness. It is positive from left to right. Default is 0.0
        curvature: scalar
            inverse of the radius of curvature: it is positive if the center of curvature
            lies on the right. If n1=n2, the parameter is assumed describing
            a thin lens of focal ratio fl=1/curvature. Default is 0.0
        n1: scalar
            refractive index of the first medium. Default is 1.0
        n2: scalar
            refractive index of the second medium. Default is 1.0
        M: scalar
            optical magnification. Default is 1.0

        Note
        -----
        Light is assumed to be propagating from a medium with refractive index n1
        into a medium with refractive index n2.

        Note
        -----
        The refractive indices are assumed to be positive when light propagates
        from left to right (+Z), and negative when light propagates from right
        to left (-Z)
        """

        if n1 == 0 or n2 == 0 or M == 0:
            logger.error(
                "Refractive index and magnification shall not be zero"
            )
            raise ValueError(
                "Refractive index and magnification shall not be zero"
            )

        T = np.array([[1.0, thickness], [0, 1.0]])

        if n1 == n2:
            # Assume a thin lens
            D = np.array([[1.0, 0.0], [-curvature, 1.0]])
        else:
            # Assume dioptre or mirror
            D = np.array([[1.0, 0.0], [-(1 - n1 / n2) * curvature, n1 / n2]])

        M = np.array([[M, 0.0], [0.0, 1.0 / M]])

        self._ABCD = T @ D @ M

        # Remove because not needed and would break ABCD surface type when defined in lens.ini file
        # self._n1 = n1
        # self._n2 = n2
        self._cin = np.sign(n1)
        self._cout = np.sign(n2)

    @property
    def thickness(self):
        (A, B), (C, D) = self._ABCD
        return B / D

    @property
    def M(self):
        (A, B), (C, D) = self._ABCD
        return (A * D - B * C) / D

    @property
    def n1n2(self):
        (A, B), (C, D) = self._ABCD
        return D * self.M

    @property
    def power(self):
        (A, B), (C, D) = self._ABCD
        return -C / self.M

    # @property
    # def n1(self):
    #    return self._n1

    # @property
    # def n2(self):
    #    return self._n2

    @property
    def cin(self):
        return self._cin

    @cin.setter
    def cin(self, c):
        self._cin = c

    @property
    def cout(self):
        return self._cout

    @cout.setter
    def cout(self, c):
        self._cout = c

    @property
    def f_eff(self):
        return 1 / (self.power * self.M)

    @property
    def ABCD(self):
        return self._ABCD

    @ABCD.setter
    def ABCD(self, ABCD):
        self._ABCD = ABCD.copy()

    def __call__(self):
        return self._ABCD

    def __mul__(self, other):
        ABCD_new = self._ABCD @ other()
        out = ABCD()
        out.ABCD = ABCD_new
        out.cin = other.cin
        out.cout = other.cout

        return out
