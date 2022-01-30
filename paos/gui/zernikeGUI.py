import itertools
import re
import sys

from PySimpleGUI import RELIEF_SUNKEN
from PySimpleGUI import Submit
from PySimpleGUI import Text, Button, Column, Frame
from PySimpleGUI import Window, WINDOW_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT
from PySimpleGUI import popup

from paos import Zernike
from paos.gui.simpleGUI import SimpleGUI
from paos.paos_config import logger


class ZernikeGUI(SimpleGUI):
    """
    Generates the Zernike editor for the `PAOS` GUI

    Parameters
    ----------
    config: :class:`~configparser.ConfigParser` object
    values: dict
    row: int
    key: str

    """

    def __init__(self, config, values, row, key):
        super().__init__()
        self.config = config
        self.values = values
        self.row = row
        self.key = key

        self.window = None
        self.zernike = {}
        self.ordering = None
        self.par = ['', '', '', '', '']
        self.names = ['Par1', 'Par2', 'Par3', 'Par4', 'Par5']
        self.headings = ['Zindex', 'Z', 'm', 'n']
        self.max_rows = None

    def add_row(self, row, dictionary, ordering):
        """

        Parameters
        ----------
        row
        dictionary
        ordering

        Returns
        -------

        """
        row += 1

        m, n = Zernike.j2mn(N=row, ordering=ordering)
        dictionary['zindex'].append(str(row))
        dictionary['z'].append('0.0')
        input_list = [str(row - 1), '0.0', m[row - 1], n[row - 1]]

        self.window.extend_layout(self.window['zernike'],
                                  [self.chain_widgets(row=row, input_list=input_list, prefix='z')])
        # Update the GUI Zernike tab
        self.window['zernike'].update()

        return row, (m, n)

    def make_window(self):
        """


        Returns
        -------

        """

        if self.key in self.config.keys() and {'zindex', 'z'}.issubset(self.config[self.key].keys()):
            zindex, z = self.config[self.key]['zindex'], self.config[self.key]['z']
            self.zernike['zindex'] = zindex.split(',') if zindex != '' else ['0']
            self.zernike['z'] = z.split(',') if z != '' else ['0']
        else:
            self.zernike['zindex'] = ['0']
            self.zernike['z'] = ['0']

        self.max_rows = len(self.zernike['zindex'])
        if len(self.zernike['z']) != self.max_rows:
            logger.error('Input zernike index and zernike coefficients differ in length. Quitting...')
            sys.exit()

        for c, head in enumerate(self.names):
            par_key = '{}_({},{})'.format(head, self.row, c + 9)
            if par_key in self.values.keys() and self.values[par_key] != '':
                self.par[c] = self.values[par_key]
        wavelength, self.ordering, normalization, radius, origin = self.par
        if self.ordering == '':
            logger.warning('Zernike ordering is not defined. Defaulting to ordering=standard.')
            self.ordering = 'standard'

        assert self.ordering in ['ansi', 'standard', 'noll', 'fringe'], 'ordering {} not supported'.format(
            self.ordering)

        m, n = Zernike.j2mn(N=self.max_rows, ordering=self.ordering)

        layout = [
            [Frame('Parameters',
                   layout=[list(itertools.chain(
                       [Text('Wavelength: {}'.format(wavelength), key='wavelength')],
                       [Text('', size=(6, 1))],
                       [Text('Ordering: {}'.format(self.ordering), key='ordering')],
                       [Text('', size=(6, 1))],
                       [Text('Normalization: {}'.format(normalization),
                             key='normalization')],
                       [Text('', size=(6, 1))],
                       [Text('Radius of S.A.: {}'.format(radius), key='radius')],
                       [Text('', size=(6, 1))],
                       [Text('Origin: {}'.format(origin), key='origin')]))],
                   font=self.font_titles,
                   relief=RELIEF_SUNKEN,
                   key='-ZERNIKE MEMO FRAME-',
                   )],
            [Text('', size=(10, 2))],
            [Column(layout=list(itertools.chain(
                [self.add_heading(self.headings)],
                [self.chain_widgets(row=i + 1,
                                    input_list=[r, float(self.zernike['z'][i]), int(m[i]), int(n[i])],
                                    prefix='z')
                 for i, r in enumerate(self.zernike['zindex'])])),
                scrollable=True, vertical_scroll_only=True, expand_y=True, key='zernike')],
            [Text('', size=(10, 2))],
            itertools.chain([
                Frame('Zernike Actions', layout=[
                    [Button(tooltip='Click to add a new row',
                            button_text='Add row',
                            enable_events=True,
                            key="-ADD ZERNIKE ROW-"),
                     Button(
                         tooltip='Click to add a radial order',
                         button_text='Add/Complete radial order',
                         enable_events=True,
                         key="-ADD ZERNIKE RADIAL ORDER-")]],
                      font=self.font_titles,
                      relief=RELIEF_SUNKEN,
                      key='-ZERNIKE ACTIONS FRAME-')]),
            [
                Button('Paste Zernike', tooltip='Click to paste Zernike coefficients', key='PASTE ZERNIKES'),
                Submit(tooltip='Click to submit (debug)', key='-SUBMIT ZERNIKES-'),
                Button('Exit', key='-EXIT ZERNIKES-')
            ]
        ]

        self.window = Window('Zernike window', layout, default_element_size=(12, 1),
                             return_keyboard_events=True, finalize=True,
                             enable_close_attempted_event=True, resizable=True,
                             element_justification='center', keep_on_top=True)

    def __call__(self):
        """
        Returns a rendering of the GUI Zernike window and handles the event loop.
        """

        self.make_window()

        order_closed = False

        while True:
            event, values = self.window.read()
            logger.debug('============ Event = {} =============='.format(event))
            elem = self.window.find_element_with_focus()
            elem_key = elem.Key if (elem is not None and isinstance(elem.Key, (str, tuple))) else (0, 0)

            if isinstance(elem_key, str):
                _ = self.move_with_arrow_keys(self.window, event, values, elem_key, self.max_rows, len(self.headings))

            if event == "-EXIT ZERNIKES-" or event in (WINDOW_CLOSE_ATTEMPTED_EVENT, WINDOW_CLOSED):
                self.close_window()
                break

            elif event == '-ADD ZERNIKE ROW-':
                self.max_rows, _ = self.add_row(row=self.max_rows, dictionary=self.zernike, ordering=self.ordering)

                # Update the 'zernike' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key='zernike')

            elif event == 'PASTE ZERNIKES' and isinstance(elem_key, str):
                row, col = re.findall('[0-9]+', elem_key.partition('_')[-1])
                if self.headings[int(col)] != 'Z':
                    logger.debug('The user shall select any cell from from the Z column. Skipping..')
                    continue
                text = self.get_clipboard_text()
                row0 = row = int(row)
                for text_item in text:
                    self.window['z_({},1)'.format(row)].update(text_item)
                    if self.max_rows <= row < row0 + len(text) - 1:
                        self.max_rows, _ = self.add_row(row=self.max_rows, dictionary=self.zernike,
                                                        ordering=self.ordering)
                    row += 1

                # Update the 'zernike' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key='zernike')

            elif event == '-ADD ZERNIKE RADIAL ORDER-':

                if self.ordering not in ['ansi', 'standard']:
                    logger.debug('Not supported with {} as ordering. Skipping..'.format(self.ordering.capitalize()))
                    continue

                m, n = Zernike.j2mn(N=self.max_rows, ordering=self.ordering)
                if self.ordering == 'standard':
                    order_closed = (min(m) == -max(n))
                elif self.ordering == 'ansi':
                    order_closed = (max(m) == max(n))

                if not order_closed:
                    while not order_closed:
                        self.max_rows, (m, n) = self.add_row(
                            row=self.max_rows, dictionary=self.zernike, ordering=self.ordering)
                        if self.ordering == 'standard':
                            order_closed = (min(m) == -max(n))
                        elif self.ordering == 'ansi':
                            order_closed = (max(m) == max(n))
                    continue

                new_m = new_n = max(n) + 1
                if self.ordering == 'standard':
                    new_m = -new_m
                jmax = Zernike.mn2j(m=new_m, n=new_n, ordering=self.ordering)
                while self.max_rows < jmax + 1:
                    self.max_rows, _ = self.add_row(row=self.max_rows, dictionary=self.zernike, ordering=self.ordering)

                # Update the 'zernike' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key='zernike')

            # ------- Display a popup window with the Zernike GUI values given as a flat dictionary ------#
            elif event == '-SUBMIT ZERNIKES-':
                popup('Paos GUI Zernike window',
                      'You clicked on the "{}" button'.format(event),
                      'The values are', values, keep_on_top=True)

        zernike = {'zindex': [], 'z': []}
        for key, item in values.items():
            row, col = re.findall('[0-9]+', key.partition('_')[-1])
            if col == '0':
                zernike['zindex'].append(item)
            elif col == '1':
                zernike['z'].append(item)
        zernike['zindex'] = ','.join(zernike['zindex'])
        zernike['z'] = ','.join(zernike['z'])
        zernike['ordering'] = self.ordering

        return zernike
