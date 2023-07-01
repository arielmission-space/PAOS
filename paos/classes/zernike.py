from math import factorial as fac

import numpy as np
from scipy.special import eval_jacobi as jacobi


class Zernike:
    """
    Generates Zernike polynomials

    Parameters
    ----------
    N : integer
        Number of polynomials to generate in a sequence following the defined 'ordering'
    rho : array like
        the radial coordinate normalised to the interval [0, 1]
    phi : array like
        Azimuthal coordinate in radians. Has same shape as rho.
    ordering : string
        Can be either ANSI ordering (ordering='ansi', this is the default), or Noll ordering
        (ordering='noll'), or Fringe ordering (ordering='fringe'), or Standard (Born&Wolf) ordering (ordering='standard')
    normalize : bool
        Set to True generates ortho-normal polynomials. Set to False generates orthogonal polynomials
        as described in `Laksminarayan & Fleck, Journal of Modern Optics (2011) <https://doi.org/10.1080/09500340.2011.633763>`_.
        The radial polynomial is estimated using the Jacobi polynomial expression as in their Equation in Equation 14.


    Returns
    -------
    out : masked array
        An instance of Zernike.

    Example
    -------
    >>> import numpy as np
    >>> from matplotlib import pyplot as plt
    >>> x = np.linspace(-1.0, 1.0, 1024)
    >>> xx, yy = np.meshgrid(x, x)
    >>> rho = np.sqrt(xx**2 + yy**2)
    >>> phi = np.arctan2(yy, xx)
    >>> zernike = Zernike(36, rho, phi, ordering='noll', normalize=True)
    >>> zer = zernike() # zer contains a list of polynomials, noll-ordered

    >>> # Plot the defocus zernike polynomial
    >>> plt.imshow(zer[3])
    >>> plt.show()

    >>> # Plot the defocus zernike polynomial
    >>> plt.imshow(zernike(3))
    >>> plt.show()

    Note
    ----
    In the example, the polar angle is counted counter-clockwise positive from the
    x axis. To have a polar angle that is clockwise positive from the y axis
    (as in figure 2 of `Laksminarayan & Fleck, Journal of Modern Optics (2011) <https://doi.org/10.1080/09500340.2011.633763>`_) use

    >>> phi = 0.5*np.pi - np.arctan2(yy, xx)

    """

    def __init__(self, N, rho, phi, ordering="ansi", normalize=False):

        assert ordering in (
            "ansi",
            "noll",
            "fringe",
            "standard",
        ), "Unrecognised ordering scheme."
        assert N > 0, "N shall be a positive integer"

        self.ordering = ordering
        self.N = N
        self.m, self.n = self.j2mn(N, ordering)

        if normalize:
            self.norm = [
                np.sqrt(n + 1) if m == 0 else np.sqrt(2.0 * (n + 1))
                for m, n in zip(self.m, self.n)
            ]
        else:
            self.norm = np.ones(self.N, dtype=np.float64)

        mask = rho > 1.0
        if isinstance(rho, np.ma.MaskedArray):
            rho.mask |= mask
        else:
            rho = np.ma.MaskedArray(data=rho, mask=mask, fill_value=0.0)

        Z = {}
        for n in range(max(self.n) + 1):
            Z[n] = {}
            for m in range(-n, 1, 2):
                Z[n][m] = data = self.__ZradJacobi__(m, n, rho)
                Z[n][-m] = Z[n][m].view()

        self.Zrad = [Z[n][m].view() for m, n in zip(self.m, self.n)]

        Z = {0: np.ones_like(phi)}
        for m in range(1, self.m.max() + 1):
            Z[m] = np.cos(m * phi)
            Z[-m] = np.sin(m * phi)
        self.Zphi = [Z[m].view() for m in self.m]

        self.Z = np.ma.MaskedArray(
            [
                self.norm[k] * self.Zrad[k] * self.Zphi[k]
                for k in range(self.N)
            ],
            fill_value=0.0,
        )

    def __call__(self, j=None):
        """
        Parameters
        ----------
        j : integer
            Polynomial to return. If set to None, returns all polynomial requested at
            instantiation

        Returns
        -------
        out : masked array
          if j is set to None, the output is a masked array where the first dimension
          has the size of the number of polynomials requested.
          When j is set to an integer, returns the j-th polynomial as a masked array.
        """
        if j is None:
            return self.Z
        else:
            return self.Z[j]

    @staticmethod
    def j2mn(N, ordering):
        """
        Convert index j into azimuthal number, m, and radial number, n
        for the first N Zernikes

        Parameters
        ----------
        N: integer
            Number of polynomials (starting from Piston)
        ordering: string
            can take values 'ansi', 'standard', 'noll', 'fringe'

        Returns
        -------
        m, n: array

        """
        j = np.arange(N, dtype=int)

        if ordering == "ansi":
            n = np.ceil((-3.0 + np.sqrt(9.0 + 8.0 * j)) / 2.0).astype(int)
            m = 2 * j - n * (n + 2)
        elif ordering == "standard":
            n = np.ceil((-3.0 + np.sqrt(9.0 + 8.0 * j)) / 2.0).astype(int)
            m = -2 * j + n * (n + 2)
        elif ordering == "noll":
            index = j + 1
            n = ((0.5 * (np.sqrt(8 * index - 7) - 3)) + 1).astype(int)
            cn = n * (n + 1) / 2 + 1
            m = np.empty(N, dtype=int)
            idx = n % 2 == 0
            m[idx] = (index[idx] - cn[idx] + 1) // 2 * 2
            m[~idx] = (index[~idx] - cn[~idx]) // 2 * 2 + 1
            m = (-1) ** (index % 2) * m
        elif ordering == "fringe":
            index = j + 1
            m_n = 2 * (np.ceil(np.sqrt(index)) - 1)
            g_s = (m_n / 2) ** 2 + 1
            n = m_n / 2 + np.floor((index - g_s) / 2)
            m = (m_n - n) * (1 - np.mod(index - g_s, 2) * 2)
            return m.astype(int), n.astype(int)
        else:
            raise NameError("Ordering not supported.")

        return m, n

    @staticmethod
    def mn2j(m, n, ordering):
        """
        Convert radial and azimuthal numbers, respectively n and m, into index j
        """
        if ordering == "ansi":
            return (n * (n + 2) + m) // 2
        elif ordering == "standard":
            return (n * (n + 2) - m) // 2
        elif ordering == "fringe":
            a = (1 + (n + np.abs(m)) / 2) ** 2
            b = 2 * np.abs(m)
            c = (1 + np.sign(m)) / 2
            return (a - b - c).astype(int) + 1
        elif ordering == "noll":
            _p = np.zeros(n.size, dtype=np.int64)
            for idx, (_m, _n) in enumerate(zip(m, n)):
                if _m > 0.0 and (_n % 4 in [0, 1]):
                    _p[idx] = 0
                elif _m < 0.0 and (_n % 4 in [2, 3]):
                    _p[idx] = 0
                elif _m >= 0.0 and (_n % 4 in [2, 3]):
                    _p[idx] = 1
                elif _m <= 0.0 and (_n % 4 in [0, 1]):
                    _p[idx] = 1
                else:
                    raise ValueError("Invalid (m,n) in Noll indexing.")
            return (n * (n + 1) / 2 + np.abs(m) + _p).astype(np.int64)
        else:
            raise NameError("Ordering not supported.")

    @staticmethod
    def __ZradJacobi__(m, n, rho):
        """
        Computes the radial Zernike polynomial

        Parameters
        ----------
        m : integer
          azimuthal number
        n : integer
          radian number
        rho : array like
          Pupil semi-diameter normalised radial coordinates

        Returns
        -------
        R_mn : array like
          the radial Zernike polynomial with shape identical to rho

        """

        m = np.abs(m)

        if n < 0:
            raise ValueError(
                "Invalid parameter: n={:d} should be > 0".format(n)
            )
        if m > n:
            raise ValueError(
                "Invalid parameter: n={:d} should be larger than m={:d}".format(
                    n, m
                )
            )
        if (n - m) % 2:
            raise ValueError(
                "Invalid parameter: n-m={:d} should be a positive even number.".format(
                    n - m
                )
            )

        jpoly = jacobi((n - m) // 2, m, 0.0, (1.0 - 2.0 * rho**2))

        return (-1) ** ((n - m) // 2) * rho**m * jpoly

    @staticmethod
    def __ZradFactorial__(m, n, rho):
        """
        CURRENTLY NOT USED
        Computes the radial Zernike polynomial

        Parameters
        ----------
        m : integer
          azimuthal number
        n : integer
          radian number
        rho : array like
          Pupil semi-diameter normalised radial coordinates

        Returns
        -------
        R_mn : array like
          the radial Zernike polynomial with shape identical to rho

        """
        m = np.abs(m)

        if n < 0:
            raise ValueError(
                "Invalid parameter: n={:d} should be > 0".format(n)
            )
        if m > n:
            raise ValueError(
                "Invalid parameter: n={:d} should be larger than m={:d}".format(
                    n, m
                )
            )
        if (n - m) % 2:
            raise ValueError(
                "Invalid parameter: n-m={:d} should be a positive even number.".format(
                    n - m
                )
            )

        pre_fac = (
            lambda k: (-1.0) ** k
            * fac(n - k)
            / (fac(k) * fac((n + m) // 2 - k) * fac((n - m) // 2 - k))
        )

        return sum(
            pre_fac(k) * rho ** (n - 2 * k) for k in range((n - m) // 2 + 1)
        )

    def cov(self):
        """
        Computes the covariance matrix M defined as

        >>> M[i, j] = np.mean(Z[i, ...]*Z[j, ...])

        When a pupil is defined as :math:`\\Phi = \\sum c[k] Z[k, ...]`, the pupil RMS can be calculated as

        >>> RMS = np.sqrt( np.dot(c, np.dot(M, c)) )

        This works also on a non-circular pupil, provided that the polynomials are masked over the pupil.

        Returns
        -------
        M : array
          the covariance matrix
        """
        cov = np.empty((self.Z.shape[0], self.Z.shape[0]))
        for i in range(self.Z.shape[0]):
            for j in range(i, self.Z.shape[0]):
                cov[i, j] = cov[j, i] = np.ma.mean(self.Z[i] * self.Z[j])

        cov[cov < 1e-10] = 0.0

        return cov
