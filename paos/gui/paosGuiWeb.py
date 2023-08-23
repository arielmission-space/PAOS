import configparser
import gc
import itertools
import logging
import os
import sys
import time
from typing import List
from webbrowser import open as openwb
from astropy.io import ascii
import copy
import numpy as np

from PySimpleGUIWeb import Checkbox, Text, InputText, InputCombo, Multiline, Listbox, Button, Column, Menu, Frame, \
    Image, Slider
from PySimpleGUIWeb import Submit
from PySimpleGUIWeb import Window, WINDOW_CLOSED
from PySimpleGUIWeb import change_look_and_feel, RELIEF_RIDGE, RELIEF_SUNKEN
from PySimpleGUI import popup, popup_scrolled, popup_get_folder, popup_get_file
from PySimpleGUIWeb import version
from PySimpleGUI import OFFICIAL_PYSIMPLEGUI_THEME
from joblib import Parallel, delayed
from tqdm import tqdm
from matplotlib import pyplot as plt

from paos import parse_config, raytrace, run, save_datacube
from paos.gui.simpleGuiWeb import SimpleGUI
from paos.log import setLogLevel
from paos import __pkg_name__, __author__, __url__, __version__, base_dir, logger
from paos.core.plot import simple_plot, plot_psf_xsec


