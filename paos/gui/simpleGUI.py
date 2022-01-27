import configparser
import itertools
import os
import sys
import gc
import re
from tkinter import Tk
from typing import List

from PySimpleGUI import Text, Column, Canvas, InputText
from PySimpleGUI import Window
from PySimpleGUI import clipboard_set
from PySimpleGUI import pin
from PySimpleGUI import popup_quick_message
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from paos.paos_config import logger


class SimpleGUI:

    """
    Base class for the Graphical User Interface (GUI) for `PAOS`, built using the publicly available library PySimpleGUI
    """

    def __init__(self):
        """
        Initializes the GUI.
        This includes instantiating the global variables, defining the GUI theme and symbols to use, defining a quick
        message to display when opening the GUI that auto-closes itself and defining the GUI Menu (principal and
        right-click)
        """

        # ------ Instantiate global variables ------ #
        self.window = None
        self.config = None
        self.temporary_config = None
        self.font_titles = ("Helvetica", 20)
        self.font_subtitles = ("Helvetica", 18)
        self.font_small = ("Courier New", 10)
        self.font_underlined = ("Courier New underline", 16)

        # ------ Quick Message Definition ------ #
        w, h = Window.get_screen_size()
        popup_quick_message('Hang on for a moment, this will take a bit to create...',
                            auto_close=True, non_blocking=True, keep_on_top=True,
                            auto_close_duration=2, location=(int(0.4 * w), int(0.1 * h)))

        # ------ Menu Definition ------ #
        self.menu_def = [['&File', ['&Open', '&Save', '&Save As', '&Exit', 'Global Settings']],
                         ['&Help', '&About'], ]

        # ------ Right Click Menu Definition ------ #
        self.right_click_menu_def = ['', ['Nothing', 'Version', 'Exit']]

        # ------ Symbols Definition ------ #
        self.symbol_up = '▲'
        self.symbol_down = '▼'
        self.symbol_disabled = '...'

    @staticmethod
    def add_heading(headings, size=(24, 2)):
        """
        Given a list of header names and a tuple for the size, returns a chained list of Text widgets with the specified
        size where the first element is returned to prettify spacing

        Parameters
        ----------
        headings: list
            a list of header names
        size: tuple
            a tuple for the widget sizes defined as (width, height)

        Returns
        -------
        out: List[Text]
            a chained list of Text widgets

        """
        headings_list = []
        for i, head in enumerate(headings):
            headings_list.append(Text(head, key=head, size=size))
        return list(itertools.chain([Text(' ' * 8)], headings_list))

    @staticmethod
    def collapse(layout, key):
        """
        Copyright 2020 PySimpleGUI.org
        Helper function that creates a Column that can be later made hidden, thus appearing "collapsed"

        Parameters
        ----------
        layout: List[List[Element]]
            The layout for the section
        key: str
            Key used to make this section visible / invisible

        Returns
        -------
        out: Column
            A pinned column that can be placed directly into your layout

        """
        return pin(Column(layout, key=key, visible=False))

    @staticmethod
    def get_clipboard_text():
        """
        Returns a copy of the local clipboard content (e.g. an Excel column)

        Returns
        -------
        out: List[str]
            the local copy of the clipboard's content
        """
        root = Tk()
        root.withdraw()
        text = root.clipboard_get().replace('\n', ',').split(',')
        text = text if text[-1] != '' else text[:-1]
        return text

    @staticmethod
    def to_configparser(dictionary):
        """
        Given a dictionary, it converts it into a `~configparser.ConfigParser` object

        Parameters
        ----------
        dictionary: dict
            input dictionary to be converted

        Returns
        -------
        out: `~configparser.ConfigParser`
        """

        config = configparser.ConfigParser()

        for key, item in dictionary.items():
            if isinstance(item, dict):
                config.add_section(key)
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
                    config.set(key, subkey, subitem)

        return config

    @staticmethod
    def draw_figure(figure, canvas):
        """
        Given a Canvas and a figure, it draws the figure onto the Canvas

        Parameters
        ----------
        figure: `~matplotlib.figure.Figure`
            the figure to be drawn
        canvas: Canvas
            the canvas onto which to draw the figure

        Returns
        -------
        out: FigureCanvasTkAgg
            the Tkinter widget to draw a `~matplotlib.figure.Figure` onto a Canvas
        """
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    @staticmethod
    def delete_figure(fig_agg):
        """
        Given a FigureCanvasTkAgg widget, it deletes it and closes the corresponding plot

        Parameters
        ----------
        fig_agg: FigureCanvasTkAgg
            the Tkinter widget to draw a `~matplotlib.figure.Figure` onto a Canvas

        Returns
        -------
        out: None
            deletes a FigureCanvasTkAgg widget and closes the corresponding plot
        """
        logger.debug('Clearing figure canvas')
        fig_agg.get_tk_widget().forget()
        plt.close()

        return

    @staticmethod
    def move_with_arrow_keys(window, event, values, elem_key, max_rows, max_cols):
        """
        Given the current GUI window, the latest event, the dictionary containing the window values, the dictionary key
        for the cell with focus and the maximum sizes for the current table editor, this method sets the focus on
        the new cell (if the current cell changed).

        Parameters
        ----------
        window: Window
            the current GUI window
        event: str
            the latest GUI event
        values: dict
            the dictionary containing the window values
        elem_key: str
            the dictionary key for the cell with focus
        max_rows: int
            the number of rows for the current table editor
        max_cols: int
            the number of columns for the current table editor

        Returns
        -------
        out: int
            The row number corresponding to where the current focus is
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

    @staticmethod
    def copy_to_clipboard(dictionary):
        """
        Saves the relevant data from the GUI configuration tabs into a dictionary, then copies it to the local clipboard

        Returns
        -------
        out: None
            copies the data to the local clipboard
        """
        clipboard_set(str(dictionary))
        return

    @staticmethod
    def chain_widgets(row, input_list, prefix):
        """
        Given the row in the GUI editor, an input list and the key prefix, returns a list of widgets

        Parameters
        ----------
        row: int
            the current row in the GUI editor
        input_list: List
            the item list to insert in the cell widgets
        prefix: str
            the key prefix

        Returns
        -------
        out: List[Text, List[Checkbox or Input or Column or Combo]]
            list of widgets
        """
        row_widget = [Text(row, size=(6, 1), key='row idx {}'.format(row))]
        keys = ['{}_({},{})'.format(prefix, row, i) for i in range(len(input_list))]

        return list(itertools.chain(row_widget,
                                    [InputText(default_text=value, key=key, size=(24, 2))
                                     for value, key in zip(input_list, keys)]
                                    ))

    def close_window(self):
        """
        Closes the GUI window and deletes the temporary .ini file (if present) and any plots in the process
        """

        # ------ Remove temporary config ------ #
        if self.temporary_config is not None:
            if not os.path.exists(self.temporary_config) or not os.path.isfile(self.temporary_config):
                logger.error('Input temporary file {} does not exist or is not a file. Quitting..'.format(
                    self.temporary_config))
                sys.exit()
            logger.info('Removing temporary .ini configuration file')
            os.remove(self.temporary_config)

        # ------ Close plots ------ #
        plt.close('all')

        # ------ Close Window ------ #
        self.window.close()
        del self.window

        # ------ Collect garbage ------ #
        _ = gc.collect()

        return
