import configparser
import itertools
import logging
import os
import re
import sys
import time
from typing import List
from webbrowser import open as openwb
from astropy.io import ascii
import numpy as np

from PySimpleGUI import Checkbox, Text, InputText, InputCombo, Multiline, Listbox, Button, Column, Menu, Frame, Tab, \
    TabGroup, Canvas, Input, Combo, popup_get_folder
from PySimpleGUI import Submit
from PySimpleGUI import Window, WINDOW_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT
from PySimpleGUI import change_look_and_feel, main_global_pysimplegui_settings, OFFICIAL_PYSIMPLEGUI_THEME, \
    RELIEF_RIDGE, RELIEF_SUNKEN
from PySimpleGUI import popup, popup_scrolled, popup_get_file, popup_ok_cancel
from PySimpleGUI import version, get_versions
from PySimpleGUI import ProgressBar
from joblib import Parallel, delayed
from tqdm import tqdm
from matplotlib import pyplot as plt

from paos import parse_config, raytrace, run, save_datacube
from paos.gui.simpleGUI import SimpleGUI
from paos.gui.zernikeGUI import ZernikeGUI
from paos.log import setLogLevel
from paos.paos_config import __pkg_name__, __author__, __url__, __version__
from paos.paos_config import base_dir, logger
from paos.paos_plotpop import simple_plot, plot_psf_xsec


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
    >>> from paos.gui.paosGUI import PaosGUI
    >>> passvalue = {'conf': '/path/to/ini/file/', 'debug': False}
    >>> PaosGUI(passvalue=passvalue, theme='Dark')()

    Note
    ----
    The first implementation of PaosGUI is in `PAOS` v0.0.4

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
        self.wl_data = {'Wavelength (micron)': ''}

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

        self.selected_wl = ['w1']
        self.selected_field = ['f1']

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

    def get_widget(self, value, key, item, size=(24, 2)):
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
        row = None

        if key.partition('_')[0] in self.lens_data.keys():
            cell = re.findall('[0-9]+', key.partition('_')[-1])
            row, col = tuple(map(int, cell))

        default = item if item != 'NaN' else None
        disabled = False if item != 'NaN' else True

        if value in ['Save', 'Ignore', 'Stop']:
            return Checkbox(text=value, default=default, key=key, size=(21, 2), disabled=disabled)
        elif value in ['Comment', 'Radius', '']:
            return InputText(default_text=default, key=key, size=size, disabled=disabled)
        elif key.startswith('aperture'):
            return self.aperture_tab(row=row, col=8, key=key, disabled=disabled)
        else:
            return InputCombo(default_value=default, values=value, key=key, size=(23, 2), disabled=disabled,
                              enable_events=True)

    def fill_aperture_tab(self, row, col):
        """
        Given the row and column corresponding to the cell in the GUI lens data editor, returns a list of widgets with
        the aperture parameters names and values

        Parameters
        ----------
        row: int
            row corresponding to the optical surface in the GUI lens data editor
        col: int
            column corresponding to the aperture header in the GUI lens data editor

        Returns
        -------
        out: List[List[Text], List[Checkbox or Input or Column or Combo]]
            list of widgets with the aperture parameters names and values
        """
        config_key = 'lens_{:02d}'.format(row)
        config_items = None
        if config_key in self.config.keys():
            config_items = self.config[config_key].get('aperture', None)
            config_items = config_items if config_items != '' else None
        if config_items is not None:
            config_items = config_items.split(',')

        surface_tab = []
        for k, (key, item) in enumerate(self.lens_data['aperture']['values'].items()):
            key_item = key.replace(' ', '_') + f'_({row},{col})'
            config_item = '' if config_items is None else config_items[k]

            surface_tab.append([Text(key, size=(20, 1))])
            surface_tab.append([self.get_widget(value=item, key=key_item, item=config_item, size=(20, 1))])

        return surface_tab

    def aperture_tab(self, row, col, key, disabled):
        """
        Given the row and column corresponding to the cell in the GUI lens data editor, returns the Column widget with
        the aperture parameters

        Parameters
        ----------
        row: int
            row corresponding to the optical surface in the GUI lens data editor
        col: int
            column corresponding to the aperture header in the GUI lens data editor
        key: str
            key to which the returned Column widget will be associated
        disabled: bool
            boolean to disable or enable events for the Button widget

        Returns
        -------
        out: Column
            the Column widget for the aperture

        """
        button_symbol = self.symbol_disabled if disabled else self.symbol_up
        text_color = 'gray' if disabled else 'yellow'
        surface_tab_layout = Column(layout=[
            [Button(button_symbol, enable_events=True, disabled=disabled,
                    key=f'-OPEN APERTURE TAB-({row},{col})', font=self.font_small, size=(2, 1)),
             Text('Aperture', size=(20, 1), text_color=text_color, key=f'LD_Tab_Title_({row},{col})')],
            [self.collapse([[Column(layout=self.fill_aperture_tab(row, col))]],
                           key=f'LD_Tab_({row},{col})')]], key=key)

        return surface_tab_layout

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
        Updates the displayed headers according to the rules set in :class:`~PaosGUI.par_heading_rules`

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

    def add_row(self, column_key):
        """
        Given the Column key, it updates the current Column by adding a row.
        For example, can add a row to the wavelength Column.

        Parameters
        ----------
        column_key: str
            key for the Column widget to which we want to add a row

        Returns
        -------
        out: int
            the current Column's updated number of rows
        """
        prefix = column_key[0]
        nrows, input_list = None, []

        if column_key == 'wavelengths':
            nrows = self.nrows_wl
            input_list = [item for key, item in self.wl_data.items()]
        elif column_key == 'fields':
            nrows = self.nrows_field
            input_list = [item for key, item in self.field_data.items()]
        elif column_key == 'lenses':
            nrows = self.nrows_ld
            input_list = [item['values'] for key, item in self.lens_data.items()]
        else:
            logger.error('Key error')

        nrows += 1
        self.window.extend_layout(self.window[column_key], [self.chain_widgets(nrows, input_list, prefix)])
        self.window[column_key].update()

        if column_key == 'lenses':
            self.config.add_section('lens_{:02d}'.format(nrows))
            for c, head in enumerate(self.lens_data.keys()):
                self.window[f'{head}_({nrows},{c})'].bind("<Button-1>", "_LeftClick")

        return nrows

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
                if head == 'aperture':
                    dictionary[key][head] = ','.join([self.values[f'{name_key.replace(" ", "_")}_({k},{c})']
                                                      for name_key in self.lens_data['aperture']['values'].keys()])
                    if dictionary[key][head] == len(dictionary[key][head]) * ',':
                        dictionary[key][head] = ''
                else:
                    dictionary[key][head] = self.values[f'{head}_({k},{c})']
                    if dictionary[key][head] == 'Zernike':
                        dictionary[key]['zindex'] = self.config[key]['zindex']
                        dictionary[key]['z'] = self.config[key]['z']

        if show:
            popup_scrolled(f'lens_data = {dictionary}', title='Copy your data from here',
                           keep_on_top=True)
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
        # Define general layout
        general_layout = [
            [Frame('General Setup', layout=[[Text('', size=(15, 1))],
                                            [Text('Project Name:', size=(15, 1)),
                                             InputText(self.config['general'].get('project', ''),
                                                       tooltip='Insert project name',
                                                       key='project',
                                                       size=(80, 1))],
                                            [Text('Version:', size=(15, 1)),
                                             InputText(self.config['general'].get('version', ''),
                                                       tooltip='Insert project version tag',
                                                       key='version',
                                                       size=(24, 1))],
                                            [Text('Grid Size:', size=(15, 1)),
                                             InputCombo(values=['64', '128', '512', '1024'],
                                                        default_value=self.config['general'].getint('grid_size', 512),
                                                        key='grid_size', size=(24, 1))],
                                            [Text('Zoom:', size=(15, 1)),
                                             InputCombo(values=['1', '2', '4', '8', '16'],
                                                        default_value=self.config['general'].getint('zoom', 4),
                                                        key='zoom', size=(24, 1))],
                                            [Text('Lens unit:', size=(15, 1)),
                                             InputText(self.config['general'].get('lens_unit', ''),
                                                       key='lens_unit', size=(24, 1), disabled=True)],
                                            [Text('T ambient:', size=(15, 1)),
                                             InputText(self.config['general'].get('Tambient', ''),
                                                       tooltip='Insert ambient temperature',
                                                       key='tambient',
                                                       size=(24, 1))],
                                            [Text('T unit:', size=(15, 1)),
                                             InputText('(°C)', key='T_unit', size=(24, 1), disabled=True)],
                                            [Text('P ambient:', size=(15, 1)),
                                             InputText(self.config['general'].get('Pambient', ''),
                                                       tooltip='Insert ambient pressure',
                                                       key='pambient',
                                                       size=(24, 1))],
                                            [Text('P unit:', size=(15, 1)),
                                             InputText('(atm)', key='P_unit', size=(24, 1), disabled=True)],
                                            [Text('', size=(15, 1))]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-GENERAL FRAME-', expand_x=True, expand_y=True)],
            [Frame('Wavelength Setup', layout=[
                [Text('', size=(15, 1))],
                [Column(layout=list(
                    itertools.chain(
                        [self.add_heading(self.wl_data.keys())],
                        [self.chain_widgets(r, [item for key, item in self.wl_data.items()], prefix='w')
                         for r in range(1, self.nrows_wl + 1)])
                ), key='wavelengths', scrollable=True, expand_x=True, expand_y=True)
                ]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-WL FRAME-', expand_x=True, expand_y=True)],
            [Frame('General Actions', layout=[
                [Button(tooltip='Click to add wavelength', button_text='Add Wavelength',
                        enable_events=True, key="-ADD WAVELENGTH-")],
                [Button('Paste Wavelengths', tooltip='Click to paste wavelengths', key='PASTE WL')]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-GENERAL ACTIONS FRAME-')]
        ]
        # Define fields layout
        fields_layout = [
            [Column(layout=list(itertools.chain([self.add_heading(self.field_data.keys())],
                                                [self.chain_widgets(r, [item for key, item in self.field_data.items()],
                                                                    prefix='f')
                                                 for r in range(1, self.nrows_field + 1)])),
                    scrollable=True, expand_x=True, expand_y=True,
                    key='fields')],
            [Text(' ')],
            [Frame('Fields Actions', layout=[
                [Button(tooltip='Click to add field row', button_text='Add Field', enable_events=True,
                        key="-ADD FIELD-")]
            ],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-FIELDS ACTIONS FRAME-')]
        ]
        # Define lens data layout
        lens_data_layout = [
            [Column(layout=list(
                itertools.chain([self.add_heading(self.lens_data.keys())],
                                [[Text('')]],
                                [self.chain_widgets(r,
                                                    [item['values'] for key, item in self.lens_data.items()],
                                                    prefix='l')
                                 for r in range(1, self.nrows_ld + 1)])
            ), scrollable=True, expand_x=False, expand_y=True, key='lenses')
            ],
            [Text(' ')],
            [Frame('Lens Data Actions', layout=[
                [Button(tooltip='Click to add surface row', button_text='Add Surface', enable_events=True,
                        key="-ADD SURFACE-")]
            ],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-LENS DATA ACTIONS FRAME-')]
        ]
        # Define launcher layout
        launcher_layout = [list(itertools.chain(
            [Frame('Select inputs', layout=[
                list(itertools.chain(
                    [Text('Select wavelength', size=(12, 2)),
                     Listbox(default_values=self.selected_wl,
                             values=[key for key, item in self.config.items('wavelengths')],
                             size=(12, 4), background_color='grey20', key='select wl',
                             enable_events=True)],
                    [Text('', size=(5, 2))],
                    [Text('Select field', size=(12, 2)),
                     Listbox(default_values=self.selected_field,
                             values=[key for key, item in self.config.items('fields')],
                             size=(12, 4), background_color='grey20', key='select field',
                             enable_events=True)]))],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-PAOS SELECT INPUTS FRAME-')
             ],
            [Text('', size=(100, 2))],
            [Frame('Save', layout=[
                [Button(tooltip='Save raytrace output',
                        button_text='Save raytrace',
                        enable_events=True,
                        key="-SAVE RAYTRACE-")],
                [Button(tooltip='Save the POP output', button_text='Save POP',
                        enable_events=True,
                        key="-SAVE POP-")],
                [Button(tooltip='Save the plot', button_text='Save Plot',
                        enable_events=True,
                        key="-SAVE FIG-")]
            ],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-PAOS SAVE FRAME-')
             ])),
            [Frame('Raytrace', layout=[
                [Text('Run a diagnostic raytrace')],
                [Button(tooltip='Launch raytrace', button_text='Raytrace', enable_events=True,
                        key="-RAYTRACE-")],
                [Column(layout=[
                    [Multiline(
                        key='raytrace log', font=self.font_small, autoscroll=True, size=(90, 20),
                        pad=(0, (15, 0)), background_color='grey20', disabled=False)]],
                    key='raytrace log col',
                )]
            ],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-PAOS RAYTRACE FRAME-'),
             Text('', size=(5, 2)),
             Frame('POP', layout=[
                 list(itertools.chain([Text('Run the POP: '),
                                       Button(tooltip='Launch POP', button_text='POP',
                                              enable_events=True, key="-POP-")],
                                      [Text('', size=(6, 2))],
                                      [Text('Plot surface: '),
                                       InputCombo(tooltip='Surface number',
                                                  values=[f'S{k}' for k in range(1, self.nrows_ld + 1)],
                                                  default_value=f'S{self.nrows_ld}', key="S#"),
                                       InputCombo(tooltip='Color scale', values=['linear scale', 'log scale'],
                                                  default_value='log scale', key="Ima scale"),
                                       Button(tooltip='Plot', button_text='Plot', enable_events=True,
                                              key="-PLOT-")
                                       ]
                                      )),
                 [Canvas(key='-CANVAS-', size=(90, 20))]
             ],
                   font=self.font_titles, relief=RELIEF_SUNKEN, expand_x=True, expand_y=True,
                   key='-PAOS POP FRAME-')
             ]
        ]
        # Define parallel launcher layout
        monte_carlo_layout = [
            [Frame('Select inputs', layout=[
                list(itertools.chain(
                    [Text('Select wavelength', size=(12, 2)),
                     Listbox(default_values=self.selected_wl,
                             values=[key for key, item in self.config.items('wavelengths')],
                             size=(12, 4), background_color='grey20', key='select wl (MC)',
                             enable_events=True)],
                    [Text('', size=(5, 2))],
                    [Text('Select field', size=(12, 2)),
                     Listbox(default_values=self.selected_field,
                             values=[key for key, item in self.config.items('fields')],
                             size=(12, 4), background_color='grey20', key='select field (MC)',
                             enable_events=True)]
                ))],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-PAOS SELECT INPUTS FRAME-')
             ],
            [Frame('MC Wavelengths', layout=[
                list(itertools.chain(
                    [Frame('Run and Save', layout=[
                        [Text('', size=(6, 2))],
                        [Text('Number of parallel jobs: '),
                         InputText(tooltip='Number of jobs', default_text=2, key="NJOBS (nwl)")],
                        (Text('Run the multi-wl POP: '),
                         Button(tooltip='Launch POP', button_text='POP', enable_events=True,
                                key="-POP (nwl)-"),
                         ProgressBar(max_value=40, orientation='horizontal', size=(40, 8), border_width=2,
                                     key='progbar (nwl)', metadata=0, bar_color=('Yellow', 'Gray'))),
                        [Text('Save the POP output: '),
                         Button(tooltip='Save the POP output', button_text='Save POP', enable_events=True,
                                key="-SAVE POP (nwl)-")],
                        [Text('', size=(6, 2))],
                        [Text('Plot surface: '),
                         InputCombo(tooltip='Surface number',
                                    values=[f'S{k}' for k in range(1, self.nrows_ld + 1)],
                                    default_value=f'S{self.nrows_ld}', key="S# (nwl)"),
                         InputCombo(tooltip='Color scale', values=['linear scale', 'log scale'],
                                    default_value='log scale', key="Ima scale (nwl)"),
                         Button(tooltip='Plot', button_text='Plot', enable_events=True,
                                key="-PLOT (nwl)-")],
                        [Text('Save the Plots')],
                        [Text('Figure prefix: '),
                         InputText(tooltip='Figure prefix', default_text='Plot', key="Fig prefix"),
                         Button(tooltip='Save the plots', button_text='Save Plot', enable_events=True,
                                key="-SAVE FIG (nwl)-")],
                    ],
                           font=self.font_subtitles, relief=RELIEF_SUNKEN, expand_x=True,
                           key='-RUN AND SAVE FRAME (nwl)-'
                           )],
                    [Frame('Display', layout=[
                        [Button(tooltip='Display plot', button_text='Display plot', enable_events=True,
                                key="-DISPLAY PLOT (nwl)-")],
                        [Canvas(key='-CANVAS (nwl)-')]
                    ],
                           font=self.font_subtitles, relief=RELIEF_SUNKEN, expand_x=True, expand_y=True,
                           key='-CANVAS FRAME (nwl)-'
                           )],
                ))],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-MC WL-', expand_x=True, expand_y=True)],
            [Frame('MC Wavefront error', layout=[
                [Button(tooltip='Import Wavefront error table', button_text='Import wfe',
                        enable_events=True, key="-IMPORT WFE-")]],
                   font=self.font_titles, relief=RELIEF_SUNKEN, key='-MC WFE-', expand_x=True, expand_y=True)]
        ]

        # Define info layout
        info_layout = [
            [Frame('GUI Info', layout=[[Text(f'Credits: {__author__}',
                                             key='-CREDITS-')],
                                       [Text(f'{__pkg_name__.upper()} version: {__version__}',
                                             key='-PAOS VERSION-')],
                                       [Text('')],
                                       [Text('Github Repo: ')],
                                       [Text(f'{__url__}',
                                             font=self.font_underlined,
                                             text_color='blue', enable_events=True, key='-LINK-')],
                                       [Text('')],
                                       [Text(f'PySimpleGui version: {version}',
                                             key='-GUI VERSION-')]], font=self.font_titles,
                   relief=RELIEF_SUNKEN, key='-INFO FRAME-')]
        ]

        # ------ Define GUI layout ------ #
        layout = [
            [Menu(self.menu_def, tearoff=True, key="-MENU-")],
            [Text('Configuration Tabs', size=(38, 1), justification='center',
                  relief=RELIEF_RIDGE, key="-TEXT HEADING-", enable_events=True)],
            [TabGroup([
                [
                    Tab('General', general_layout, key="-GENERAL TAB-"),
                    Tab('Fields', fields_layout, key="-FIELDS TAB-"),
                    Tab('Lens Data', lens_data_layout, key="-LENS DATA TAB-"),
                    Tab('Launcher', launcher_layout, key="-LAUNCHER TAB-"),
                    Tab('Monte Carlo', monte_carlo_layout, key="-PARALLEL LAUNCHER TAB-"),
                    Tab('Info', info_layout, key="-INFO TAB-")
                ]
            ],
                key='-CONF TAB GROUP-')],
            [
                Submit(tooltip='Click to submit (debug)', key='-SUBMIT-'),
                Button(tooltip='Click to show dict', button_text='Show Dict',
                       key="-SHOW DICT-"),
                Button(tooltip='Click to copy dict to clipboard',
                       button_text='Copy to clipboard',
                       key="-TO CLIPBOARD-"),
                Button(tooltip='Save to ini file',
                       button_text='Save',
                       key="-SAVE-"),
                Button('Exit', key='-EXIT-')
            ]
        ]

        # ------ Window creation ------ #
        self.window = Window('PAOS Configuration GUI', layout, default_element_size=(12, 1),
                             element_padding=(1, 1), return_keyboard_events=True, finalize=True,
                             right_click_menu=self.right_click_menu_def, resizable=True,
                             font=self.font, enable_close_attempted_event=True,
                             element_justification='center', keep_on_top=True)

        self.window['-CONF TAB GROUP-'].expand(True, True, True)

        # ------ Cursors definition ------ #
        self.window['-ADD SURFACE-'].set_cursor(cursor='hand1')
        self.window['-SHOW DICT-'].set_cursor(cursor='target')
        self.window['-LINK-'].set_cursor(cursor='trek')
        self.window['-CREDITS-'].set_cursor(cursor='boat')
        self.window['-PAOS VERSION-'].set_cursor(cursor='coffee_mug')
        self.window['-GUI VERSION-'].set_cursor(cursor='clock')

        # ------- Bind method for Par headings ------#
        for r, (c, head) in itertools.product(range(1, self.nrows_ld + 1), enumerate(self.lens_data.keys())):
            self.window[f'{head}_({r},{c})'].bind("<Button-1>", "_LeftClick")

        return

    def __call__(self):
        """
        Returns a rendering of the GUI window and handles the event loop.
        """

        # ------ Generate the main GUI window ------ #
        self.make_window()

        # ------ Instantiate global variables ------ #
        raytrace_log, retval, retval_list = '', None, []
        wavelength_list = []
        fig, figure_list = None, []
        fig_agg, fig_agg_nwl = None, None
        save_to_ini_file = False
        aperture_tab_visible = False

        while True:  # Event Loop

            # ------- Read the current window ------#
            self.event, self.values = self.window.read()
            logger.debug(f'============ Event = {self.event} ==============')

            # ------- Save to temporary configuration file ------#
            self.to_ini(temporary=True)

            # ------- Find the window element with focus ------#
            elem = self.window.find_element_with_focus()
            elem_key = elem.Key if (elem is not None and isinstance(elem.Key, (str, tuple))) else (0, 0)

            # ------- Move with arrow keys within the editor tab and update the headings accordingly ------#
            if isinstance(elem_key, str) and elem_key.startswith(
                    tuple([head for head in self.lens_data.keys()])):
                # Move with arrow keys
                row = self.move_with_arrow_keys(self.window, self.event, self.values, elem_key, self.nrows_ld,
                                                len(self.lens_data.keys()))
                # Update headings
                self.update_headings(row)

            # ------- Save (optional) and properly close the current window ------#
            if self.event in (WINDOW_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, 'Exit', '-EXIT-'):
                # Save back to the configuration file
                if save_to_ini_file:
                    self.to_ini()
                # Close the current window
                self.close_window()
                break

            # ------- Update the headings according to mouse left click ------#
            elif isinstance(elem_key, str) and self.event == elem_key + '_LeftClick':
                cell = re.findall('[0-9]+', elem_key.partition('_')[-1])
                row, col = tuple(map(int, cell))
                self.update_headings(row)

            # ------- Display a popup window with the output dictionary ------#
            elif self.event == '-SHOW DICT-':
                self.save_to_dict(show=True)

            # ------- Paste from the clipboard to the desired wavelength input cells ------#
            elif self.event == 'PASTE WL':
                # Check if focus is on a wavelength input cell
                if not elem_key.startswith('w'):
                    logger.debug('Wavelength cell not selected. Skipping..')
                    continue
                # Get text from the clipboard
                text = self.get_clipboard_text()
                row0 = row = int(elem_key[1:])
                # Loop through text to insert the wavelengths one at a time
                for text_item in text:
                    self.window[f'w{row}'].update(text_item)
                    if self.nrows_wl <= row < row0 + len(text) - 1:
                        # Add the new wavelength and update wavelength count
                        self.nrows_wl = self.add_row('wavelengths')
                        self.wl_keys.append(f'w{self.nrows_wl}')
                        # Update 'select wl' Listbox widget in the launcher Tab
                        self.window["select wl"].update(self.wl_keys)
                    row += 1
                # Update 'select wl' Listbox widget in the launcher Tab
                self.window["select wl"].update(self.wl_keys)
                # Update 'select wl' Listbox widget in the Monte Carlo Tab
                self.window["select wl (MC)"].update(self.wl_keys)

            # ------- Add a new wavelength input cell below those already present ------#
            elif self.event == '-ADD WAVELENGTH-':
                # Add the new wavelength and update wavelength count
                self.nrows_wl = self.add_row('wavelengths')
                self.wl_keys.append(f'w{self.nrows_wl}')
                # Update 'select wl' Listbox widget in the launcher Tab
                self.window["select wl"].update(self.wl_keys)
                # Update 'select wl' Listbox widget in the Monte Carlo Tab
                self.window["select wl (MC)"].update(self.wl_keys)

            # ------- Add a new fields input row below those already present ------#
            elif self.event == '-ADD FIELD-':
                # Add the new field and update wavelength count
                self.nrows_field = self.add_row('fields')
                self.field_keys.append(f'f{self.nrows_field}')
                # Update 'select field' Listbox widget in the launcher Tab
                self.window["select field"].update(self.field_keys)
                # Update 'select field' Listbox widget in the Monte Carlo Tab
                self.window["select field (MC)"].update(self.field_keys)

            # ------- Add a new optical surface in the lens data editor as a new row ------#
            elif self.event == '-ADD SURFACE-':
                # Add the new optical surface and update surface count
                self.nrows_ld = self.add_row('lenses')

            # ------- Make the aperture tab visible/invisible by clicking on the triangle symbol ------#
            elif isinstance(self.event, str) and self.event.startswith('-OPEN APERTURE TAB-'):
                # Find current location in the lens data editor
                row, col = re.findall('[0-9]+', self.event)
                aperture_tab_key = f'LD_Tab_({row},{col})'
                # Make the aperture tab visible/invisible
                aperture_tab_visible = not aperture_tab_visible
                self.window[aperture_tab_key].update(visible=aperture_tab_visible)
                # Update the triangle symbol
                self.window[self.event].update(self.symbol_down if aperture_tab_visible else self.symbol_up)

            # ------- Assign/edit the surface type in the lens data editor ------#
            elif isinstance(self.event, str) and self.event.startswith('SurfaceType'):
                # Get the current row
                row, col = re.findall('[0-9]+', self.event)
                surface_type_key = f'SurfaceType_({row},0)'
                # Loop through all widgets in the current row
                for c, (key, value) in enumerate(self.lens_data.items()):
                    name_key = f'{key}_({row},{c})'
                    # Apply the pre-defined rules for the lens data editor to enable/disable a widget
                    item = self.lens_data_rules(surface_type=self.values[surface_type_key], header=name_key)
                    disabled = True if item == 'NaN' else False
                    if key == 'aperture':
                        item_column_key = f'-OPEN APERTURE TAB-({row},{c})'
                        # Update triangle symbol
                        self.window[item_column_key].update(self.symbol_disabled if disabled else self.symbol_up)
                        title_column_key = f'LD_Tab_Title_({row},8)'
                        text_color = 'gray' if disabled else 'yellow'
                        # Update aperture text color
                        self.window[title_column_key].update(text_color=text_color)
                    else:
                        item_column_key = f'{key}_({row},{c})'
                    # Enable/disable the row widgets
                    self.window[item_column_key].update(disabled=disabled)

                # Only if the selected surface type is Zernike...
                if self.values[surface_type_key] == 'Zernike':
                    # Display popup to select action
                    action = popup_ok_cancel('Insert/Edit Zernike coefficients', keep_on_top=True)
                    if action == 'OK':
                        key = 'lens_{:02d}'.format(int(row))
                        # Launch the Zernike GUI editor
                        zernike = ZernikeGUI(config=self.config, values=self.values, row=row, key=key)()
                        if key in self.config.keys():
                            # Update the zernike values in the config object
                            self.config[key].update(zernike)
                        else:
                            # Create ex-novo the zernike values in the config object
                            for subkey, subitem in zernike.items():
                                self.config.set(key, subkey, subitem)
                        # Update the zernike ordering (relevant only if previously not indicated)
                        col = list(self.lens_data.keys()).index("Par2")
                        self.window[f'Par2_({row},{col})'].update(zernike['ordering'])

            # ------- Select a different wavelength or field using the 'select field' or the 'select field' ------#
            # ------- Listbox widget in the launcher tab ------#
            elif self.event in ['select wl', 'select field']:
                if self.values['select wl'] != self.selected_wl \
                        or self.values['select field'] != self.selected_field:
                    if retval_list is not None:
                        # Reset POP simulation output
                        del retval_list
                        retval_list = []
                    if fig_agg is not None:
                        # Reset figure canvas
                        self.delete_figure(fig_agg)
                        fig_agg = None
                    if self.event == 'select field' and raytrace_log is not None:
                        raytrace_log = ''
                        # Update the raytrace log Column
                        self.window['raytrace log'].update(raytrace_log)
                    self.selected_wl = self.values['select wl']
                    self.selected_field = self.values['select field']

            # ------- Select a different wavelength or field using the 'select field' or the 'select field' ------#
            # ------- Listbox widget in the Monte Carlo tab ------#
            elif self.event in ['select wl (MC)', 'select field (MC)']:
                if self.values['select wl (MC)'] != self.selected_wl \
                        or self.values['select field (MC)'] != self.selected_field:
                    if self.event == 'select field (MC)' \
                            or int(self.values['select wl (MC)'][0][1:]) > len(retval_list):
                        if retval_list:
                            # Reset POP simulation output
                            del retval_list
                            retval_list = []
                        if figure_list:
                            # Reset figure
                            del figure_list
                            figure_list = []
                            plt.close('all')
                    if fig_agg_nwl is not None:
                        # Reset figure canvas
                        self.delete_figure(fig_agg_nwl)
                        fig_agg_nwl = None
                    self.selected_wl = self.values['select wl (MC)']
                    self.selected_field = self.values['select field (MC)']

            # ------- Run a diagnostic raytrace and display the output in a Column widget ------#
            elif self.event == '-RAYTRACE-':
                # Get the wavelength and the field indexes from the respective Listbox widgets
                n_wl = int(self.selected_wl[0][1:]) - 1
                n_field = int(self.selected_field[0][1:]) - 1
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.temporary_config)
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                # Run the raytrace
                raytrace_log = raytrace(field, opt_chain)
                # Update the raytrace log Column
                self.window['raytrace log'].update('\n'.join(raytrace_log))
                # For later saving
                wavelength_list = [wavelength]

            # ------- Run the POP ------#
            elif self.event == '-POP-':
                # Get the wavelength and the field indexes from the respective Listbox widgets
                n_wl = int(self.selected_wl[0][1:]) - 1
                n_field = int(self.selected_field[0][1:]) - 1
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.temporary_config)
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                # Run the POP
                retval = run(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
                             field, opt_chain)
                # For later saving
                wavelength_list = [wavelength]
                retval_list = [retval]

            elif self.event == '-POP (nwl)-':
                # Reset previous POP output
                if retval_list:
                    retval_list = []
                # Reset progress bar
                progbar_nwl = self.window['progbar (nwl)']
                progbar_nwl.update('')
                progbar_nwl.metadata = 0
                # Get the field index from the Listbox widget
                n_field = int(self.selected_field[0][1:]) - 1
                # Get the number of parallel jobs
                n_jobs = int(self.values['NJOBS (nwl)'])
                # Parse the temporary configuration file
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.temporary_config)
                field = fields[n_field]
                # Run the POP
                start_time = time.time()
                logger.info('Start POP in parallel...')

                for i in range(0, len(wavelengths), n_jobs):
                    wl_batch = wavelengths[i:i + n_jobs]
                    optc_batch = opt_chains[i:i + n_jobs]
                    retval_list.append(Parallel(n_jobs=n_jobs)(
                        delayed(run)(pup_diameter,
                                     1.0e-6 * wavelength,
                                     parameters['grid_size'],
                                     parameters['zoom'],
                                     field,
                                     opt_chain)
                        for wavelength, opt_chain in tqdm(zip(wl_batch, optc_batch))))
                    progress = np.ceil(progbar_nwl.Size[0] * len(wl_batch) / len(wavelengths))
                    progbar_nwl.metadata += progress
                    progbar_nwl.update_bar(progbar_nwl.metadata)

                end_time = time.time()
                logger.info('Parallel POP completed in {:6.1f}s'.format(end_time - start_time))
                # For later saving
                wavelength_list = wavelengths
                retval_list = list(itertools.chain.from_iterable(retval_list))

            # ------- Save the output of the diagnostic raytrace ------#
            elif self.event == '-SAVE RAYTRACE-':
                if raytrace_log == '':
                    logger.debug('Perform raytrace first')
                    continue
                # Get the file path to save to
                filename = popup_get_file('Choose file (TXT) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    # Save the raytrace output to the specified .txt file
                    with open(filename, "wt") as f:
                        f.write('\n'.join(raytrace_log))
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Save the output of the POP ------#
            elif self.event in ['-SAVE POP-', '-SAVE POP (nwl)-']:
                if not retval_list:
                    logger.debug('Run POP first')
                    continue
                # Get the file path to save to
                filename = popup_get_file('Choose file (HDF5) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    # Save the POP output to the specified .hdf5 file
                    group_tags = list(map(str, wavelength_list))
                    save_datacube(retval_list, filename, group_tags, keys_to_keep=['amplitude', 'dx', 'dy', 'wl'],
                                  overwrite=True)
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Plot at the given optical surface ------#
            elif self.event == '-PLOT-':
                if not retval_list:
                    logger.debug('Run POP first')
                    continue
                if fig_agg is not None:
                    # Reset figure canvas
                    self.delete_figure(fig_agg)
                # Get surface to plot
                key = int(self.values['S#'][1:])
                # Get image scale
                ima_scale = self.values['Ima scale'].partition(' ')[0]
                # Check that surface is stored in POP output
                if key not in retval.keys():
                    logger.error('Surface not present in POP output: it was either ignored or simply not saved')
                    continue
                # Plot
                fig = self.plot_surface(key, retval, ima_scale)
                # Draw the figure canvas
                fig_agg = self.draw_figure(figure=fig, canvas=self.window['-CANVAS-'].tk_canvas)
                fig_agg.draw()

            # ------- Plot at the given optical surface (MC) ------#
            elif self.event == '-PLOT (nwl)-':
                if not retval_list:
                    logger.debug('Run POP first')
                    continue
                # Get surface to plot
                key = int(self.values['S# (nwl)'][1:])
                # Get image scale
                ima_scale = self.values['Ima scale (nwl)'].partition(' ')[0]
                for wl, ret in zip(wavelength_list, retval_list):
                    # Check that surface is stored in POP output
                    if key not in ret.keys():
                        logger.error('Surface not present in POP output: it was either ignored or simply not saved')
                        continue
                    # Plot
                    logger.debug(f'Plotting POP @ {wl}micron')
                    figure_list.append(self.plot_surface(key, ret, ima_scale))

            # ------- Display the plot for a given wavelength (MC) ------#
            elif self.event == '-DISPLAY PLOT (nwl)-':
                if not figure_list:
                    logger.debug('Plot POP first')
                    continue
                if fig_agg_nwl is not None:
                    # Reset figure canvas
                    self.delete_figure(fig_agg_nwl)
                # Get the wavelength index
                n_wl = int(self.selected_wl[0][1:]) - 1
                # Draw the figure canvas
                fig_agg_nwl = self.draw_figure(figure=figure_list[n_wl], canvas=self.window['-CANVAS (nwl)-'].tk_canvas)
                fig_agg_nwl.draw()

            # ------- Save the Plot ------#
            elif self.event == '-SAVE FIG-':
                if retval is None or fig_agg is None:
                    logger.debug('Create plot first')
                    continue
                # Get the file path to save to
                filename = popup_get_file('Choose file (PNG, JPG) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    # Save the plot to the specified .png or .jpg file
                    fig.savefig(filename, bbox_inches='tight', dpi=150)
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Save the Plot (MC) ------#
            elif self.event == '-SAVE FIG (nwl)-':
                if not figure_list:
                    logger.debug('Create plot first')
                    continue
                # Get the folder to save to
                folder = popup_get_folder('Choose folder to save to', keep_on_top=True)
                if folder is not None:
                    for wl, figure in zip(wavelength_list, figure_list):
                        # Save the plot to the specified .png or .jpg file
                        figure.savefig(
                            os.path.join(folder, f'{self.values["Fig prefix"]}_{self.values["S# (nwl)"]}_'
                                                 f'{self.values["select field (MC)"][0]}_'
                                                 f'wl{wl}micron.png'),
                            format='png', bbox_inches='tight', dpi=150)
                        logger.debug(f'Saved Plot @ {wl}micron')
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Import wfe table ------#
            elif self.event == '-IMPORT WFE-':
                wfe_realizations_file = popup_get_file('Choose wavefront error (CSV) file', keep_on_top=True)
                if wfe_realizations_file is not None:
                    wfe = ascii.read(wfe_realizations_file)
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

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
                new_config_file = popup_get_file('Choose configuration (INI) file', keep_on_top=True)
                if new_config_file is not None:
                    self.passvalue['conf'] = new_config_file
                    # Close the current window
                    self.close_window()
                    # Relaunch the GUI for the new configuration file
                    PaosGUI(passvalue=self.passvalue, theme=self.theme)()
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Display a Save As popup window with text entry field and browse button ------#
            elif self.event == 'Save As':
                # Get the file path to save to
                filename = popup_get_file('Choose file (INI) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    # Save as a new configuration file
                    self.to_ini(filename=filename)
                else:
                    logger.debug('Pressed Cancel. Continuing...')
                    continue

            # ------- Display a window to set the global PySimpleGUI settings (e.g. the color theme) ------#
            elif self.event == 'Global Settings':
                main_global_pysimplegui_settings()

            # ------- Display a popup with the PySimpleGUI version ------#
            elif self.event == 'Version':
                popup_scrolled(get_versions(), keep_on_top=True)

            # ------- Display url using the default browser ------#
            elif self.event == '-LINK-':
                openwb(self.window['-LINK-'].DisplayText)

            # ------- Display a popup window with the `PAOS` GUI info ------#
            elif self.event == 'About':
                popup(f'PAOS Configuration GUI v{__version__}')

        # Exit the `PAOS` GUI for good
        sys.exit()