class PaosGUI(SimpleGUI):
    """
    Generates the Graphical User Interface (GUI) for `PAOS`, built using the publicly available library PySimpleGUI

    Parameters
    ----------
    passvalue: dict
        input dictionary for the GUI.
        It contains the file path to the input configuration .ini file to pass (defaults to using a template if
        unspecified), the debug and logger keywords and the file path to the output file to write.
    theme: str
        GUI theme. By default, it is set to the official PySimpleGUI theme
    font: tuple
        GUI default font. By default, it is set to ("Courier New", 16)


    Example
    -------
    >>> from paos.gui.paosGUI import PaosGui
    >>> passvalue = {'conf': '/path/to/ini/file/', 'debug': False}
    >>> PaosGui(passvalue=passvalue, theme='Dark')()

    Note
    ----
    The first implementation of PaosGui is in `PAOS` v0.0.4

    """

    def __init__(self, passvalue, theme=OFFICIAL_PYSIMPLEGUI_THEME, font=("Courier New", 16)):
        """
        Initializes the Paos GUI.
        This includes instantiating the global variables, setting up the debug logger (optional), defining the content
        to display in the main GUI Tabs and a fallback configuration file if the user did not specify it
        """

        # ------ Instantiate global variables ------ #
        super().__init__()
        self.passvalue = passvalue
        self.theme = theme
        self.font = font
        self.wavelengths = None
        self.wl_keys = None
        self.fields = None
        self.field_keys = None

        # ------ Set up the debug logger ------ #
        if self.passvalue['debug']:
            setLogLevel(logging.DEBUG)

        # ------ Theme Definition ------ #
        change_look_and_feel(self.theme)

        # ------ Tabs Definition ------ #
        # Wavelengths
        self.nrows_wl = None
        self.wl_data = {'Wavelength': ''}

        # Fields
        self.nrows_field = None
        self.field_data = {'X': '', 'Y': ''}

        # Lens data surfaces
        self.nrows_ld = None
        self.lens_data = {
            'SurfaceType': {'values': ['INIT', 'Coordinate Break', 'Standard', 'Paraxial Lens', 'ABCD', 'Zernike']},
            'Comment': {'values': 'Comment'},
            'Radius': {'values': ''},
            'Thickness': {'values': ''},
            'Material': {'values': ['', 'MIRROR', 'BK7', 'BAF2', 'CAF2', 'SAPPHIRE', 'SF11', 'ZNSE']},
            'Save': {'values': 'Save'},
            'Ignore': {'values': 'Ignore'},
            'Stop': {'values': 'Stop'},
            'aperture': {'values': {'Aperture Type': ['',
                                                      'rectangular aperture', 'rectangular obscuration',
                                                      'circular aperture', 'circular obscuration',
                                                      'elliptical aperture', 'elliptical obscuration'],
                                    'X-Half Width': '',
                                    'Y-Half Width': '',
                                    'Aperture X-Decenter': '',
                                    'Aperture Y-Decenter': ''}},
            'Par1': {'values': ''},
            'Par2': {'values': ''},
            'Par3': {'values': ''},
            'Par4': {'values': ''},
            'Par5': {'values': ''},
            'Par6': {'values': ''},
            'Par7': {'values': ''},
            'Par8': {'values': ''}}

        # ------ Define fallback configuration file ------ #
        if 'conf' not in self.passvalue.keys() or self.passvalue['conf'] is None:
            self.passvalue['conf'] = os.path.join(base_dir, 'lens data', 'lens_file_template.ini')

        # ------ Instantiate some more global variables (for dynamic updates) ------ #
        self.disable_wfe = True
        self.disable_wfe_color = ''

    def init_window(self):
        """
        Initializes the main GUI window by parsing the configuration file and initializing the input data dimensions
        """

        # ------ Set up the configuration file parser ------ #
        self.config = configparser.ConfigParser()
        if 'conf' in self.passvalue.keys() and self.passvalue['conf'] is not None:
            if not os.path.exists(self.passvalue['conf']) or not os.path.isfile(self.passvalue['conf']):
                logger.error(f'Input file {self.passvalue["conf"]} does not exist or is not a file. Quitting..')
                sys.exit()
        else:
            logger.debug('Configuration file not found. Exiting..')
            sys.exit()

        # ------ Parse the configuration file ------ #
        self.config.read(self.passvalue['conf'])

        # ------- Initialize count of wavelengths, fields and optical surfaces ------#
        self.nrows_wl = len(self.config['wavelengths']) if 'wavelengths' in self.config.keys() else 1
        self.nrows_field = len(self.config['fields']) if 'fields' in self.config.keys() else 1
        self.nrows_ld = len([key for key in self.config.keys() if key.startswith('lens')])

        # ------- Initialize keys of wavelengths, fields ------#
        self.wl_keys = [f'w{k}' for k in range(1, self.nrows_wl + 1)]
        self.field_keys = [f'f{k}' for k in range(1, self.nrows_field + 1)]

        for key, item in self.config.items():
            for subkey, subitem in item.items():
                if subkey == 'surfacetype' and subitem == 'Zernike':
                    self.disable_wfe = False
        self.disable_wfe_color = 'gray' if self.disable_wfe else 'blue'

    @staticmethod
    def get_widget(value, key, item, size=(24, 2)):
        """
        Given the cell value, key and item, returns the widget of the desired type

        Parameters
        ----------
        value: str or Iterable or dict
            value or selection of values to put inside the widget
        key: str
            key to which the returned widget will be associated
        item: bool or str
            typically, the default value to show in the widget
        size: tuple
            a tuple for the widget sizes defined as (width, height)

        Returns
        -------
        out: Checkbox or Input or Column or Combo
            the desired Widget
        """

        default = item if item != 'NaN' else None
        disabled = False if item != 'NaN' else True

        if value in ['Save', 'Ignore', 'Stop']:
            return Checkbox(text=value, default=default, key=key, size=(21, 2), disabled=disabled)
        elif value in ['Comment', 'Radius', '']:
            return InputText(default_text=default, key=key, size=size, disabled=disabled)
        elif key.startswith('aperture'):
            return InputText(default_text=default, key=key, size=size, disabled=disabled)
        else:
            return InputCombo(default_value=default, values=value, key=key, size=(23, 2), disabled=disabled,
                              enable_events=True)

    @staticmethod
    def par_heading_rules(surface_type):
        """
        Given the optical surface type, applies pre-defined rules to return the desired list of headers

        Parameters
        ----------
        surface_type: str
            the surface type (e.g. Standard)

        Returns
        -------
        out: List[str] or None
            the desired list of headers
        """

        headings = []
        if surface_type in ['INIT', 'Standard']:
            headings = ['', '', '', '', '', '', '', '']
        elif surface_type == 'Coordinate Break':
            headings = ['Xtilt', 'Ytilt', 'Xdecenter', 'Ydecenter', '', '', '', '']
        elif surface_type == 'Paraxial Lens':
            headings = ['Focal length', '', '', '', '', '', '', '']
        elif surface_type == 'ABCD':
            headings = ['Ax', 'Bx', 'Cx', 'Dx', 'Ay', 'By', 'Cy', 'Dy']
        elif surface_type == 'Zernike':
            headings = ['Wavelength', 'Ordering', 'Normalization', 'Radius of S.A.', 'Origin', '', '', '']

        return headings

    def update_headings(self, row):
        """
        Updates the displayed headers according to the rules set in :class:`~PaosGui.par_heading_rules`

        Parameters
        ----------
        row: int
            row corresponding to the optical surface in the GUI lens data editor

        Returns
        -------
        out: None
            Updates the headers
        """
        par_headings = self.par_heading_rules(self.values[f'SurfaceType_({row},0)'])
        for head, new_head in zip([key for key in self.lens_data.keys() if key.startswith('Par')], par_headings):
            self.window[head].update(new_head)

        return

    @staticmethod
    def lens_data_rules(surface_type, header, item=None):
        """
        Given the optical surface type, applies pre-defined rules to return the desired item for the widget

        Parameters
        ----------
        surface_type: str
            the surface type (e.g. Standard)
        header: str
            the column header from the lens data editor
        item: bool or str
            the item to put in the cell widget

        Returns
        -------
        out: bool or str
            the item to put in the cell widget
        """
        if surface_type == 'INIT' and header.startswith(
                ('Radius', 'Thickness', 'Material', 'Save', 'Ignore', 'Stop', 'Par')):
            item = 'NaN'

        elif surface_type == 'Coordinate Break' and (
                header.startswith(('Radius', 'Material', 'aperture'))
                or header.startswith(('Par5', 'Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        elif surface_type == 'Standard' and header.startswith('Par'):
            item = 'NaN'

        elif surface_type == 'Paraxial Lens' and (
                header.startswith(('Radius', 'Material'))
                or header.startswith(('Par2', 'Par3', 'Par4', 'Par5', 'Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        elif surface_type == 'ABCD' and header.startswith(('Radius', 'Material')):
            item = 'NaN'

        elif surface_type == 'Zernike' and (
                header.startswith(('Radius', 'Thickness', 'Material', 'aperture'))
                or header.startswith(('Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        return item

    def chain_widgets(self, row, input_list, prefix):
        """
        Given the row in the GUI lens data editor, an input list and a prefix, returns a list of widgets to fill a GUI
        editor data row

        Parameters
        ----------
        row: int
            row corresponding to the optical surface in the GUI lens data editor
        input_list: list
            items list with which to fill the new row
        prefix: str
            prefix to indicate which kind of widgets list must be returned

        Returns
        -------
        out: List[Text, List[Checkbox or Input or Column or Combo]]
            list of widgets to fill a GUI editor data row
        """
        row_widget = [Text(row, size=(6, 1), key=f'row idx {row}')]

        if prefix == 'w':
            key = f'{prefix}{row}'
            item = self.config['wavelengths'].get(key, '')
            return list(itertools.chain(row_widget,
                                        [self.get_widget(value, key, item) for value in input_list]))

        elif prefix == 'f':
            key = f'{prefix}{row}'
            items = self.config['fields'].get(key, '0.0,0.0').split(',')
            keys = ['_'.join([key, str(i)]) for i in range(len(items))]
            return list(itertools.chain(row_widget,
                                        [self.get_widget(value, key, item) for value, key, item in
                                         zip(input_list, keys, items)]))

        elif prefix == 'l':
            key = 'lens_{:02d}'.format(row)

            lens_dict = {}
            for c, name in enumerate(self.lens_data.keys()):
                name_key = f'{name}_({row},{c})'
                if key in self.config.keys() and name in self.config[key].keys():
                    lens_dict[name_key] = self.config[key].getboolean(name) \
                        if name in ['Save', 'Ignore', 'Stop'] else self.config[key][name]
                else:
                    lens_dict[name_key] = None

                surface_type_key = f'SurfaceType_({row},0)'
                surface_type = lens_dict[surface_type_key]
                lens_dict[name_key] = self.lens_data_rules(surface_type=surface_type, header=name_key,
                                                           item=lens_dict[name_key])

            return list(itertools.chain(row_widget,
                                        [self.get_widget(value, key, item)
                                         for value, (key, item) in zip(input_list, lens_dict.items())]))

    def save_to_dict(self, show=True):
        """
        Saves the data content from the GUI input Tabs (General, Fields, Lens Data) to a dictionary

        Parameters
        ----------
        show: bool
            If True, displays a popup window with the output dictionary that can be copied to the local clipboard.
            If False, returns the output dictionary.

        Returns
        -------
        out: dict or None
            the GUI input content as a dictionary
        """

        # ------- Get general data ------#
        dictionary = {'general': {
            'project': self.values['project'],
            'version': self.values['version'],
            'grid_size': self.values['grid_size'],
            'zoom': self.values['zoom'],
            'lens_unit': self.values['lens_unit'],
            'Tambient': self.values['tambient'],
            'Pambient': self.values['pambient']
        }}

        # ------- Get wavelengths data ------#
        key = 'wavelengths'
        dictionary[key] = {}
        for k in range(1, self.nrows_wl + 1):
            if self.values[f'w{k}'] != '':
                dictionary[key][f'w{k}'] = self.values[f'w{k}']

        # ------- Get fields data ------#
        key = 'fields'
        dictionary[key] = {}
        for k in range(1, self.nrows_field + 1):
            fields = [self.values[f'f{k}_{c}'] for c in range(len(self.field_data.keys()))]
            dictionary[key][f'f{k}'] = ','.join(map(str, fields))

        # ------- Get lens data editor data ------#
        for k in range(1, self.nrows_ld + 1):
            key = 'lens_{:02d}'.format(k)
            dictionary[key] = {}
            for (c, head) in enumerate(self.lens_data.keys()):
                section = dictionary[key]
                if head == 'aperture':
                    section[head] = ','.join([self.values[f'{name_key.replace(" ", "_")}_({k},{c})']
                                              for name_key in self.lens_data['aperture']['values'].keys()])
                    if section[head] == len(section[head]) * ',':
                        section[head] = ''
                else:
                    section[head] = self.values[f'{head}_({k},{c})']
                    if section[head] == 'Zernike':
                        section['zindex'] = self.config[key].get('zindex', '0')
                        section['z'] = self.config[key].get('z', '0')
                dictionary[key].update(section)

        if show:
            popup_scrolled(f'lens_data = {dictionary}')
            return
        else:
            return dictionary

    def to_ini(self, filename=None, temporary=False):
        """
        Given the output .ini file path, it writes the data content from the GUI input Tabs to it

        Parameters
        ----------
        filename: str or None
            if not given, writes to the current .ini configuration file
        temporary: bool
            if True, the .ini file is temporary and is deleted upon exiting the GUI

        Returns
        -------
        out: None
            writes the data content from the GUI input Tabs to a .ini file
        """
        config = self.to_configparser(dictionary=self.save_to_dict(show=False))

        if filename is not None:
            if not os.path.exists(filename) or not os.path.isfile(filename):
                logger.error(f'Input file {filename} does not exist or is not a file. Quitting..')
                sys.exit()
        elif temporary:
            self.temporary_config = filename = \
                os.path.join(os.path.dirname(self.passvalue['conf']),
                             ''.join(['temp_', os.path.basename(self.passvalue['conf'])]))
        else:
            filename = self.passvalue['conf']

        with open(filename, 'w') as cf:
            config.write(cf)
        return

    @staticmethod
    def plot_surface(key, retval, ima_scale):
        """
        Given the optical surface key, the POP output dictionary and the image scale, plots the squared amplitude
        of the wavefront at the given surface (cross-sections and 2D plot)

        Parameters
        ----------
        key: int
            the key index associated to the optical surface
        retval: dict
            the POP output dictionary
        ima_scale: str
            the image scale. Can be either 'linear' or 'log'

        Returns
        -------
        out: :class:`~matplotlib.figure.Figure`
            the figure with the squared amplitude of the wavefront at the given surface

        """

        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
        # Xsec plot
        plot_psf_xsec(fig=fig, axis=axs[0], key=key, item=retval[key], ima_scale=ima_scale)
        # 2D plot
        simple_plot(fig=fig, axis=axs[1], key=key, item=retval[key], ima_scale=ima_scale)
        fig.suptitle(axs[0].get_title(), fontsize=20)
        axs[0].set_title('X-sec view')
        axs[1].set_title('2D view')
        fig.tight_layout()

        return fig

    def draw_surface(self, retval_list, groups, figure_agg, image_key, surface_key, scale_key, range_key=None):
        """
        Given a list of simulation output dictionaries, the names to associate to each simulation, the Figure element
        to draw on and its key, the key for the surface to plot and the plot scale, plots at the given optical surface
        and returns the figure(s) produced

        Parameters
        ----------
        retval_list: List of dict
            list of simulation output dictionaries
        groups: List of str
            names to associate to each simulation in the output
        figure_agg: Figure
            element Figure to draw on
        image_key: str
            Figure element key
        surface_key: str
            key associated to the surface to plot
        scale_key: str
            plot scale. Can be either 'linear' or 'log'
        range_key: str
            range of simulations to plot.
            Examples:
            0) '0,1' means only the first simulation is plotted
            1) '0,10' means that the first ten simulations are plotted
            If the number of simulations to plot is greater than len(retval_list), plots all the simulations and
            nothing bad happens

        Returns
        -------
        out: None or :class:`~matplotlib.figure.Figure` or List[:class:`~matplotlib.figure.Figure`]
             or (List[:class:`~matplotlib.figure.Figure`], List[int])
            Plots at the given optical surface and returns the figure(s)

        Notes
        -----
        Do not plot too many figures (> 20) at a time, otherwise they may occupy too much memory, and you will get
        a warning from matplotlib for reached maximum number of opened figures
        """

        # Close all previous plots
        plt.close('all')

        if figure_agg is not None:
            # Reset figure canvas
            self.clear_image(self.window[image_key])
        # Get surface to plot
        key = int(self.values[surface_key][1:])
        # Get image scale
        ima_scale = self.values[scale_key].partition(' ')[0]
        if 'nwl' in image_key or 'wfe' in image_key:
            sim_range = self.values[range_key].split('-')
            n_min, n_max = list(map(int, sim_range))
            n_max = min(n_max, len(retval_list))
            # Update plot slider
            figure_list = []
            j = n_min
            idx = []
            while j < n_max:
                group, ret = groups[j], retval_list[j]
                # Check that surface is stored in POP output
                if key not in ret.keys():
                    logger.error('Surface not present in POP output: it was either ignored or simply not saved')
                    break
                # Plot
                logger.debug(f'Plotting POP for group {group}')
                figure_list.append(self.plot_surface(key, ret, ima_scale))
                # Get the index of the plotted figures
                idx.append(j)
                j += 1
            if 'nwl' in image_key:
                self.window['-Slider (nwl)-'].update(range=(0, n_max - n_min - 1))
            elif 'wfe' in image_key:
                self.window['-Slider (wfe)-'].update(range=(0, n_max - n_min - 1))
            return figure_list, idx
        else:
            ret = retval_list[0]
            # Check that surface is stored in POP output
            if key not in ret.keys():
                logger.error('Surface not present in POP output: it was either ignored or simply not saved')
                return
            # Plot
            fig = self.plot_surface(key, ret, ima_scale)
            return fig

    def display_plot_slide(self, figure_list, figure_agg, image_key, slider_key):
        """
        Given a list of figures, a figure canvas, the image key and the slider key, returns the updated Image element

        Parameters
        ----------
        figure_list: List of :class:`~matplotlib.figure.Figure`
            a list of matplotlib figures
        figure_agg: Canvas
            the figure Canvas
        image_key: str
            the Image key
        slider_key:
            the Slider key

        Returns
        -------
        out: None or Canvas
            the updated Image element

        """
        if not figure_list:
            logger.debug('Plot POP first')
            return
        if figure_agg is not None:
            # Reset figure canvas
            self.clear_image(self.window[image_key])
        # Get the simulation index
        n = int(self.values[slider_key])
        # Draw the image
        figure_agg = self.draw_image(figure=figure_list[n], element=self.window[image_key])
        return figure_agg

    @staticmethod
    def save_figure(figure, filename=None):
        """
        Given a matplotlib figure and a file path (optional), saves the figure to the file path

        Parameters
        ----------
        figure: :class:`~matplotlib.figure.Figure`
            the matplotlib figure to save
        filename: str
            the saving file path

        Returns
        -------
        out: None
            Saves the matplotlib figure

        """
        if figure is None:
            logger.debug('Create plot first')
            return

        if filename is None:
            # Get the file path to save to
            filename = popup_get_file('Choose file (PNG, JPG) to save to', save_as=True, keep_on_top=True)

            if filename is None:
                logger.debug('Pressed Cancel. Continuing...')
                return

            if not filename.endswith(('.PNG', '.png', '.JPG', '.jpg')):
                logger.warning('Saving file format not provided. Defaulting to .png')
                filename = ''.join([filename, '.png'])

        # Save the plot to the specified .png or .jpg file
        figure.savefig(filename, bbox_inches='tight', dpi=150)

        logger.debug(f'Saved figure to {filename}')

        return

    @staticmethod
    def to_hdf5(retval_list, groups, keys_to_keep=None):
        """
        Given the POP output dictionary list, the names for each simulation (saving groups) and the keys to store,
        opens a popup to get the output file name and then dumps the simulation outputs to a hdf5 file.

        Parameters
        ----------
        retval_list: List of dict
            list of simulation output dictionaries
        groups: List of strings
            names to associate to each simulation in the output
        keys_to_keep: List of strings
            dictionary keys to store

        Returns
        -------
        out: None
            Dumps the simulation output to the indicated hdf5 file

        """

        if keys_to_keep is None:
            keys_to_keep = ['amplitude', 'dx', 'dy', 'wl']

        if not retval_list:
            logger.debug('Run POP first')
            return

        # Get the file path to save to
        filename = popup_get_file('Choose file (HDF5) to save to', save_as=True, keep_on_top=True)

        if filename is None:
            logger.debug('Pressed Cancel. Continuing...')
            return

        if not filename.endswith(('.HDF5', '.hdf5', '.H5', '.h5')):
            logger.warning('Saving file format not provided. Defaulting to .h5')
            filename = ''.join([filename, '.h5'])

        # Save the POP output to the specified .hdf5 file
        tags = list(map(str, groups))
        save_datacube(retval_list, filename, tags, keys_to_keep=keys_to_keep, overwrite=True)
        return

    @staticmethod
    def to_txt(text_list):
        """
        Given a list of strings, opens a popup to get the output file name and then dumps the text ordered in rows
        to the output text file

        Parameters
        ----------
        text_list: list of strings

        Returns
        -------
        out: None
            writes the input text list to a text file.
            Used to save the output of the diagnostic raytrace

        """

        if text_list == '':
            logger.debug('Perform raytrace first')
            return

        # Get the file path to save to
        filename = popup_get_file('Choose file (TXT) to save to', save_as=True, keep_on_top=True)

        if filename is None:
            logger.debug('Pressed Cancel. Continuing...')
            return

        if not filename.endswith(('.TXT', '.txt')):
            logger.warning('Saving file format not provided. Defaulting to .txt')
            filename = ''.join([filename, '.txt'])

        # Save the text list to the specified .txt file
        with open(filename, "wt") as f:
            f.write('\n'.join(text_list))
        return

    def make_window(self):
        """
        Generates the main GUI window. The layout is composed of 5 Tabs, the first one for the general input parameters
        and the wavelengths, the second one for the input fields, the third one for the optical data surfaces, the
        fourth one for the simulation launcher (diagnostic raytrace, POP and plots) and the last one for the general
        info on the GUI and its developers. Defines also some pretty cursors and binds the method to update the headings

        Returns
        -------
        out: None
            Generates the main GUI window
        """

        # ------ Initialize window ------ #
        self.init_window()

        # ------ Define main Tabs layout ------ #
        # # Define general layout
        general_layout = [
            [Frame('General Setup', layout=[
                [Text('', size=(24, 1))],
                [Text('Project Name:', size=(24, 1)),
                 InputText(self.config['general'].get('project', ''), do_not_clear=True,
                           tooltip='Insert project name', key='project', size=(80, 1))],
                [Text('Comment:', size=(24, 1)),
                 InputText(self.config['general'].get('comment', ''),
                           tooltip='Insert comment', key='comment', size=(80, 1))],
                [Text('Version:', size=(24, 1)),
                 InputText(self.config['general'].get('version', ''),
                           tooltip='Insert project version tag', key='version', size=(24, 1))],
                [Text('Grid Size:', size=(24, 1)),
                 InputCombo(values=['64', '128', '512', '1024'],
                            default_value=self.config['general'].getint('grid_size', 512), key='grid_size',
                            size=(24, 1))],
                [Text('Zoom:', size=(24, 1)),
                 InputCombo(values=['1', '2', '4', '8', '16'],
                            default_value=self.config['general'].getint('zoom', 4), key='zoom', size=(24, 1))],
                [Text('Lens unit:', size=(24, 1)),
                 InputText(self.config['general'].get('lens_unit', ''), key='lens_unit', size=(24, 1), disabled=True)],
                [Text('Angles unit:', size=(24, 1)),
                 InputText('degrees', size=(24, 1), key='angle_units', disabled=True)],
                [Text('Wavelengths unit:', size=(24, 1)),
                 InputText('micrometers', size=(24, 1), key='lambda_units', disabled=True)],
                [Text('T ambient:', size=(24, 1)),
                 InputText(self.config['general'].get('Tambient', ''),
                           tooltip='Insert ambient temperature', key='tambient', size=(24, 1))],
                [Text('T unit:', size=(24, 1)),
                 InputText('(°C)', key='T_unit', size=(24, 1), disabled=True)],
                [Text('P ambient:', size=(24, 1)),
                 InputText(self.config['general'].get('Pambient', ''),
                           tooltip='Insert ambient pressure', key='pambient', size=(24, 1))],
                [Text('P unit:', size=(24, 1)),
                 InputText('(atm)', key='P_unit', size=(24, 1), disabled=True)],
                [Text('', size=(24, 1))]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='GENERAL FRAME')],
            [Frame('Wavelength Setup', layout=[
                [Text('', size=(24, 1))],
                [Column(layout=list(itertools.chain(
                    [self.add_heading(self.wl_data.keys())],
                    [self.chain_widgets(r, [item for key, item in self.wl_data.items()], prefix='w')
                     for r in range(1, self.nrows_wl + 1)])),
                    key='wavelengths', scrollable=True, vertical_scroll_only=True)]
            ],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='WL FRAME',
                   element_justification='top')],
        ]
        # Define fields layout
        fields_layout = [
            [Column(layout=list(itertools.chain(
                [self.add_heading(self.field_data.keys())],
                [self.chain_widgets(r, [item for key, item in self.field_data.items()], prefix='f')
                 for r in range(1, self.nrows_field + 1)])),
                scrollable=True, vertical_scroll_only=True, key='fields')],
        ]
        # Define lens data layout
        lens_data_layout = [
            [Column(layout=list(itertools.chain(
                [self.add_heading(self.lens_data.keys())],
                [[Text('')]],
                [self.chain_widgets(r, [item['values'] for key, item in self.lens_data.items()], prefix='l')
                 for r in range(1, self.nrows_ld + 1)])),
                scrollable=True, key='lenses')],
        ]
        # Define launcher layout
        launcher_layout = [list(itertools.chain(
            [Frame('Select inputs', layout=[
                list(itertools.chain(
                    [Text('Select wavelength', size=(12, 2)),
                     Listbox(default_values=['w1'],
                             values=[key for key, item in self.config.items('wavelengths')],
                             size=(12, 4), background_color='grey20', key='select wl',
                             enable_events=True)],
                    [Text('', size=(5, 2))],
                    [Text('Select field', size=(12, 2)),
                     Listbox(default_values=['f1'],
                             values=[key for key, item in self.config.items('fields')],
                             size=(12, 4), background_color='grey20', key='select field', enable_events=True)]))],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='INPUTS FRAME')
             ],
            [Text('', size=(100, 2))],
            [Frame('Save', layout=[
                [Button(tooltip='Save raytrace output', button_text='Save raytrace', enable_events=True,
                        key="-SAVE RAYTRACE-")],
                [Button(tooltip='Save the POP output', button_text='Save POP', enable_events=True, key="-SAVE POP-")],
                [Button(tooltip='Save the plot', button_text='Save Plot', enable_events=True, key="-SAVE FIG-")]
            ],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='PAOS SAVE FRAME')
             ])),
            [Frame('Raytrace', layout=[
                [Text('Run a diagnostic raytrace')],
                [Button(tooltip='Launch raytrace', button_text='Raytrace', enable_events=True, key="-RAYTRACE-")],
                [Column(layout=[
                    [Multiline(key='raytrace log', font=self.font_small, autoscroll=True, size=(60, 20),
                               background_color='grey20', disabled=False)]],
                    key='raytrace log col')]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='PAOS RAYTRACE FRAME'),
             Text('', size=(5, 2)),
             Frame('POP', layout=[
                 list(itertools.chain(
                     [Text('Run the POP: '),
                      Button(tooltip='Launch POP', button_text='POP', enable_events=True, key="-POP-")],
                     [Text('', size=(6, 2))],
                     [Text('Plot surface: '),
                      InputCombo(tooltip='Surface number', values=[f'S{k}' for k in range(1, self.nrows_ld + 1)],
                                 default_value=f'S{self.nrows_ld}', key="S#"),
                      InputCombo(tooltip='Color scale', values=['linear scale', 'log scale'], default_value='log scale',
                                 key="Ima scale"),
                      Button(tooltip='Plot', button_text='Plot', enable_events=True, key="-PLOT-")])),
                 [Image(key='-IMAGE-')]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='PAOS POP FRAME')
             ]
        ]
        # Define parallel launcher layout
        monte_carlo_layout = [
            [Column(layout=[
                [Text('', size=(6, 1))],
                [Button(self.symbol_up, enable_events=True, disabled=False,
                        key='-OPEN FRAME MC (nwl)-', font=self.font_small, size=(2, 1)),
                 Text('MC Wavelengths', size=(20, 1), text_color='yellow', key='-FRAME TITLE MC (nwl)-',
                      font=self.font_titles, relief=RELIEF_SUNKEN)],
                [Column(layout=[[self.collapse_frame(title='', layout=[
                    [Frame('Select inputs', layout=[
                        [Text('Select field', size=(12, 2)),
                         Listbox(default_values=['f1'],
                                 values=[key for key, item in self.config.items('fields')],
                                 size=(12, 4), background_color='grey20', key='select field (nwl)',
                                 enable_events=True)]], font=self.font_subtitles, relief=RELIEF_SUNKEN,
                           key='INPUTS FRAME (nwl)')],
                    list(itertools.chain(
                        [Frame('Run and Save', layout=[
                            [Text('', size=(6, 2))],
                            [Text('Number of parallel jobs: ', size=(30, 1)),
                             InputText(tooltip='Number of jobs', default_text=2, key="NJOBS (nwl)")],
                            [Text('Run the multi-wl POP: ', size=(30, 1)),
                             Button(tooltip='Launch POP', button_text='POP', enable_events=True,
                                    key="-POP (nwl)-"),
                             Text('', size=(40, 1), relief='sunken',
                                  text_color='yellow', background_color='black', key='progbar (nwl)', metadata=0)],
                            [Text('Save the POP output: ', size=(30, 1)),
                             Button(tooltip='Save the POP output', button_text='Save POP', enable_events=True,
                                    key="-SAVE POP (nwl)-")],
                            [Text('', size=(6, 2))],
                            [Text('Range to plot: ', size=(30, 1)),
                             InputText(tooltip='Select sim range to plot', default_text='0-1', key="RANGE (nwl)")],
                            [Text('Plot surface: ', size=(30, 1)),
                             InputCombo(tooltip='Surface number',
                                        values=[f'S{k}' for k in range(1, self.nrows_ld + 1)],
                                        default_value=f'S{self.nrows_ld}', key="S# (nwl)"),
                             InputCombo(tooltip='Color scale', values=['linear scale', 'log scale'],
                                        default_value='log scale', key="Ima scale (nwl)"),
                             Button(tooltip='Plot', button_text='Plot', enable_events=True,
                                    key="-PLOT (nwl)-")],
                            [Text('Figure prefix: ', size=(30, 1)),
                             InputText(tooltip='Figure prefix', default_text='Plot', key="Fig prefix (nwl)")],
                            [Text('Save the Plots', size=(30, 1)),
                             Button(tooltip='Save the plots', button_text='Save Plot', enable_events=True,
                                    key="-SAVE FIG (nwl)-")]],
                               font=self.font_subtitles, relief=RELIEF_SUNKEN,
                               key='-RUN AND SAVE FRAME (nwl)-')],
                        [Frame('Display', layout=[
                            [Text('', size=(6, 1))],
                            [Button(tooltip='Display plot', button_text='Display plot', enable_events=True,
                                    key="-DISPLAY PLOT (nwl)-"),
                             Text('', size=(2, 1)),
                             Slider(range=(0, 10), orientation='horizontal', size=(40, 15), default_value=0,
                                    key='-Slider (nwl)-', enable_events=True)],
                            [Image(key='-IMAGE (nwl)-')]],
                               font=self.font_subtitles, relief=RELIEF_SUNKEN,
                               key='IMAGE FRAME (nwl)')],
                    ))
                ], key='FRAME MC (nwl)')]])],
                [Text('', size=(6, 2))],
                [Button(self.symbol_up, enable_events=True, disabled=self.disable_wfe,
                        key='-OPEN FRAME MC (wfe)-', font=self.font_small, size=(2, 1)),
                 Text('MC Wavefront error', size=(20, 1), text_color=self.disable_wfe_color,
                      key="-FRAME TITLE MC (wfe)-", font=self.font_titles, relief=RELIEF_SUNKEN)],
                [Column(layout=[[self.collapse_frame(title='', layout=[
                    [Frame('Select inputs', layout=[
                        list(itertools.chain(
                            [Text('Select wavelength', size=(12, 2)),
                             Listbox(default_values=['w1'],
                                     values=[key for key, item in self.config.items('wavelengths')],
                                     size=(12, 4), background_color='grey20', key='select wl (wfe)',
                                     enable_events=True)],
                            [Text('', size=(5, 2))],
                            [Text('Select field', size=(12, 2)),
                             Listbox(default_values=['f1'],
                                     values=[key for key, item in self.config.items('fields')],
                                     size=(12, 4), background_color='grey20', key='select field (wfe)',
                                     enable_events=True)]
                        ))], key='INPUTS FRAME (wfe)', font=self.font_subtitles, relief=RELIEF_SUNKEN)],
                    list(itertools.chain(
                        [Frame('Run and Save', layout=[
                            [Text('', size=(6, 2))],
                            [Text('Import Wavefront error table: ', size=(30, 1)),
                             Button(tooltip='Import wfe table', button_text='Import wfe', enable_events=True,
                                    key="-IMPORT WFE-")],
                            [Text('Unit of Zernike coefficients: ', size=(30, 1)),
                             InputText(tooltip='Zernike unit (-9=nm)', default_text='-9', key="ZUNIT (wfe)")],
                            [Text('', size=(6, 2))],
                            [Text('Number of parallel jobs: ', size=(30, 1)),
                             InputText(tooltip='Number of jobs', default_text=2, key="NJOBS (wfe)")],
                            [Text('Index of Zernike surface: ', size=(30, 1)),
                             InputText(tooltip='Index of Zernike', default_text='', key="NSURF (wfe)")],
                            [Text('Run the POP for each wfe: ', size=(30, 1)),
                             Button(tooltip='Launch POP', button_text='POP', enable_events=True, key="-POP (wfe)-"),
                             Text('', size=(40, 1), relief='sunken',
                                  text_color='yellow', background_color='black', key='progbar (wfe)', metadata=0)],
                            [Text('Save the POP output: ', size=(30, 1)),
                             Button(tooltip='Save the POP output', button_text='Save POP', enable_events=True,
                                    key="-SAVE POP (wfe)-")],
                            [Text('', size=(6, 2))],
                            [Text('Range to plot: ', size=(30, 1)),
                             InputText(tooltip='Select sim range to plot', default_text='0-1', key="RANGE (wfe)")],
                            [Text('Plot surface: ', size=(30, 1)),
                             InputCombo(tooltip='Surface number',
                                        values=[f'S{k}' for k in range(1, self.nrows_ld + 1)],
                                        default_value=f'S{self.nrows_ld}', key="S# (wfe)"),
                             InputCombo(tooltip='Color scale', values=['linear scale', 'log scale'],
                                        default_value='log scale', key="Ima scale (wfe)"),
                             Button(tooltip='Plot', button_text='Plot', enable_events=True,
                                    key="-PLOT (wfe)-")],
                            [Text('Figure prefix: ', size=(30, 1)),
                             InputText(tooltip='Figure prefix', default_text='Wfe', key="Fig prefix (wfe)")],
                            [Text('Save the Plots', size=(30, 1)),
                             Button(tooltip='Save the plots', button_text='Save Plot', enable_events=True,
                                    key="-SAVE FIG (wfe)-")]],
                               font=self.font_subtitles, relief=RELIEF_SUNKEN,
                               key='-RUN AND SAVE FRAME (wfe)-'
                               )],
                        [Frame('Display', layout=[
                            [Text('', size=(6, 1))],
                            [Button(tooltip='Display plot', button_text='Display plot', enable_events=True,
                                    key="-DISPLAY PLOT (wfe)-"),
                             Text('', size=(2, 1)),
                             Slider(range=(0, 10), orientation='horizontal', size=(40, 15), default_value=0,
                                    key='-Slider (wfe)-', enable_events=True)],
                            [Image(key='-IMAGE (wfe)-')]],
                               font=self.font_subtitles, relief=RELIEF_SUNKEN,
                               key='-IMAGE FRAME (wfe)-'
                               )]
                    ))
                ], key='FRAME MC (wfe)')]])],
            ], scrollable=True, key='MC LAUNCHER COL')]
        ]

        # Define info layout
        info_layout = [
            [Frame('GUI Info', layout=[
                [Text(f'Credits: {__author__}', key='-CREDITS-')],
                [Text(f'{__pkg_name__.upper()} version: {__version__}', key='-PAOS VERSION-')],
                [Text('')],
                [Text('Github Repo: ')],
                [Text(f'{__url__}', font=self.font_underlined, text_color='blue', enable_events=True, key='-LINK-')],
                [Text('')],
                [Text(f'PySimpleGui version: {version}', key='-GUI VERSION-')]], font=self.font_titles,
                   relief=RELIEF_SUNKEN, key='-INFO FRAME-')]
        ]

        # ------ Define GUI layout ------ #
        layout = [
            [Menu(self.menu_def, tearoff=True, key="-MENU-")],
            [Text('Configuration Tabs', size=(38, 1), justification='center', relief=RELIEF_RIDGE, key="-TEXT HEADING-",
                  enable_events=True)],
            [Frame('General', general_layout, key="-GENERAL TAB-", element_justification='center')],
            [Frame('Fields', fields_layout, key="-FIELDS TAB-", element_justification='center')],
            [Frame('Lens Data', lens_data_layout, key="-LENS DATA TAB-", element_justification='center')],
            [Frame('Launcher', launcher_layout, key="-LAUNCHER TAB-")],
            [Frame('Monte Carlo', monte_carlo_layout, key="-MC LAUNCHER TAB-")],
            [Frame('Info', info_layout, key="-INFO TAB-")],
            [
                Submit(tooltip='Click to submit (debug)', key='-SUBMIT-'),
                Button(tooltip='Click to show dict', button_text='Show Dict', key="-SHOW DICT-"),
                Button(tooltip='Click to copy dict to clipboard', button_text='Copy to clipboard',
                       key="-TO CLIPBOARD-"),
                Button(tooltip='Save to ini file', button_text='Save', key="-SAVE-"),
                Button('Exit', key='-EXIT-')
            ]
        ]

        # ------ Window creation ------ #
        self.window = Window('PAOS Configuration GUI', layout, default_element_size=(12, 1),
                             element_padding=(1, 1), return_keyboard_events=True, finalize=True,
                             font=self.font, element_justification='left')

        # # ------- Bind method for Par headings ------#
        # for r, (c, head) in itertools.product(range(1, self.nrows_ld + 1), enumerate(self.lens_data.keys())):
        #     self.window[f'{head}_({r},{c})'].bind("<Button-1>", "_LeftClick")

        return

    def __call__(self):
        """
        Returns a rendering of the GUI window and handles the event loop.
        """

        # ------ Generate the main GUI window ------ #
        self.make_window()

        # ------ Instantiate local variables ------ #
        raytrace_log = ''
        retval, retval_list, saving_groups = {}, [], []
        figure, figure_list_nwl, figure_list_wfe = None, [], []
        fig_agg, fig_agg_nwl, fig_agg_wfe = None, None, None
        idx_nwl, idx_wfe = [], []
        save_to_ini_file = False

        # ------ Instantiate more local variables for dynamic interface ------ #
        wfe_realizations_file = None

        pop = ''

        while True:  # Event Loop

            # ------- Read the current window ------#
            self.event, self.values = self.window.Read()
            logger.debug(f'============ Event = {self.event} ==============')

            # # ------- Save to temporary configuration file ------#
            # self.to_ini(temporary=True)

            # ------- Save (optional) and properly close the current window ------#
            if self.event in (WINDOW_CLOSED, 'Exit', '-EXIT-'):
                # Save back to the configuration file
                if save_to_ini_file:
                    self.to_ini()
                # Clear simulation outputs
                del retval, figure
                retval, figure = {}, None
                retval_list.clear()
                figure_list_nwl.clear()
                figure_list_wfe.clear()
                for image_key in ['-IMAGE-', '-IMAGE (nwl)-', '-IMAGE (wfe)-']:
                    self.clear_image(self.window[image_key])
                # Close the current window
                self.close_window()
                break

            # ------- Display a popup window with the output dictionary ------#
            elif self.event == '-SHOW DICT-':
                # Show GUI window contents as a dict
                self.save_to_dict(show=True)

            # ------- Update 'Select wavelength' or 'Select field' Listbox widget in the Launcher tab ------#
            elif self.event in ['select wl', 'select field']:
                # Reset previous outputs
                del retval, figure
                retval, figure = {}, None
                retval_list.clear()
                # Reset figure canvas
                self.clear_image(self.window['-IMAGE-'])
                if self.event == 'select field':
                    # Update the raytrace log Column
                    raytrace_log = ''
                    self.window['raytrace log'].update(raytrace_log)
                _ = gc.collect()

            # ------- Update 'Select field' Listbox widget in MC Wavelengths frame ------#
            elif self.event == 'select field (nwl)':
                # Reset POP simulation output
                retval_list.clear()
                # Reset figure
                figure_list_nwl.clear()
                # Reset figure canvas
                self.clear_image(self.window['-IMAGE (nwl)-'])
                # Reset progress bar
                _ = self.reset_progress_bar(self.window['progbar (nwl)'])
                _ = gc.collect()

            # ------- Update 'Select wavelength' or 'Select field' Listbox widget in MC Wavefront error frame ------#
            elif self.event in ['select wl (wfe)', 'select field (wfe)']:
                # Reset POP simulation output
                retval_list.clear()
                # Reset figures
                figure_list_wfe.clear()
                # Reset figure canvas
                self.clear_image(self.window['-IMAGE (wfe)-'])
                # Reset progress bar
                _ = self.reset_progress_bar(self.window['progbar (wfe)'])
                _ = gc.collect()

            # ------- Run a diagnostic raytrace and display the output in a Column widget ------#
            elif self.event == '-RAYTRACE-':
                # Get the wavelength and the field indexes from the respective Listbox widgets
                if self.values['select field'] == [None]:
                    logger.error('Select field')
                    continue
                elif self.values['select wl'] == [None]:
                    self.values['select wl'] = ['w1']
                n_wl = int(self.values['select wl'][0][1:]) - 1
                n_field = int(self.values['select field'][0][1:]) - 1
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.passvalue['conf'])
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                # Run the raytrace
                raytrace_log = raytrace(field, opt_chain)
                # Update the raytrace log Column
                self.window['raytrace log'].update('\n'.join(raytrace_log))
                # For later saving
                saving_groups = [wavelength]

            # ------- Run the POP ------#
            elif self.event == '-POP-':
                if self.values['select wl'] == [None]:
                    logger.error('Select wl')
                    continue
                elif self.values['select field'] == [None]:
                    logger.error('Select field')
                    continue
                # Clean up the GUI before running the POP
                del retval, figure
                retval, figure = {}, None
                retval_list.clear()
                figure_list_nwl.clear()
                figure_list_wfe.clear()
                for image_key in ['-IMAGE-', '-IMAGE (nwl)-', '-IMAGE (wfe)-']:
                    self.clear_image(self.window[image_key])
                plt.close('all')
                _ = gc.collect()
                # Get the wavelength and the field indexes from the respective Listbox widgets
                n_wl = int(self.values['select wl'][0][1:]) - 1
                n_field = int(self.values['select field'][0][1:]) - 1
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.passvalue['conf'])
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                # Run the POP
                retval = run(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
                             field, opt_chain)
                # For later saving
                saving_groups = [wavelength]
                retval_list = [retval]
                # For later plotting
                pop = 'simple'

            # ------- Run the POP (nwl) ------#
            elif self.event == '-POP (nwl)-':
                # Clean up the GUI before running the POP
                del retval, figure
                retval, figure = {}, None
                retval_list.clear()
                figure_list_nwl.clear()
                figure_list_wfe.clear()
                for image_key in ['-IMAGE-', '-IMAGE (nwl)-', '-IMAGE (wfe)-']:
                    self.clear_image(self.window[image_key])
                plt.close('all')
                _ = gc.collect()
                # Reset progress bars
                progbar_nwl = self.reset_progress_bar(self.window['progbar (nwl)'])
                _ = self.reset_progress_bar(self.window['progbar (wfe)'])
                if self.values['select field (nwl)'] == [None]:
                    logger.error('Select field')
                    continue
                elif self.values['NJOBS (nwl)'] == '':
                    logger.error('Select number of jobs')
                    continue
                n_field = int(self.values['select field (nwl)'][0][1:]) - 1
                # Get the number of parallel jobs
                n_jobs = int(self.values['NJOBS (nwl)'])
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.passvalue['conf'])
                field = fields[n_field]
                # Run the POP
                start_time = time.time()
                logger.info('Start POP in parallel...')
                print(progbar_nwl.metadata)
                for i in range(0, len(wavelengths), n_jobs):
                    wl_batch = wavelengths[i:i + n_jobs]
                    opt_batch = opt_chains[i:i + n_jobs]
                    retval_list.append(Parallel(n_jobs=n_jobs)(
                        delayed(run)(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
                                     field, opt_chain)
                        for wavelength, opt_chain in tqdm(zip(wl_batch, opt_batch))))
                    progbar_nwl.metadata += np.ceil(progbar_nwl.Size[0]/8 * len(wl_batch) / len(wavelengths))
                    print(progbar_nwl.metadata)
                    progbar_nwl = self.update_progress_bar(progbar_nwl)
                logger.info('Parallel POP completed in {:6.1f}s'.format(time.time() - start_time))
                # For later saving
                saving_groups = wavelengths
                retval_list = list(itertools.chain.from_iterable(retval_list))
                # For later plotting
                self.window['RANGE (nwl)'].update(value='-'.join(['0', str(len(retval_list))]))
                pop = 'nwl'

            # ------- Select wfe table to import ------#
            elif self.event == '-IMPORT WFE-':
                wfe_realizations_file = popup_get_file('Choose wavefront error (CSV) file', keep_on_top=True)
                if wfe_realizations_file is None:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Run the POP (wfe) ------#
            elif self.event == '-POP (wfe)-':
                # Clean up the GUI before running the POP
                del retval, figure
                retval, figure = {}, None
                retval_list.clear()
                figure_list_nwl.clear()
                figure_list_wfe.clear()
                for image_key in ['-IMAGE-', '-IMAGE (nwl)-', '-IMAGE (wfe)-']:
                    self.clear_image(self.window[image_key])
                plt.close('all')
                _ = gc.collect()
                # Reset progress bars
                _ = self.reset_progress_bar(self.window['progbar (nwl)'])
                progbar_wfe = self.reset_progress_bar(self.window['progbar (wfe)'])
                if self.values['select field (wfe)'] == [None]:
                    logger.error('Select field')
                    continue
                elif self.values['select wl (wfe)'] == [None]:
                    logger.error('Select wavelength')
                    continue
                elif self.values['NJOBS (wfe)'] == '':
                    logger.error('Select number of jobs')
                    continue
                elif self.values['NSURF (wfe)'] == '':
                    logger.error('Indicate index of Zernike surface')
                    continue
                # Get the Zernike surface index
                surf = self.values['NSURF (wfe)']
                if self.values[f'SurfaceType_({int(surf)},0)'] != 'Zernike':
                    logger.debug('The indicated surface index does not belong to a Zernike surface. Continuing...')
                    continue
                elif self.values[f'Ignore_({int(surf)},6)']:
                    logger.debug('Zernike surface is currently ignored. Continuing...')
                    continue
                elif wfe_realizations_file is None:
                    logger.debug('Import Wavefront error table first')
                    continue
                # Read the wfe table
                wfe = ascii.read(wfe_realizations_file)
                wave = float(''.join(['1.0e', self.values['ZUNIT (wfe)']]))
                # Get the number of wfe realizations
                sims = len(wfe.columns) - 3
                # Get the wavelength and the field indexes from the respective Listbox widgets
                n_wl = int(self.values['select wl (wfe)'][0][1:]) - 1
                n_field = int(self.values['select field (wfe)'][0][1:]) - 1
                # Get the number of parallel jobs
                n_jobs = int(self.values['NJOBS (wfe)'])
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.passvalue['conf'])
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                opt = []
                for k in range(sims):
                    temp = copy.deepcopy(opt_chain)
                    ck = wfe['col%i' % (k + 4)].data * wave
                    temp[int(surf)]['Z'] = np.append(np.zeros(3), ck)
                    opt.append(temp)
                # Run the POP
                start_time = time.time()
                logger.info('Start POP in parallel...')
                for i in range(0, sims, n_jobs):
                    opt_batch = opt[i:i + n_jobs]
                    retval_list.append(Parallel(n_jobs=n_jobs)(
                        delayed(run)(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
                                     field, o_chain)
                        for o_chain in tqdm(opt_batch)))
                    progbar_wfe.metadata += np.ceil(progbar_wfe.Size[0]/2 * len(opt_batch) / len(opt))
                    progbar_wfe = self.update_progress_bar(progbar_wfe)
                logger.info('Parallel POP completed in {:6.1f}s'.format(time.time() - start_time))
                # For later saving
                saving_groups = list(range(sims))
                retval_list = list(itertools.chain.from_iterable(retval_list))
                # For later plotting
                self.window['RANGE (wfe)'].update(value='-'.join(['0', str(len(retval_list))]))
                # For later plotting
                pop = 'wfe'

            # ------- Save the output of the diagnostic raytrace ------#
            elif self.event == '-SAVE RAYTRACE-':
                # Save the raytrace output
                self.to_txt(text_list=raytrace_log)

            # ------- Save the output of the POP ------#
            elif self.event == '-SAVE POP-':
                if pop != 'simple' or not retval_list:
                    logger.debug('Run POP first')
                    continue
                # Save the POP output
                self.to_hdf5(retval_list, saving_groups)

            # ------- Save the output of the POP (nwl) ------#
            elif self.event == '-SAVE POP (nwl)-':
                if pop != 'nwl' or not retval_list:
                    logger.debug('Run POP (nwl) first')
                    continue
                # Save the POP output
                self.to_hdf5(retval_list, saving_groups)

            # ------- Save the output of the POP (wfe) ------#
            elif self.event == '-SAVE POP (wfe)-':
                if pop != 'wfe' or not retval_list:
                    logger.debug('Run POP (wfe) first')
                    continue
                # Save the POP output
                self.to_hdf5(retval_list, saving_groups)

            # ------- Plot at the given optical surface ------#
            elif self.event == '-PLOT-':
                if pop != 'simple' or not retval_list:
                    logger.debug('Run POP first')
                    continue
                figure = self.draw_surface(
                    retval_list=retval_list, groups=saving_groups, figure_agg=fig_agg,
                    image_key='-IMAGE-', surface_key='S#', scale_key='Ima scale')
                # Draw the figure canvas
                fig_agg = self.draw_image(figure=figure, element=self.window['-IMAGE-'])

            elif self.event == '-PLOT (nwl)-':
                if pop != 'nwl' or not retval_list:
                    logger.debug('Run POP (nwl) first')
                    continue
                figure_list_nwl, idx_nwl = self.draw_surface(
                    retval_list=retval_list, groups=saving_groups, figure_agg=fig_agg_nwl,
                    image_key='-IMAGE (nwl)-', surface_key='S# (nwl)', scale_key='Ima scale (nwl)',
                    range_key='RANGE (nwl)')

            elif self.event == '-PLOT (wfe)-':
                if pop != 'wfe' or not retval_list:
                    logger.debug('Run POP (wfe) first')
                    continue
                figure_list_wfe, idx_wfe = self.draw_surface(
                    retval_list=retval_list, groups=saving_groups, figure_agg=fig_agg_wfe,
                    image_key='-IMAGE (wfe)-', surface_key='S# (wfe)', scale_key='Ima scale (wfe)',
                    range_key='RANGE (wfe)')

            # ------- Display the plot for a given wavelength (MC) ------#
            elif self.event in ['-DISPLAY PLOT (nwl)-', '-Slider (nwl)-']:
                # Display the plot for a given wavelength
                self.display_plot_slide(figure_list_nwl, fig_agg_nwl, '-IMAGE (nwl)-', '-Slider (nwl)-')

            # ------- Display the plot for a given wfe realization (MC) ------#
            elif self.event in ['-DISPLAY PLOT (wfe)-', '-Slider (wfe)-']:
                # Display the plot for a given wfe realization
                self.display_plot_slide(figure_list_wfe, fig_agg_wfe, '-IMAGE (wfe)-', '-Slider (wfe)-')

            # ------- Save the Plot ------#
            elif self.event == '-SAVE FIG-':
                # Save figure
                self.save_figure(figure=figure)

            # ------- Save the Plot (nwl) ------#
            elif self.event == '-SAVE FIG (nwl)-':
                if not figure_list_nwl:
                    logger.debug('Create plot first')
                    continue
                # Get the folder to save to
                folder = popup_get_folder('Choose folder to save to', keep_on_top=True, no_window=True)
                if folder is None:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue
                for wl, figure in zip(np.array(saving_groups)[idx_nwl], np.array(figure_list_nwl)):
                    filename = os.path.join(folder, f'{self.values["Fig prefix (nwl)"]}_{self.values["S# (nwl)"]}_'
                                                    f'{self.values["select field (nwl)"][0]}_wl{wl}micron.png')
                    # Save the plot to the specified .png or .jpg file
                    self.save_figure(figure, filename)

            # ------- Save the Plot (wfe) ------#
            elif self.event == '-SAVE FIG (wfe)-':
                if not figure_list_wfe:
                    logger.debug('Create plot first')
                    continue
                # Get the folder to save to
                folder = popup_get_folder('Choose folder to save to', keep_on_top=True)
                if folder is None:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue
                for n, figure in zip(np.array(saving_groups)[idx_wfe], np.array(figure_list_wfe)):
                    filename = os.path.join(folder, f'{self.values["Fig prefix (wfe)"]}_{self.values["S# (wfe)"]}_'
                                                    f'{self.values["select field (wfe)"][0]}_N{n}.png')
                    # Save the plot to the specified .png or .jpg file
                    self.save_figure(figure, filename)

            # ------- Display a popup window with the GUI values given as a flat dictionary ------#
            elif self.event == '-SUBMIT-':
                popup(f'PAOS Configuration GUI v{__version__}',
                      f'You clicked on the "{self.event}" button',
                      f'The values are {self.values}', keep_on_top=True)

            # ------- Copy the relevant data from the GUI to the local clipboard ------#
            elif self.event == '-TO CLIPBOARD-':
                self.copy_to_clipboard(dictionary=self.save_to_dict(show=False))

            # ------- Save to configuration file ------#
            elif self.event in ['Save', '-SAVE-']:
                # Update the Save switch
                save_to_ini_file = True

            # ------- Display a Open File popup window with text entry field and browse button ------#
            elif self.event == 'Open':
                # Get the new configuration file path
                filename = popup_get_file('Choose configuration (INI) file', keep_on_top=True)
                if filename is None:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue
                self.passvalue['conf'] = filename
                # Close the current window
                self.close_window()
                # Relaunch the GUI for the new configuration file
                PaosGUI(passvalue=self.passvalue, theme=self.theme)()

            # ------- Display a Save As popup window with text entry field and browse button ------#
            elif self.event == 'Save As':
                # Get the file path to save to
                filename = popup_get_file('Choose file (INI) to save to', save_as=True, keep_on_top=True)
                if filename is None:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue
                if not filename.endswith(('.INI', '.ini')):
                    logger.warning('Saving file format not provided. Defaulting to .ini')
                    filename = ''.join([filename, '.ini'])
                # Save as a new configuration file
                self.to_ini(filename=filename)

            # ------- Display url using the default browser ------#
            elif self.event == '-LINK-':
                openwb(self.window['-LINK-'].DisplayText)

            # ------- Display a popup window with the `PAOS` GUI info ------#
            elif self.event == 'About':
                popup(f'PAOS Configuration GUI v{__version__}')

        # Exit the `PAOS` GUI for good
        sys.exit()
