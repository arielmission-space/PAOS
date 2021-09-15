import numpy as np
import pandas as pd
from .paos_abcd import ABCD


def ReadConfig(filename):
    """
    """
    parameters = {'general': {}, 'LD': None, 'field': {}}

    with pd.ExcelFile(filename, engine='openpyxl') as xls:
        wb = pd.read_excel(xls, 'General')
        for key, val in zip(wb['INIT'], wb['Value']):
            parameters['general'][key] = val
        wb = pd.read_excel(xls, 'Lens Data')
        parameters['LD'] = wb

        wb = pd.read_excel(xls, 'Fields')
        for field, x, y in zip(wb['Field'], wb['X'], wb['Y']):
            parameters['field'][str(field)] = {'us': np.tan(np.deg2rad(x)),
                                               'ut': np.tan(np.deg2rad(y))}

    return parameters


def ParseConfig(filename):
    """
    """
    parameters = ReadConfig(filename)

    n1 = None  # Refractive index
    pup_diameter = None  # input pupil pup_diameter

    opt_chain = {}

    for index, element in parameters['LD'].iterrows():

        chain_step = element['Surface num']

        if element['Ignore'] == 1:
            continue

        if element['Surface Type'] == 'INIT':
            n1 = 1.0  # propagation starts in free space
            xpup = element['XRADIUS']
            ypup = element['YRADIUS']

            if np.isfinite(xpup) and np.isfinite(ypup):
                pup_diameter = 2*max(xpup, ypup)
            else:
                raise ValueError('Pupil wrongly defined')

            continue

        if n1 is None or pup_diameter is None:
            raise ValueError('INIT is not the first surface in Lens Data.')

        _data_ = {
            'num':      element['Surface num'],
            'type':     element['Surface Type'],
            'is_stop':  True if element['Stop'] == 1 else False,
            'save':     True if element['Save'] == 1 else False,
            'name':     element['Comment'],
            'R':        element['Radius'],
            'T':        element['Thickness'],
            'material': element['Material'],
            'xrad':     element['XRADIUS'],
            'yrad':     element['YRADIUS'],
            'xdec':     element['XDECENTER'],
            'ydec':     element['YDECENTER'],
            'xrot':     element['TiltAboutX'],
            'yrot':     element['TiltAboutY'],
            'Mx':       element['MagnificationX'],
            'My':       element['MagnificationY']
        }

        if element['Surface Type'] == 'Zernike':
            sheet, stmp = element['Range'].split('.')
            colrange = ''.join([i for i in stmp if not i.isdigit()])
            rowrange = ''.join([i for i in stmp if i.isdigit() or i == ':']).split(':')
            rowstart = int(rowrange[0])
            nrows = int(rowrange[1])-rowstart+1

            with pd.ExcelFile(filename, engine='openpyxl') as xls:
                wb0 = pd.read_excel(xls, sheet, header=None, nrows=3)
                wb1 = pd.read_excel(xls, sheet, skiprows=rowstart-1, usecols='A,'+colrange, nrows=nrows, header=None)
            _data_.update({
                'Zindex':      wb1[0].to_numpy(dtype=int),
                'Z':           wb1[1].to_numpy(dtype=float),
                'Zradius':     max(_data_['xrad'], _data_['yrad']),
                'Zwavelength': float(wb0[1][0]),
                'Zordering':   wb0[1][1].lower(),
                'Znormalize':  wb0[1][2],
                'ABCDt':       ABCD(),
                'ABCDs':       ABCD(),
                'Zorigin':     'x'  # this is the default origin for the angles: from x axis, counted
                                    # positive counterclockwise
            })

            opt_chain[chain_step] = _data_

        else:
            thickness = _data_['T'] if np.isfinite(_data_['T']) else 0.0
            Mx = _data_['Mx'] if np.isfinite(_data_['Mx']) else 1
            My = _data_['My'] if np.isfinite(_data_['My']) else 1
            if _data_['type'] == 'Coordinate Break':
                C = 0.0
                n2 = n1
            elif _data_['type'] == 'Paraxial Lens':
                C = 1.0/_data_['R'] if np.isfinite(_data_['R']) else 0.0
                n2 = n1
            elif _data_['type'] in ('Standard', 'Slit', 'Obscuration'):
                C = 1.0/_data_['R'] if np.isfinite(_data_['R']) else 0.0
                if _data_['material'] == 'MIRROR':
                    n2 = -n1
                else:
                    n2 = n1  # to be modified using material ref index
            elif _data_['type'] == 'Prism':
                C = 0
                n2 = n1
            else:
                raise ValueError('Surface Type not recognised: {:s}'.format(str(_data_['type'])))

            _data_['ABCDt'] = ABCD(thickness, C, n1, n2, My)
            _data_['ABCDs'] = ABCD(thickness, C, n1, n2, Mx)

            n1 = n2
            opt_chain[chain_step] = _data_

    return pup_diameter, parameters['general'], parameters['field'], opt_chain
