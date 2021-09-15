import numpy as np
from .paos_wfo import WFO
from .paos_abcd import ABCD
from .paos_coordinatebreak import CoordinateBreak
from copy import deepcopy
import gc

def push_results(wfo):
    retval = {'amplitude':       wfo.amplitude,              
              'wz':              wfo.wz,
              'distancetofocus': wfo.distancetofocus,
              'fratio':          wfo.fratio,
              'phase':           wfo.phase,
              'dx':              wfo.dx, 
              'dy':              wfo.dy,
              'wfo':             wfo.wfo,
              'wl':              wfo.wl,
              'extent':          wfo.extent
             }

    return retval


def run(pupil_diameter, wavelength, gridsize, zoom, field, opt_chain):
    """
    Run the POP. 
    
    Parameters
    ----------
    pupil_diameter: scalar
        input pupil diameter in meters
    wavelength: scalar
        wavelength in meters
    gridsize: scalar
        the size of the sumulation grid. It has to be a power of 2
    zoom: scalar
        zoom factor
    field: dictionary
        contains the slopes in the tangential and sagittal planes as field={'vt': slopey, 'vs': slopex}
    opt_chain: list
        the list of the optical elements returned by paos.parseconfig
    
    Returns
    -------
    out: dict
        ductionary containing the results of the POP
    """
    retval = dict()
    
    vt = np.array([0.0, field['ut']])
    vs = np.array([0.0, field['us']])

    ABCDt = ABCD()
    ABCDs = ABCD()
    
    wfo = WFO(pupil_diameter, wavelength, gridsize, zoom)
    
    for index, item in opt_chain.items():
        if item['type'] == 'Coordinate Break':
            vt, vs = CoordinateBreak(vt, vs, item['xdec'], item['ydec'], item['xrot'], item['yrot'], 0.0)

        _retval_ = {'aperture': None}

        # Check if aperture needs to be applied
        if item['type'] in ['Standard', 'Paraxial Lens', 'Slit', 'Obscuration']:
            xdec = item['xdec'] if np.isfinite(item['xdec']) else vs[0]
            ydec = item['ydec'] if np.isfinite(item['ydec']) else vt[0]
            xrad = item['xrad'] 
            yrad = item['yrad'] 
            xrad *= np.sqrt(1/(vs[1]**2+1))
            yrad *= np.sqrt(1/(vt[1]**2+1))
            xaper = xdec - vs[0]
            yaper = ydec - vt[0]
            
            aperture_shape = 'rectangular' if item['type'] == 'Slit' else 'elliptical'
            obscuration = True if item['type'] == 'Obscuration' else False
            if np.all(np.isfinite([xrad, yrad])):
                aper = wfo.aperture(xaper, yaper, hx=xrad, hy=yrad, 
                                    shape=aperture_shape, obscuration=obscuration)
                _retval_['aperture'] = aper
        
        # Check if this is a stop surface
        if item['is_stop']: wfo.make_stop()
    
        if item['type'] == 'Zernike':
            radius = item['Zradius'] if np.isfinite(item['Zradius']) else wfo.wz
            wfo.zernikes(item['Zindex'], item['Z']*item['Zwavelength'], 
                        item['Zordering'], item['Znormalize'], radius,
                        origin=item['Zorigin'])

        _retval_.update(push_results(wfo))

        Mt = item['ABCDt'].M
        fl = np.inf if (item['ABCDt'].power==0) else item['ABCDt'].cout/item['ABCDt'].power 
        T = item['ABCDt'].cout*item['ABCDt'].thickness
        n1n2 = item['ABCDt'].n1n2
        
        # Apply magnification
        if Mt != 1.0:
            wfo.Magnification(1.0, Mt)
        
        # Apply lens
        if np.isfinite(fl):
            wfo.lens(fl)
        
        if np.isfinite(T) and np.abs(T)>1e-10:
            wfo.propagate(T)
        
        vt = item['ABCDt']()@vt
        vs = item['ABCDs']()@vs
        ABCDt = item['ABCDt']*ABCDt
        ABCDs = item['ABCDs']*ABCDs
        
        _retval_['ABCDt'] = ABCDt
        _retval_['ABCDs'] = ABCDs
        
        if item['save']:
            retval[item['num']] = deepcopy(_retval_)
        del _retval_
        
    _ = gc.collect()
    
    return retval
    
    
