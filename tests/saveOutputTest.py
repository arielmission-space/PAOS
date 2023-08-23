""" Tests all the functions in the saveOutput module using a dictionary that contains a dictionary and a numpy array.
"""

import unittest
import os
import h5py
import numpy as np
from paos.core.saveOutput import remove_keys, save_recursively_to_hdf5


class TestSaveOutput(unittest.TestCase):
    def setUp(self):
        self.my_dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        self.keys_to_drop = ['a', 'c', 'e']
        self.outgroup = h5py.File('test.hdf5', 'w')

    def test_remove_keys(self):
        remove_keys(self.my_dict, self.keys_to_drop)
        self.assertEqual(self.my_dict, {'b': 2, 'd': 4})

    def test_save_recursively_to_hdf5(self):
        save_recursively_to_hdf5(self.my_dict, self.outgroup)
        self.assertEqual(self.outgroup['a'][()], 1)
        self.assertEqual(self.outgroup['b'][()], 2)
        self.assertEqual(self.outgroup['c'][()], 3)
        self.assertEqual(self.outgroup['d'][()], 4)

    def tearDown(self):
        self.outgroup.close()
        os.remove('test.hdf5')
