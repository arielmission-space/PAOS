import itertools
import os
import sys
import re
import gc
import logging
import configparser
from matplotlib import pyplot as plt

from paos import parse_config, raytrace, run, Zernike, save_datacube
from paos.paos_config import base_dir, logger
from paos.paos_plotpop import simple_plot, plot_psf_xsec
from paos.log import setLogLevel

from tkinter import Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from webbrowser import open as openwb

from PySimpleGUI import change_look_and_feel, main_global_pysimplegui_settings, OFFICIAL_PYSIMPLEGUI_THEME, \
    RELIEF_RIDGE, RELIEF_SUNKEN, pin
from PySimpleGUI import version, get_versions
from PySimpleGUI import Checkbox, Text, InputText, InputCombo, Multiline, Listbox, Button, Column, Menu, Frame, Tab, \
    TabGroup, Canvas
from PySimpleGUI import Window, WINDOW_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT
from PySimpleGUI import popup, popup_scrolled, popup_quick_message, popup_get_file, popup_ok_cancel
from PySimpleGUI import Submit, clipboard_set


class PaosConfigurationGui:
    """
    Generates the Graphical User Interface (GUI) for the `PAOS` code using the publicly available library PySimpleGUI.

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
    >>> from paos.gui.paos_guilib import PaosConfigurationGui
    >>> passvalue = {'conf': '/path/to/ini/file/', 'debug': False}
    >>> PaosConfigurationGui(passvalue=passvalue, theme='Dark')()

    Note
    ----
    The first implementation of PaosConfigurationGui is in `PAOS` v0.0.4

    """

    def __init__(self, passvalue, theme=OFFICIAL_PYSIMPLEGUI_THEME, font=("Courier New", 16)):
        """

        """

        # ------ Define fallback configuration file ------ #
        self.passvalue = passvalue
        self.theme, self.font = theme, font

        if self.passvalue['debug']:
            setLogLevel(logging.DEBUG)

        # ------ Theme Definition ------ #
        change_look_and_feel(self.theme)

        # ------ Quick Message Definition ------ #
        w, h = Window.get_screen_size()
        popup_quick_message('Hang on for a moment, this will take a bit to create....',
                            auto_close=True, non_blocking=True, keep_on_top=True,
                            auto_close_duration=2, location=(int(0.4 * w), int(0.1 * h)))

        # ------ Menu Definition ------ #
        self.menu_def = [['&File', ['&Open', '&Save', '&Save As', '&Exit', 'Global Settings']],
                         ['&Help', '&About'], ]

        # ------ Right Click Menu Definition ------ #
        self.right_click_menu_def = ['', ['Nothing', 'Version', 'Exit']]

        # ------ Tabs Definition ------ #

        # Wavelengths
        self.WAVELENGTH_MAX_ROWS = None
        self.wl_data = {'Wavelength (micron)': ''}

        # Fields
        self.MAX_FIELDS = None
        self.field_data = {'X': '', 'Y': ''}

        # Lens data surfaces
        self.MAX_SURFACES = None
        self.lens_data = {
            'SurfaceType': {'values': ['INIT', 'Coordinate Break', 'Standard', 'Paraxial Lens', 'ABCD', 'Zernike']},
            'Comment': {'values': 'Comment'},
            'Radius': {'values': ''},
            'Thickness': {'values': ''},
            'Material': {'values': ['', 'MIRROR', 'BK7', 'BAF2', 'CAF2', 'SAPPHIRE', 'SF11', 'ZNSE']},
            'Save': {'values': 'Save'},
            'Ignore': {'values': 'Ignore'},
            'Stop': {'values': 'Stop'},
            'aperture': {'values': {'Aperture Type': ['rectangular aperture', 'rectangular obscuration',
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

        # ------ Instantiate global variables ------ #
        self.window = None
        self.config = None
        self.temporary_config = None

    def init_window(self):
        """

        """
        # ------ Config File Definition ------ #
        self.config = configparser.ConfigParser()
        if 'conf' in self.passvalue.keys() and self.passvalue['conf'] is not None:
            if not os.path.exists(self.passvalue['conf']) or not os.path.isfile(self.passvalue['conf']):
                logger.error('Input file {} does not exist or is not a file. Quitting..'.format(self.passvalue['conf']))
                sys.exit()
            self.config.read(self.passvalue['conf'])
        else:
            logger.debug('Configuration file not found. Exiting..')
            sys.exit()

        self.WAVELENGTH_MAX_ROWS = len(self.config['wavelengths']) if 'wavelengths' in self.config.keys() else 2
        self.MAX_FIELDS = len(self.config['fields']) if 'fields' in self.config.keys() else 1
        self.MAX_SURFACES = len([k for k in self.config.keys() if k.startswith('lens')])

    # ------ Functions Definition ------ #
    @staticmethod
    def add_heading(headings, size=(24, 2)):
        """

        Parameters
        ----------
        headings
        size

        Returns
        -------

        """
        headings_list = []
        for i, head in enumerate(headings):
            headings_list.append(Text(head, key=head, size=size))
        return list(itertools.chain([Text(' ' * 8)], headings_list))

    @staticmethod
    def collapse(layout, key):
        return pin(Column(layout, key=key, visible=False))

    def fill_col(self, value, key, item, size=(24, 2)):
        """

        Parameters
        ----------
        value
        key
        item
        size

        Returns
        -------

        """
        print(value, key, item)

        if key.partition('_')[0] in self.lens_data.keys():
            current_cell = re.findall('[0-9]+', key.partition('_')[-1])
            _, col = tuple(map(int, current_cell))

        default = item if item != 'NaN' else None
        disabled = False if item != 'NaN' else True

        if value in ['Save', 'Ignore', 'Stop']:
            return Checkbox(text=value, default=default, key=key, size=(21, 2), disabled=disabled)
        elif value in ['Comment', 'Radius', '']:
            return InputText(default_text=default, key=key, size=size, disabled=disabled)
        elif key.startswith('aperture'):
            return InputText(default_text=default, key=key, size=size, disabled=disabled)
        elif key.startswith('z'):
            return InputText(default_text=value, key=key, size=size, disabled=disabled)
        else:
            return InputCombo(default_value=default, values=value, key=key, size=(23, 2), disabled=disabled,
                              expand_y=True, enable_events=True)

    @staticmethod
    def par_heading_rules(surface_type):
        """

        Parameters
        ----------
        surface_type

        Returns
        -------

        """
        par_headings = []
        if surface_type in ['INIT', 'Standard']:
            par_headings = ['', '', '', '', '', '', '', '']
        elif surface_type == 'Coordinate Break':
            par_headings = ['Xtilt', 'Ytilt', 'Xdecenter', 'Ydecenter', '', '', '', '']
        elif surface_type == 'Paraxial Lens':
            par_headings = ['Focal length', '', '', '', '', '', '', '']
        elif surface_type == 'ABCD':
            par_headings = ['Ax', 'Bx', 'Cx', 'Dx', 'Ay', 'By', 'Cy', 'Dy']
        elif surface_type == 'Zernike':
            par_headings = ['Wavelength', 'Ordering', 'Normalization', 'Radius of S.A.', 'Origin', '', '', '']

        return par_headings

    def update_headings(self, row):
        """

        Parameters
        ----------
        row
        """
        par_headings = self.par_heading_rules(self.values['SurfaceType_({},0)'.format(row)])
        for head, new_head in zip([key for key in self.lens_data.keys() if key.startswith('Par')], par_headings):
            self.window[head].update(new_head)

    @staticmethod
    def lens_rules(surface_type, key, item):
        """

        Parameters
        ----------
        surface_type
        key
        item

        Returns
        -------

        """
        if surface_type == 'INIT' and key.startswith(
                ('Radius', 'Thickness', 'Material', 'Save', 'Ignore', 'Stop', 'Par')):
            item = 'NaN'

        elif surface_type == 'Coordinate Break' and (
                key.startswith(('Radius', 'Material', 'Aperture'))
                or key.startswith(('Par5', 'Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        elif surface_type == 'Standard' and key.startswith('Par'):
            item = 'NaN'

        elif surface_type == 'Paraxial Lens' and (
                key.startswith(('Radius', 'Material'))
                or key.startswith(('Par2', 'Par3', 'Par4', 'Par5', 'Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        elif surface_type == 'ABCD' and key.startswith(('Radius', 'Material')):
            item = 'NaN'

        elif surface_type == 'Zernike' and (
                key.startswith(('Radius', 'Thickness', 'Material', 'Aperture'))
                or key.startswith(('Par6', 'Par7', 'Par8'))):
            item = 'NaN'

        return item

    def add_row_data(self, row, input_list, prefix):
        """

        Parameters
        ----------
        row
        input_list
        prefix

        Returns
        -------

        """
        row_widget = [Text(row, size=(6, 1), key='row idx {}'.format(row))]

        if prefix == 'w':
            key = '{}{}'.format(prefix, row)
            item = self.config['wavelengths'].get(key, '')
            return list(itertools.chain(row_widget,
                                        [self.fill_col(value, key, item) for value in input_list]))

        elif prefix == 'f':
            key = '{}{}'.format(prefix, row)
            items = self.config['fields'].get(key, '0.0,0.0').split(',')
            keys = ['_'.join([key, str(i)]) for i in range(len(items))]
            return list(itertools.chain(row_widget,
                                        [self.fill_col(value, key, item) for value, key, item in
                                         zip(input_list, keys, items)]))

        elif prefix == 'l':
            key = 'lens_{:02d}'.format(row)

            lens_dict = {}
            for c, name in enumerate(self.lens_data.keys()):
                name_key = '{}_({},{})'.format(name, row, c)
                if key in self.config.keys() and name in self.config[key].keys():
                    lens_dict[name_key] = self.config[key].getboolean(name) \
                        if name in ['Save', 'Ignore', 'Stop'] else self.config[key][name]
                else:
                    lens_dict[name_key] = None

                surface_type_key = 'SurfaceType_({},0)'.format(row)
                surface_type = lens_dict[surface_type_key]
                lens_dict[name_key] = self.lens_rules(surface_type, name_key, lens_dict[name_key])

            return list(itertools.chain(row_widget,
                                        [self.fill_col(value, key, item)
                                         for value, (key, item) in zip(input_list, lens_dict.items())]))

        elif prefix == 'z':
            items = ['', '', '', '']
            keys = ['{}_({},{})'.format(prefix, row, i) for i in range(len(items))]
            return list(itertools.chain(row_widget,
                                        [self.fill_col(value, key, item) for value, key, item in
                                         zip(input_list, keys, items)]))

    def save_to_dict(self, show=True):
        """

        Parameters
        ----------
        show

        Returns
        -------

        """
        table = {
            'general': {
                'project': self.values['project'],
                'version': self.values['version'],
                'grid_size': self.values['grid_size'],
                'zoom': self.values['zoom'],
                'lens_unit': self.values['lens_unit']
            }
        }

        key = 'wavelengths'
        table[key] = {}
        for nwl in range(1, self.nrows_wl + 1):
            table[key]['w{}'.format(nwl)] = self.values['w{}'.format(nwl)]

        key = 'fields'
        table[key] = {}
        for nf in range(1, self.nrows_field + 1):
            fields = [self.values['f{}_{}'.format(nf, c)] for c in range(len(self.field_data.keys()))]
            table[key]['f{}'.format(nf)] = ','.join(map(str, fields))

        for r in range(1, self.nrows_ld + 1):
            key = 'lens_{:02d}'.format(r)
            table[key] = {}
            for (c, head) in enumerate(self.lens_data.keys()):
                table[key][head] = self.values['{}_({},{})'.format(head, r, c)]
                if table[key][head] == 'Zernike' and not self.config[key].getboolean('Ignore'):
                    table[key]['zindex'] = self.config[key]['zindex']
                    table[key]['z'] = self.config[key]['z']
        if not show:
            return table
        else:
            popup_scrolled('lens_data = {}'.format(table), title='Copy your data from here', font='fixedsys',
                           keep_on_top=True)

    def copy_to_clipboard(self):
        """

        Returns
        -------

        """
        table = self.save_to_dict(show=False)
        clipboard_set(table)
        return

    @staticmethod
    def get_clipboard_text():
        """

        Returns
        -------

        """
        root = Tk()
        root.withdraw()
        text = root.clipboard_get().replace('\n', ',').split(',')
        text = text if text[-1] != '' else text[:-1]
        return text

    def add_row(self, key):
        """

        Parameters
        ----------
        key

        Returns
        -------

        """
        prefix = key[0]
        nrows, input_list = None, []

        if key == 'wavelengths':
            nrows = self.nrows_wl
            input_list = [item for key, item in self.wl_data.items()]
        elif key == 'fields':
            nrows = self.nrows_field
            input_list = [item for key, item in self.field_data.items()]
        elif key == 'lenses':
            nrows = self.nrows_ld
            input_list = [item['values'] for key, item in self.lens_data.items()]
        else:
            logger.error('Key error')

        nrows += 1
        self.window.extend_layout(self.window[key], [self.add_row_data(nrows, input_list, prefix)])
        self.window[key].update()

        if key == 'lenses':
            self.config.add_section('lens_{:02d}'.format(nrows))
            for c, head in enumerate(self.lens_data.keys()):
                self.window['{}_({},{})'.format(head, nrows, c)].bind("<Button-1>", "_LeftClick")

        return nrows

    def write_to_config(self, dictionary):
        """

        Parameters
        ----------
        dictionary

        Returns
        -------
        `~configparser.ConfigParser`
        """

        write_config = configparser.ConfigParser()

        for key, item in dictionary.items():
            if isinstance(item, dict):
                write_config.add_section(key)
                for subkey, subitem in item.items():
                    if subitem is not None and subitem != "":
                        if isinstance(subitem, str):
                            pass
                        elif isinstance(subitem, (float, bool)):
                            subitem = str(subitem)
                        elif isinstance(subitem, (tuple, list)):
                            subitem = ','.join(subitem)
                        else:
                            raise NotImplementedError('item type not supported')
                    write_config.set(key, subkey, subitem)

        return write_config

    def write_to_ini_file(self, temporary=False, filename=None):
        """

        Parameters
        ----------
        temporary
        filename

        Returns
        -------

        """
        dictionary = self.save_to_dict(show=False)
        write_config = self.write_to_config(dictionary)

        if filename is not None:
            if not os.path.exists(filename) or not os.path.isfile(filename):
                logger.error('Input file {} does not exist or is not a file. Quitting..'.format(filename))
                sys.exit()
        elif temporary:
            self.temporary_config = filename = \
                os.path.join(os.path.dirname(self.passvalue['conf']),
                             ''.join(['temp_', os.path.basename(self.passvalue['conf'])]))
        else:
            filename = self.passvalue['conf']

        with open(filename, 'w') as cf:
            write_config.write(cf)
        return

    # Function for drawing
    @staticmethod
    def draw_figure(canvas, figure):
        """

        Parameters
        ----------
        canvas
        figure

        Returns
        -------

        """
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    @staticmethod
    def delete_fig_agg(fig_agg):
        """

        Parameters
        ----------
        fig_agg
        """
        logger.debug('Clearing figure canvas')
        fig_agg.get_tk_widget().forget()
        plt.close('all')

    def make_window(self):
        """

        """
        self.init_window()

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
                                            [Text('', size=(15, 1))]],
                   font=("Helvetica", 20), relief=RELIEF_SUNKEN, key='-GENERAL FRAME-', expand_x=True, expand_y=True)],
            [Frame('Wavelength Setup', layout=[[Text('', size=(15, 1))],
                                               [Column(layout=list(itertools.chain(
                                                   [self.add_heading(self.wl_data.keys())],
                                                   [self.add_row_data(r, [item for key, item in self.wl_data.items()],
                                                                      prefix='w')
                                                    for r in range(1, self.WAVELENGTH_MAX_ROWS + 1)])),
                                                   key='wavelengths',
                                                   scrollable=True, expand_x=True, expand_y=True)]],
                   font=("Helvetica", 20), relief=RELIEF_SUNKEN, key='-WL FRAME-', expand_x=True, expand_y=True)],
            [Frame('General Actions', layout=[
                [Button(tooltip='Click to add wavelength', button_text='Add Wavelength',
                        enable_events=True, key="-ADD WAVELENGTH-")],
                [Button('Paste Wavelengths', tooltip='Click to paste wavelengths', key='PASTE WL')]],
                   font=("Helvetica", 20), relief=RELIEF_SUNKEN, key='-GENERAL ACTIONS FRAME-')]
        ]

        fields_layout = [
            [Column(layout=list(itertools.chain([self.add_heading(self.field_data.keys())],
                                                [self.add_row_data(r, [item for key, item in self.field_data.items()],
                                                                   prefix='f')
                                                 for r in range(1, self.MAX_FIELDS + 1)])),
                    scrollable=True, expand_x=True, expand_y=True,
                    key='fields')],
            [Text(' ')],
            [Frame('Fields Actions', layout=[
                [Button(tooltip='Click to add field row', button_text='Add Field', enable_events=True,
                        key="-ADD FIELD-")]
            ],
                   font=("Helvetica", 20), relief=RELIEF_SUNKEN, key='-FIELDS ACTIONS FRAME-')]
        ]

        lens_data_layout = [
            [Column(layout=list(itertools.chain([self.add_heading(self.lens_data.keys())],
                                                [[Text('')]],
                                                [self.add_row_data(r, [item['values'] for key, item in
                                                                       self.lens_data.items()],
                                                                   prefix='l')
                                                 for r in range(1, self.MAX_SURFACES + 1)])),
                    scrollable=True, expand_x=False, expand_y=True,
                    key='lenses')],
            [Text(' ')],
            [Frame('Lens Data Actions', layout=[
                [Button(tooltip='Click to add surface row', button_text='Add Surface', enable_events=True,
                        key="-ADD SURFACE-")]
            ],
                   font=("Helvetica", 20),
                   relief=RELIEF_SUNKEN,
                   key='-LENS DATA ACTIONS FRAME-')]
        ]

        launcher_layout = [[Text('')],
                           list(itertools.chain(
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
                                                size=(12, 4), background_color='grey20', key='select field',
                                                enable_events=True)]))],
                                      font=("Helvetica", 20),
                                      relief=RELIEF_SUNKEN,
                                      key='-PAOS SELECT INPUTS FRAME-')
                                ],
                               [Text('', size=(100, 2))],
                               [Frame('Save', layout=[
                                   [Button(tooltip='Save raytrace output',
                                           button_text='Save raytrace',
                                           enable_events=True,
                                           key="-SAVE RAYTRACE-")],
                                   [Button(tooltip='Save POP output', button_text='Save POP',
                                           enable_events=True,
                                           key="-SAVE POP-")],
                                   [Button(tooltip='Save this plot', button_text='Save Plot',
                                           enable_events=True,
                                           key="-SAVE FIG-")]
                               ],
                                      font=("Helvetica", 20),
                                      relief=RELIEF_SUNKEN,
                                      key='-PAOS SAVE FRAME-')
                                ])),
                           [Frame('Raytrace', layout=[
                               [Text('Run a diagnostic raytrace')],
                               [Button(tooltip='Launch raytrace', button_text='Raytrace', enable_events=True,
                                       key="-RAYTRACE-")],
                               [Column(layout=[
                                   [Multiline(
                                       key='raytrace log', font=('Courier New', 10), autoscroll=True, size=(90, 20),
                                       pad=(0, (15, 0)), background_color='grey20', disabled=False)]],
                                   key='raytrace log col',
                               )]
                           ],
                                  font=("Helvetica", 20),
                                  relief=RELIEF_SUNKEN,
                                  key='-PAOS RAYTRACE FRAME-'),
                            Text('', size=(5, 2)),
                            Frame('POP', layout=[
                                list(itertools.chain([Text('Run the POP: '),
                                                      Button(tooltip='Launch POP', button_text='POP',
                                                             enable_events=True, key="-POP-")],
                                                     [Text('', size=(6, 2))],
                                                     [Text('Embed Plot: '),
                                                      Button(tooltip='Plot', button_text='Plot', enable_events=True,
                                                             key="-PLOT-")])),
                                [Canvas(key='-CANVAS-', size=(90, 20))]
                            ],
                                  font=("Helvetica", 20), relief=RELIEF_SUNKEN, expand_x=True, expand_y=True,
                                  key='-PAOS POP FRAME-')
                            ]
                           ]

        # logging_layout = [
        #     [Frame('GUI Logs', layout=[[Text("Anything printed will display here!")],
        #                                [Output(font=('Courier New', 16),
        #                                        size=(92, 34),
        #                                        pad=(0, (15, 0)),
        #                                        background_color='grey20')]],
        #            font=("Helvetica", 25),
        #            relief=RELIEF_SUNKEN,
        #            key='-LOGS FRAME-')]
        # ]

        info_layout = [
            [Frame('GUI Info', layout=[[Text('Github Repo: ')],
                                       [Text('https://github.com/arielmission-space/PAOS',
                                             font=("Courier New underline", 16),
                                             text_color='blue', enable_events=True, key='-LINK-')],
                                       [Text('')],
                                       [Text('Credits: Andrea Bocchieri and Enzo Pascale',
                                             key='-CREDITS-')],
                                       [Text('PySimpleGui version: {}'.format(version),
                                             key='-GUI VERSION-')]], font=("Helvetica", 25),
                   relief=RELIEF_SUNKEN, key='-INFO FRAME-')]
        ]

        layout = [
            [Menu(self.menu_def, tearoff=True, key='-MENU-')],
            [Text('Configuration Tabs', size=(38, 1), justification='center', font=("Helvetica", 16),
                  relief=RELIEF_RIDGE, key='-TEXT HEADING-', enable_events=True)],
            [TabGroup([
                [
                    Tab('General', general_layout, key='-GENERAL TAB-'),
                    Tab('Fields', fields_layout, key='-FIELDS TAB-'),
                    Tab('Lens Data', lens_data_layout, key='-LENS DATA TAB-'),
                    Tab('PAOS Launcher', launcher_layout, key='-PAOS LAUNCHER TAB-'),
                    # Tab('Logs', logging_layout, key='-LOGS TAB-'),
                    Tab('Info', info_layout, key='-INFO TAB-')
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
        self.window['-GUI VERSION-'].set_cursor(cursor='clock')

        # ------- Bind method for Par headings ------#
        for r, (c, head) in itertools.product(range(1, self.MAX_SURFACES + 1), enumerate(self.lens_data.keys())):
            self.window['{}_({},{})'.format(head, r, c)].bind("<Button-1>", "_LeftClick")

    def close_window(self):
        """

        """
        if self.temporary_config is not None:
            if not os.path.exists(self.temporary_config) or not os.path.isfile(self.temporary_config):
                logger.error('Input temporary file {} does not exist or is not a file. Quitting..'.format(
                    self.temporary_config))
                sys.exit()
            logger.info('Removing temporary .ini configuration file')
            os.remove(self.temporary_config)
        plt.close('all')
        self.window.close()
        del self.window
        _ = gc.collect()

    @staticmethod
    def move_with_arrow_keys(window, event, values, elem_key, max_rows, max_cols):
        """

        Parameters
        ----------
        window
        event
        values
        max_rows
        max_cols
        elem_key
        """
        current_cell = re.findall('[0-9]+', elem_key.partition('_')[-1])
        r, c = tuple(map(int, current_cell))

        if event.startswith('Down'):
            r = r + 1 * (r < max_rows)
        elif event.startswith('Left'):
            c = c - 1 * (c > 0)
        elif event.startswith('Right'):
            c = c + 1 * (c < max_cols - 1)
        elif event.startswith('Up'):
            r = r - 1 * (r > 0) if r > 1 else 1

        # if the current cell changed, set focus on new cell
        if current_cell != (r, c):
            for key in values.keys():
                if key.endswith('({},{})'.format(r, c)):
                    window[key].set_focus()  # set the focus on the element moved to
                    window[key].update()
        return r

    def add_zernike_row(self, window, row, dictionary, ordering):
        row += 1
        m, n = Zernike.j2mn(N=row, ordering=ordering)
        dictionary['zindex'].append(str(row))
        dictionary['z'].append('0.0')
        window.extend_layout(window['zernike'], [
            self.add_row_data(row=row, input_list=[str(row - 1), '0.0', int(m[row - 1]), int(n[row - 1])], prefix='z')])
        window['zernike'].update()
        return row, (m, n)

    def make_zernike_window(self, row, key):
        """

        Parameters
        ----------
        row
        key

        Returns
        -------

        """
        zernike = {}
        if key in self.config.keys() and {'zindex', 'z'}.issubset(self.config[key].keys()):
            zindex, z = self.config[key]['zindex'], self.config[key]['z']
            zernike['zindex'] = zindex.split(',') if zindex != '' else ['0']
            zernike['z'] = z.split(',') if z != '' else ['0']
        else:
            zernike['zindex'] = ['0']
            zernike['z'] = ['0']

        par = ['', '', '', '', '']
        names = ['Par1', 'Par2', 'Par3', 'Par4', 'Par5']
        for c, head in enumerate(names):
            par_key = '{}_({},{})'.format(head, row, c + 9)
            if par_key in self.values.keys() and self.values[par_key] != '':
                par[c] = self.values[par_key]
        wavelength, ordering, normalization, radius, origin = par
        if ordering == '':
            logger.warning('Zernike ordering is not defined. Exiting window...')
            return

        assert ordering in ['ansi', 'standard', 'noll', 'fringe'], 'ordering {} not supported'.format(ordering)

        max_rows = len(zernike['zindex'])
        m, n = Zernike.j2mn(N=max_rows, ordering=ordering)
        headings = ['Zindex', 'Z', 'm', 'n']

        layout = [
            [Frame('Parameters',
                   layout=[list(itertools.chain([Text('Wavelength: {}'.format(wavelength), key='wavelength')],
                                                [Text('', size=(6, 1))],
                                                [Text('Ordering: {}'.format(ordering), key='ordering')],
                                                [Text('', size=(6, 1))],
                                                [Text('Normalization: {}'.format(normalization),
                                                      key='normalization')],
                                                [Text('', size=(6, 1))],
                                                [Text('Radius of S.A.: {}'.format(radius), key='radius')],
                                                [Text('', size=(6, 1))],
                                                [Text('Origin: {}'.format(origin), key='origin')]))],
                   font=("Helvetica", 20),
                   relief=RELIEF_SUNKEN,
                   key='-ZERNIKE MEMO FRAME-',
                   )],
            [Text('', size=(10, 2))],
            [Column(layout=list(itertools.chain([self.add_heading(headings)],
                                                [self.add_row_data(i + 1,
                                                                   [r, float(zernike['z'][i]), int(m[i]), int(n[i])],
                                                                   prefix='z')
                                                 for i, r in enumerate(zernike['zindex'])])),
                    scrollable=True, expand_y=True,
                    key='zernike')],
            [Text('', size=(10, 2))],
            itertools.chain([Frame('Zernike Actions', layout=[
                [Button(tooltip='Click to add a new row',
                        button_text='Add row',
                        enable_events=True,
                        key="-ADD ZERNIKE ROW-"),
                 Button(
                     tooltip='Click to add a radial order',
                     button_text='Add/Complete radial order',
                     enable_events=True,
                     key="-ADD ZERNIKE RADIAL ORDER-")],
            ],
                                   font=("Helvetica", 20),
                                   relief=RELIEF_SUNKEN,
                                   key='-ZERNIKE ACTIONS FRAME-')]),
            [
                Button('Paste Zernike', tooltip='Click to paste Zernike coefficients', key='PASTE ZERNIKES'),
                Submit(tooltip='Click to submit (debug)', key='-SUBMIT ZERNIKES-'),
                Button(tooltip='Save coefficients to ini file',
                       button_text='Save',
                       key="SAVE ZERNIKES"),
                Button('Exit', key='-EXIT ZERNIKES-')
            ]
        ]
        window = Window('Zernike window', layout, default_element_size=(12, 1),
                        return_keyboard_events=True, finalize=True, modal=True,
                        enable_close_attempted_event=True, resizable=True,
                        element_justification='center', keep_on_top=True)

        save = False
        order_closed = False

        while True:
            event, values = window.read()
            logger.debug('============ Event = {} =============='.format(event))
            elem = window.find_element_with_focus()
            elem_key = elem.Key if (elem is not None and isinstance(elem.Key, (str, tuple))) else (0, 0)

            if isinstance(elem_key, str):
                _ = self.move_with_arrow_keys(window, event, values, elem_key, max_rows, len(headings))

            if event == "-EXIT ZERNIKES-" or event in (WINDOW_CLOSE_ATTEMPTED_EVENT, WINDOW_CLOSED):
                window.close()
                del window
                _ = gc.collect()
                break

            elif event == '-ADD ZERNIKE ROW-':
                max_rows, _ = self.add_zernike_row(window=window, row=max_rows, dictionary=zernike, ordering=ordering)

            elif event == 'PASTE ZERNIKES':
                row, col = re.findall('[0-9]+', elem_key.partition('_')[-1])
                if headings[int(col)] != 'Z':
                    logger.debug('The user shall select the starting cell from the Z column. Skipping..')
                    continue
                text = self.get_clipboard_text()
                row0 = row = int(row)
                for text_item in text:
                    window['z_({},1)'.format(row)].update(text_item)
                    if max_rows <= row < row0 + len(text) - 1:
                        max_rows, _ = self.add_zernike_row(window=window, row=max_rows, dictionary=zernike,
                                                           ordering=ordering)
                    row += 1

            elif event == '-ADD ZERNIKE RADIAL ORDER-':
                if ordering not in ['ansi', 'standard']:
                    logger.debug('Not supported with {} as ordering. Skipping..'.format(ordering.capitalize()))
                    continue
                m, n = Zernike.j2mn(N=max_rows, ordering=ordering)
                if ordering == 'standard':
                    order_closed = (min(m) == -max(n))
                elif ordering == 'ansi':
                    order_closed = (max(m) == max(n))
                if not order_closed:
                    while not order_closed:
                        max_rows, (m, n) = self.add_zernike_row(
                            window=window, row=max_rows, dictionary=zernike, ordering=ordering)
                        if ordering == 'standard':
                            order_closed = (min(m) == -max(n))
                        elif ordering == 'ansi':
                            order_closed = (max(m) == max(n))
                    continue
                new_m = new_n = max(n) + 1
                if ordering == 'standard':
                    new_m = -new_m
                jmax = Zernike.mn2j(m=new_m, n=new_n, ordering=ordering)
                while max_rows < jmax + 1:
                    max_rows, _ = self.add_zernike_row(window=window, row=max_rows, dictionary=zernike,
                                                       ordering=ordering)

            elif event == 'SAVE ZERNIKES':
                save = True

            elif event == '-SUBMIT ZERNIKES-':
                popup('Paos GUI Zernike window',
                      'You clicked on the "{}" button'.format(event),
                      'The values are', values, keep_on_top=True)

        if save:
            zernike_new = {'zindex': [], 'z': []}
            for key, item in values.items():
                row, col = re.findall('[0-9]+', key.partition('_')[-1])
                if col == '0':
                    zernike_new['zindex'].append(item)
                elif col == '1':
                    zernike_new['z'].append(item)
            zernike_new['zindex'] = ','.join(zernike_new['zindex'])
            zernike_new['z'] = ','.join(zernike_new['z'])
            return zernike_new

    def __call__(self):
        """

        """
        self.make_window()

        self.nrows_wl, self.nrows_field, self.nrows_ld = self.WAVELENGTH_MAX_ROWS, self.MAX_FIELDS, self.MAX_SURFACES
        raytrace_log, retval = '', None
        fig, fig_agg = None, None
        wavelength = None
        wavelengths: list = []
        fields: list = []
        opt_chains: list = []
        save_to_ini_file = False

        while True:  # Event Loop
            self.event, self.values = self.window.read()
            logger.debug('============ Event = {} =============='.format(self.event))

            elem = self.window.find_element_with_focus()
            elem_key = elem.Key if (elem is not None and isinstance(elem.Key, (str, tuple))) else (0, 0)

            if isinstance(elem_key, str) and elem_key.startswith(
                    tuple([head for head in self.lens_data.keys()])):
                current_row = self.move_with_arrow_keys(self.window, self.event, self.values, elem_key, self.nrows_ld,
                                                        len(self.lens_data.keys()))
                self.update_headings(current_row)

            if self.event in (WINDOW_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, 'Exit', '-EXIT-'):
                if save_to_ini_file:
                    self.write_to_ini_file()
                self.close_window()
                break

            elif isinstance(elem_key, str) and self.event == elem_key + '_LeftClick':
                current_cell = re.findall('[0-9]+', elem_key.partition('_')[-1])
                current_row, _ = tuple(map(int, current_cell))
                self.update_headings(current_row)

            elif self.event == '-SHOW DICT-':
                self.save_to_dict(show=True)

            elif self.event == 'PASTE WL':
                if not elem_key.startswith('w'):
                    logger.debug('Wavelength cell not selected. Skipping..')
                    continue
                text = self.get_clipboard_text()
                row0 = row = int(elem_key[1:])
                for text_item in text:
                    self.window['w{}'.format(row)].update(text_item)
                    if self.nrows_wl <= row < row0 + len(text) - 1:
                        self.nrows_wl = self.add_row('wavelengths')
                    row += 1

            elif self.event == '-ADD WAVELENGTH-':
                self.write_to_ini_file(temporary=True)
                self.nrows_wl = self.add_row('wavelengths')
                wl_names = list(dict.fromkeys([key.partition('_')[0] for key in self.values.keys()
                                               if key.startswith('w')]))
                wl_names.append('w{}'.format(self.nrows_wl))
                self.window["select wl"].update(wl_names)

            elif self.event == '-ADD FIELD-':
                self.write_to_ini_file(temporary=True)
                self.nrows_field = self.add_row('fields')
                field_names = list(dict.fromkeys([key.partition('_')[0] for key in self.values.keys()
                                                  if key.startswith('f')]))
                field_names.append('f{}'.format(self.nrows_field))
                self.window["select field"].update(field_names)

            elif self.event == '-ADD SURFACE-':
                self.nrows_ld = self.add_row('lenses')

            elif self.event.startswith('SurfaceType'):
                row, col = re.findall('[0-9]+', self.event)
                surface_type_key = 'SurfaceType_({},0)'.format(row)
                c = 0
                for key, value in self.lens_data.items():
                    name_key = '{}_({},{})'.format(key, row, c)
                    item = self.lens_rules(self.values[surface_type_key], name_key, self.values[name_key])
                    disabled = True if item == 'NaN' else False
                    item_column_key = '{}_({},{})'.format(key, row, c)
                    self.window[item_column_key].update(disabled=disabled)
                    c += 1
                if self.values[surface_type_key] == 'Zernike':
                    action = popup_ok_cancel('Insert/Edit Zernike coefficients', keep_on_top=True)
                    if action == 'OK':
                        key = 'lens_{:02d}'.format(int(row))
                        zernike_dict = self.make_zernike_window(row, key)
                        if zernike_dict is not None:
                            if key in self.config.keys():
                                self.config[key].update(zernike_dict)
                            else:
                                for subkey, subitem in zernike_dict.items():
                                    self.config.set(key, subkey, subitem)
                            self.write_to_ini_file(temporary=True)

            elif self.event == '-SUBMIT-':
                popup('PAOS Simple GUI',
                      'You clicked on the "{}" button'.format(self.event),
                      'The values are', self.values, keep_on_top=True)

            elif self.event == '-TO CLIPBOARD-':
                self.copy_to_clipboard()

            elif self.event in ['Save', '-SAVE-']:
                self.write_to_ini_file(temporary=True)
                save_to_ini_file = True

            elif self.event == '-LINK-':
                openwb(self.window['-LINK-'].DisplayText)

            elif self.event == 'About':
                popup('PAOS Simple GUI v0.0.4')

            elif self.event == '-RAYTRACE-':
                n_wl = int(self.values['select wl'][0][1:]) - 1
                n_field = int(self.values['select field'][0][1:]) - 1
                self.write_to_ini_file(temporary=True)
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.temporary_config)
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                raytrace_log = raytrace(field, opt_chain)
                self.window['raytrace log'].update('\n'.join(raytrace_log))

            elif self.event == '-POP-':
                n_wl = int(self.values['select wl'][0][1:]) - 1
                n_field = int(self.values['select field'][0][1:]) - 1
                self.write_to_ini_file(temporary=True)
                pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(self.temporary_config)
                wavelength, field, opt_chain = wavelengths[n_wl], fields[n_field], opt_chains[n_wl]
                retval = run(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
                             field, opt_chain)

            elif self.event == '-SAVE RAYTRACE-':
                if raytrace_log == '':
                    logger.debug('Perform raytrace first')
                    continue
                filename = popup_get_file('Choose file (TXT) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    with open(filename, "wt") as f:
                        f.write('\n'.join(raytrace_log))

            elif self.event == '-SAVE POP-':
                if retval is None:
                    logger.debug('Run POP first')
                    continue
                filename = popup_get_file('Choose file (HDF5) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    group_tags = list(map(str, [wavelength]))
                    save_datacube([retval], filename, group_tags, keys_to_keep=['amplitude', 'dx', 'dy', 'wl'],
                                  overwrite=True)

            elif self.event == '-PLOT-':
                if retval is None:
                    logger.debug('Run POP first')
                    continue
                if fig_agg is not None:
                    self.delete_fig_agg(fig_agg)
                fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
                key = list(retval.keys())[-1]  # plot at last optical surface
                plot_psf_xsec(fig=fig, axis=axs[0], key=key, item=retval[key], ima_scale='log', x_units='standard')
                simple_plot(fig=fig, axis=axs[1], key=key, item=retval[key], ima_scale='log')
                fig.suptitle(axs[0].get_title(), fontsize=20)
                axs[0].set_title('X-sec view')
                axs[1].set_title('2D view')
                fig.tight_layout()
                fig_agg = self.draw_figure(self.window['-CANVAS-'].TKCanvas, fig)
                fig_agg.draw()

            elif self.event == '-SAVE FIG-':
                if retval is None or fig_agg is None:
                    logger.debug('Create plot first')
                    continue
                filename = popup_get_file('Choose file (PNG, JPG) to save to', save_as=True, keep_on_top=True)
                if filename is not None:
                    fig.savefig(filename, bbox_inches='tight', dpi=150)

            elif self.event == 'select wl':
                n_wl = int(self.values['select wl'][0][1:]) - 1
                if wavelengths is not None:
                    if n_wl > len(wavelengths) - 1 or (
                            n_wl <= len(wavelengths) - 1 and wavelength != wavelengths[n_wl]):
                        if retval is not None:
                            retval = None
                        if fig_agg is not None:
                            self.delete_fig_agg(fig_agg)
                            fig_agg = None

            elif self.event == 'select field':
                n_field = int(self.values['select field'][0][1:]) - 1
                if fields is not None:
                    if n_field > len(fields) - 1 or (n_field <= len(fields) - 1 and fields != fields[n_field]):
                        if retval is not None:
                            retval = None
                        if raytrace_log is not None:
                            raytrace_log = ''
                            self.window['raytrace log'].update(raytrace_log)
                        if fig_agg is not None:
                            self.delete_fig_agg(fig_agg)
                            fig_agg = None

            elif self.event == 'Open':
                self.passvalue['conf'] = popup_get_file('Choose configuration (INI) file', keep_on_top=True)
                self.close_window()
                PaosConfigurationGui(passvalue=self.passvalue, theme=self.theme)()

            elif self.event == 'Save As':
                filename = popup_get_file('Choose file (INI) to save to', save_as=True, keep_on_top=True)
                self.write_to_ini_file(filename=filename)

            elif self.event == 'Global Settings':
                main_global_pysimplegui_settings()

            elif self.event == 'Version':
                popup_scrolled(get_versions(), keep_on_top=True)

        sys.exit()
