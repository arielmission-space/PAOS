import numpy as np
import os, h5py
import datetime
from copy import deepcopy as dc
from .paos_config  import __author__, __version__

def remove_keys(dictionary, keys):
    for k in keys:
        dictionary.pop(k, 'key not found')
    return

def save_recursively_to_hdf5(dictionary, outgroup):
    for key, data in dictionary.items():
        if isinstance(data, dict):
            sub_outgroup = outgroup.create_group(key)
            save_recursively_to_hdf5(data, sub_outgroup)
        elif isinstance(data, (str, int, float, tuple)):
            outgroup.create_dataset(key, data=data)
        elif isinstance(data, np.ndarray):
            outgroup.create_dataset(key, data=data,
                                    shape=data.shape,
                                    dtype=data.dtype)
        elif isinstance(data, list):
            asciiList = [n.encode("ascii", "ignore") for n in data]
            outgroup.create_dataset(key, data=asciiList,
                                    shape=(len(asciiList), 1), dtype='S10')
        elif data is None:
            continue
        else:
            print(key, data)
            raise NameError('data type not supported')

def save_info(file_name, out):

    """Inspired by a similar function from ExoRad2."""

    attrs = {'file_name': file_name,
             'file_time': datetime.datetime.now().isoformat(),
             'creator': __author__,
             'HDF5_Version': h5py.version.hdf5_version,
             'h5py_version': h5py.version.version,
             'program_name': __package__.upper(),
             'program_version': __version__
            }

    infogroup = out.create_group('info')
    save_recursively_to_hdf5(attrs, infogroup)

    return

def save_retval(retval, keys_to_keep, out, verbose):
    for index in retval.keys():

        groupname = 'S{:02d}'.format(index)
        if verbose:
            print('saving {}'.format(groupname))

        item = dc(retval[index])

        if item['aperture'] is not None:
            item['aperture'] = item['aperture'].__dict__

        item['ABCDs'] = item['ABCDs'].__dict__
        item['ABCDt'] = item['ABCDt'].__dict__

        if keys_to_keep is None:
            keys_to_keep = item.keys()

        keys_to_drop = [key for key in item.keys() if key not in keys_to_keep]
        remove_keys(item, keys_to_drop)

        outgroup = out.create_group(groupname)
        save_recursively_to_hdf5(item, outgroup)

    return


def save_output(retval, file_name, keys_to_keep=None, overwrite=True, verbose=False):
    assert isinstance(retval, dict), "parameter retval must be a dict"
    assert isinstance(file_name, str), "parameter file_name must be a string"
    if keys_to_keep is not None:
        assert isinstance(keys_to_keep, list), "parameter keys_to_keep must be a list of strings"

    if verbose:
        print('saving {} started...'.format(file_name))

    if overwrite:
        if verbose:
            print('removing old file')
        if os.path.isfile(file_name):
            os.remove(file_name)

    with h5py.File(file_name, 'a') as out:
        
        save_info(file_name, out)
        save_retval(retval, keys_to_keep, out, verbose)

    if verbose:
        print('saving ended.')

    return


def save_datacube(retval_list, file_name, group_names, keys_to_keep=None, overwrite=True, verbose=False):
    assert isinstance(retval_list, list), "parameter retval_list must be a list"
    assert isinstance(file_name, str), "parameter file_name must be a string"
    assert isinstance(group_names, list), "parameter group_names must be a list of strings"
    if keys_to_keep is not None:
        assert isinstance(keys_to_keep, list), "parameter keys_to_keep must be a list of strings"

    if verbose:
        print('saving {} started...'.format(file_name))

    if overwrite:
        if verbose:
            print('removing old file')
        if os.path.isfile(file_name):
            os.remove(file_name)

    with h5py.File(file_name, 'a') as cube:

        save_info(file_name, cube)

        for groupname, retval in zip(group_names, retval_list):

            out = cube.create_group(groupname)
            if verbose:
                print('saving group {}'.format(out))

            save_retval(retval, keys_to_keep, out, verbose=False)

    if verbose:
        print('saving ended.')

    return
