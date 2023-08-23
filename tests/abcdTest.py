""" Tests the ABCD class in the abcd module. """

import unittest
import numpy as np
from paos.classes.abcd import ABCD


class ABCDTest(unittest.TestCase):
    """Test the ABCD class in the ABCD module.
    Runs a test for each property of the ABCD class.
    Runs a test for the __mul__ method of the ABCD class.
    Runs a test for each setter of the ABCD class."""

    def setUp(self):
        self.abcd = ABCD(1, 1)
        self.abcd.ABCD = np.array([[1, 2], [3, 4]])
        self.abcd.cin = 1
        self.abcd.cout = 1

    def test_thickness(self):
        self.assertEqual(self.abcd.thickness, 2 / 4)

    def test_M(self):
        self.assertEqual(self.abcd.M, (1 * 4 - 2 * 3) / 4)

    def test_n1n2(self):
        self.assertEqual(self.abcd.n1n2, 4 * self.abcd.M)

    def test_power(self):
        self.assertEqual(self.abcd.power, -3 / self.abcd.M)

    def test_cin(self):
        self.assertEqual(self.abcd.cin, 1)

    def test_cout(self):
        self.assertEqual(self.abcd.cout, 1)

    def test_f_eff(self):
        self.assertEqual(self.abcd.f_eff, 1 / (self.abcd.power * self.abcd.M))

    def test_ABCD(self):
        self.assertTrue(np.array_equal(self.abcd.ABCD, np.array([[1, 2], [3, 4]])))

    def test_mul(self):
        abcd = ABCD(1, 1)
        abcd.ABCD = np.array([[1, 2], [3, 4]])
        abcd2 = ABCD(1, 1)
        abcd2.ABCD = np.array([[5, 6], [7, 8]])
        abcd3 = abcd * abcd2
        self.assertTrue(np.array_equal(abcd3.ABCD, np.array([[19, 22], [43, 50]])))

    def test_cin_setter(self):
        self.abcd.cin = 2
        self.assertEqual(self.abcd.cin, 2)

    def test_cout_setter(self):
        self.abcd.cout = 2
        self.assertEqual(self.abcd.cout, 2)

    def test_ABCD_setter(self):
        self.abcd.ABCD = np.array([[5, 6], [7, 8]])
        self.assertTrue(np.array_equal(self.abcd.ABCD, np.array([[5, 6], [7, 8]])))


