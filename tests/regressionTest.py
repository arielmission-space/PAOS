import glob
import os
import time
import unittest

import h5py
import numpy as np

from paos.core.pipeline import pipeline
from paos.log import disableLogging

disableLogging()

paospath = "~/git/PAOS"
regression_dir = os.path.join(os.path.expanduser(paospath), 'tests', 'regression data')
conf_file = os.path.join(regression_dir, 'Hubble_simple.ini')


def new_out():
    """
    It runs the current PAOS version on the configuration file stored in 'regression data'.
    The new file name is updated with the current date

    Returns
    -------
    out: str
        the new file name
    """

    time_test = time.strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(regression_dir, 'regression-{}.h5'.format(time_test))

    pipeline(passvalue={'conf': conf_file,
                        'output': out_file,
                        'wavelengths': '1.0',
                        'store_keys': None})

    return out_file


class RegressionTest(unittest.TestCase):
    # looks for older PAOS file
    old_file = glob.glob(os.path.join(regression_dir, '*.h5'))

    if not old_file:
        # if no older file is in the regression data dir, a new one is produced but the test is failed
        new_out()
        raise FileNotFoundError(
            'previous run not found. New output file produced. '
            'Check your results before running the test again.')
    else:
        old_file = old_file[0]

    # produce a new ExoSim output
    print('Producing a new PAOS output')
    new_file = new_out()

    def test_content(self):
        old_f = h5py.File(self.old_file, 'r')
        new_f = h5py.File(self.new_file, 'r')

        print('iteratively checking the output dictionaries')
        # full run
        self.check_dict_key(new_f, old_f)
        old_f.close()
        new_f.close()
        os.remove(self.old_file)
        print('Test passed: old version product removed')

    def check_dict_key(self, input1, input2):
        for key in input1.keys():
            print(key)
            if key == 'info':
                continue
            if key in input2.keys():
                if isinstance(input1[key], h5py.Dataset):
                    try:
                        self.assertEqual(input1[key][()], input2[key][()])
                    except ValueError:
                        np.testing.assert_array_equal(input1[key][()],
                                                      input2[key][()])
                else:
                    self.check_dict_key(input1[key], input2[key])
            else:
                print(key, 'not in old product')
