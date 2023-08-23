""" Tests the Zernike class in the zernike module. """

import unittest
import numpy as np
from paos.classes.zernike import Zernike


class ZernikeTest(unittest.TestCase):
    """ Tests the Zernike class in the zernike module.
    Runs a test for the j2mn method of the Zernike class."""

    def test_j2mn(self):
        """ Tests the j2mn method of the Zernike class."""

        # Initialize the Zernike class
        zernike = Zernike(36, 0, 0, ordering='noll', normalize=True)

        # Test the j2mn method with the Noll ordering scheme
        m, n = zernike.j2mn(36, 'noll')
        print(m, n)
        np.testing.assert_array_equal(n, np.array([0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6,
                                                   6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7]))

        # Test the j2mn method with the ANSI ordering scheme
        m, n = zernike.j2mn(36, 'ansi')
        print(m, n)
        np.testing.assert_array_equal(n, np.array([0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6,
                                                    6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7]))
        np.testing.assert_array_equal(m, np.array([0, -1, 1, -2, 0, 2, -3, -1, 1, 3, -4, -2, 0, 2, 4, -5, -3, -1, 1,
                                                   3, 5, -6, -4, -2, 0, 2, 4, 6, -7, -5, -3, -1, 1, 3, 5, 7]))

        # Test the j2mn method with the Fringe ordering scheme
        m, n = zernike.j2mn(36, 'fringe')
        print(m, n)
        np.testing.assert_array_equal(n, np.array([0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6,
                                                    6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7]))

    def test_cov(self):
        """ Tests the cov method of the Zernike class."""

        # Initialize the Zernike class
        zernike = Zernike(36, 0, 0, ordering='noll', normalize=True)

        # Compute the covariance matrix of a set of Zernike polynomials
        cov = zernike.cov
        print(cov)






