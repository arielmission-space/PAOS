import configparser
import gc
import io
import itertools
import os
import re
import sys
from tkinter import Tk
from typing import List

from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PySimpleGUI import Canvas
from PySimpleGUI import Checkbox
from PySimpleGUI import clipboard_set
from PySimpleGUI import Column
from PySimpleGUI import Frame
from PySimpleGUI import InputText
from PySimpleGUI import pin
from PySimpleGUI import popup_get_file
from PySimpleGUI import popup_quick_message
from PySimpleGUI import ProgressBar
from PySimpleGUI import Text
from PySimpleGUI import Window

from paos import logger
from paos import save_datacube
from paos.core.plot import plot_psf_xsec
from paos.core.plot import simple_plot


class SimpleGui:
    """
    Base class for the Graphical User Interface (GUI) for ``PAOS``, built using the publicly available library PySimpleGUI
    """

    def __init__(self):
        """
        Initializes the GUI.
        This includes instantiating the global variables, defining the symbols to use
        and defining the GUI Menu (principal and right-click)
        """

        # ------ Instantiate global variables ------ #
        self.window = None
        self.config = None
        self.temporary_config = None
        self.font_titles = ("Helvetica", 20)
        self.font_subtitles = ("Helvetica", 18)
        self.font_small = ("Courier New", 10)
        self.font_underlined = ("Courier New underline", 16)

        # ------ Menu Definition ------ #
        self.menu_def = [
            [
                "&File",
                ["&Open", "&Save", "&Save As", "Global Settings", "&Exit"],
            ],
            ["&Help", "&About"],
        ]

        # ------ Right Click Menu Definition ------ #
        self.right_click_menu_def = ["", ["Nothing", "Version", "Exit"]]

        # ------ Symbols Definition ------ #
        self.triangle_right = "▶"
        self.triangle_down = "▼"
        self.symbol_disabled = "◯"
        self.symbol_state = "●"

        # ------ Quick Message Definition ------ #
        w, h = Window.get_screen_size()
        popup_quick_message(
            "Hang on for a moment, this will take a bit to create....",
            auto_close=True,
            non_blocking=True,
            keep_on_top=True,
            auto_close_duration=2,
            location=(int(0.4 * w), int(0.1 * h)),
        )

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
        return list(itertools.chain([Text(" " * 8)], headings_list))

    @staticmethod
    def collapse_frame(title, layout, key):
        """
        Helper function that creates a Frame that can be later made hidden, thus appearing "collapsed"

        Parameters
        ----------
        title: str
            the Frame title
        layout: List[List[Element]]
            the layout for the section
        key: str
            key used to make this section visible / invisible

        Returns
        -------
        out: Frame
            A pinned Frame that can be placed directly into your layout

        """
        return pin(Frame(title=title, layout=layout, key=key, visible=False))

    @staticmethod
    def collapse_column(layout, key):
        """
        Helper function that creates a Column that can be later made hidden, thus appearing "collapsed"

        Parameters
        ----------
        layout: List[List[Element]]
            the layout for the section
        key: str
            key used to make this section visible / invisible

        Returns
        -------
        out: Column
            A pinned Column that can be placed directly into your layout

        """
        return pin(Column(layout=layout, key=key, visible=False))

    @staticmethod
    def update_column_scrollbar(window, col_key):
        """
        Given the current GUI window and the current Column key, updates the column scrollbar if the Column has changed

        Parameters
        ----------
        window: Window
            the current GUI window
        col_key: str
            the current Column key

        Returns
        -------
        out: None
            Updates the column scrollbar

        """
        window.refresh()
        window[col_key].contents_changed()
        return

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
        text = root.clipboard_get().replace("\n", ",").split(",")
        text = text if text[-1] != "" else text[:-1]
        return text

    @staticmethod
    def to_configparser(dictionary):
        """
        Given a dictionary, it converts it into a :class:`~configparser.ConfigParser` object

        Parameters
        ----------
        dictionary: dict
            input dictionary to be converted

        Returns
        -------
        out: :class:`~configparser.ConfigParser`
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
                            subitem = ",".join(subitem)
                        else:
                            raise NotImplementedError("item type not supported")
                    config.set(key, subkey, subitem)

        return config

    def to_hdf5(self, retval_list, groups, keys_to_keep=None):
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
            keys_to_keep = ["amplitude", "dx", "dy", "wl"]

        if not retval_list:
            logger.error("Run POP first")
            return

        # Get the file path to save to
        filename = popup_get_file(
            "Choose file (HDF5) to save to",
            default_path=self.passvalue["output"],
            default_extension=".h5",
            save_as=True,
            keep_on_top=True,
        )

        if filename is None:
            logger.warning("Pressed Cancel. Continuing...")
            return

        if not filename.endswith((".HDF5", ".hdf5", ".H5", ".h5")):
            logger.debug("Saving file format not provided. Defaulting to .h5")
            filename = "".join([filename, ".h5"])

        # Save the POP output to the specified .hdf5 file
        tags = list(map(str, groups))
        save_datacube(
            retval_list,
            filename,
            tags,
            keys_to_keep=keys_to_keep,
            overwrite=True,
        )
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

        if text_list == "":
            logger.error("Perform raytrace first")
            return

        # Get the file path to save to
        filename = popup_get_file(
            "Choose file (TXT) to save to", save_as=True, keep_on_top=True
        )

        if filename is None:
            logger.warning("Pressed Cancel. Continuing...")
            return

        if not filename.endswith((".TXT", ".txt")):
            logger.debug("Saving file format not provided. Defaulting to .txt")
            filename = "".join([filename, ".txt"])

        # Save the text list to the specified .txt file
        with open(filename, "w") as f:
            f.write("\n".join(text_list))
        return

    @staticmethod
    def draw_figure(figure, canvas):
        """
        CURRENTLY NOT USED
        Given a Canvas and a figure, it draws the figure onto the Canvas

        Parameters
        ----------
        figure: :class:`~matplotlib.figure.Figure`
            the figure to be drawn
        canvas: Canvas
            the canvas onto which to draw the figure

        Returns
        -------
        out: FigureCanvasTkAgg
            the Tkinter widget to draw a :class:`~matplotlib.figure.Figure` onto a Canvas
        """
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
        return figure_canvas_agg

    @staticmethod
    def draw_image(figure, element):
        """
        Draws the previously created "figure" in the supplied Image Element

        Parameters
        ----------
        figure: :class:`~matplotlib.figure.Figure`
            a Matplotlib figure
        element: Image
            an Image element

        Returns
        -------
        out: Canvas
            The figure canvas

        """

        if figure is None:
            logger.error("Plot first")
            return

        plt.close("all")  # erases previously drawn plots
        canvas = FigureCanvasAgg(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format="png")
        if buf is not None:
            buf.seek(0)
            element.update(data=buf.read())
            element.update(visible=True)
            return canvas
        else:
            return None

    @staticmethod
    def clear_image(element):
        """
        Given an Image widget, it clears it

        Parameters
        ----------
        element: Image
            the Image widget to clear

        Returns
        -------
        out: None
            clears an Image widget
        """
        logger.debug("Clearing image")
        element.update()
        element.update(visible=False)

        return

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
            logger.error("Create plot first")
            return

        if filename is None:
            # Get the file path to save to
            filename = popup_get_file(
                "Choose file (PNG, JPG) to save to",
                save_as=True,
                keep_on_top=True,
            )

            if filename is None:
                logger.warning("Pressed Cancel. Continuing...")
                return

            if not filename.endswith((".PNG", ".png", ".JPG", ".jpg")):
                logger.debug("Saving file format not provided. Defaulting to .png")
                filename = "".join([filename, ".png"])

        # Save the plot to the specified .png or .jpg file
        figure.savefig(filename, bbox_inches="tight", dpi=150)

        logger.debug(f"Saved figure to {filename}")

        return

    @staticmethod
    def reset_progress_bar(progress_bar):
        """
        Given a progress bar element, it resets it

        Parameters
        ----------
        progress_bar: ProgressBar
            the progress bar element to reset

        Returns
        -------
        out: ProgressBar
            resets the progress bar element
        """
        progress_bar.metadata = 0
        progress_bar.update_bar(progress_bar.metadata)
        return progress_bar

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
        current_cell = re.findall("[0-9]+", elem_key.partition("_")[-1])
        r, c = tuple(map(int, current_cell))

        if event.startswith("Down"):
            r = r + 1 * (r < max_rows)
        elif event.startswith("Left"):
            c = c - 1 * (c > 0)
        elif event.startswith("Right"):
            c = c + 1 * (c < max_cols - 1)
        elif event.startswith("Up"):
            r = r - 1 * (r > 0) if r > 1 else 1

        # if the current cell changed, set focus on new cell
        if current_cell != (r, c):
            for key in values.keys():
                if key.endswith(f"({r},{c})"):
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
    def chain_widgets(row, input_list, prefix, disabled_list=None):
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
        disabled_list: list[bool]
            list with options to disable widgets

        Returns
        -------
        out: List[Text, List[Checkbox or Input or Column or Combo]]
            list of widgets
        """
        if disabled_list is None:
            disabled_list = []
        row_widget = [Text(row, size=(6, 1), key=f"row idx {row}")]
        keys = [f"{prefix}_({row},{i})" for i in range(len(input_list))]

        if not disabled_list:
            disabled_list = [False for _ in input_list]

        return list(
            itertools.chain(
                row_widget,
                [
                    InputText(
                        default_text=value,
                        key=key,
                        size=(24, 2),
                        disabled=disabled,
                    )
                    for value, key, disabled in zip(input_list, keys, disabled_list)
                ],
            )
        )

    def make_visible(self, event, visible, key):
        """
        Given the current event, a boolean and the widget key, it makes the widget visible/invisible

        Parameters
        ----------
        event: str
            the current event
        visible: bool
            if True, the widget becomes visible. If False, it becomes invisible
        key: str
            the widget key

        Returns
        -------
        out: bool
            the updated visibile parameter of the widget

        """
        visible = not visible
        self.window[key].update(visible=visible)
        # Update the triangle symbol
        self.window[event].update(
            self.triangle_down if visible else self.triangle_right
        )

        return visible

    def close_window(self):
        """
        Deletes the temporary .ini file (if present), any unsaved outputs and then closes the GUI window

        Returns
        -------
        out: None
            closes the GUI window and cleans up the memory
        """

        # ------ Remove temporary config ------ #
        if self.temporary_config is not None:
            if not os.path.exists(self.temporary_config) or not os.path.isfile(
                self.temporary_config
            ):
                logger.error(
                    f"Input temporary file {self.temporary_config} does not exist or is not a file. "
                    f"Quitting.."
                )
                sys.exit()
            logger.info("Removing temporary .ini configuration file")
            os.remove(self.temporary_config)

        # ------ Close plots ------ #
        plt.close("all")

        # ------ Close Window ------ #
        self.window.close()
        del self.window

        # ------ Collect garbage ------ #
        _ = gc.collect()

        return

    @staticmethod
    def sort_column(window, values, col_key):
        """
        Given a GUI window, the window contents (values) and the Column key, it sorts the Column elements in
        increasing order

        Parameters
        ----------
        window: Window
            the GUI window
        values: dict
            the dictionary with the Window contents
        col_key: str
            the Column key

        Returns
        -------
        out: None
            Sorts the Column elements in ascending order

        """
        col_values = []
        keys = []
        for key, item in values.items():
            if key.startswith(col_key):
                col_values.append(item)
                keys.append(key)

        if "" in col_values:
            logger.warning("Invalid wavelength in column. Continuing..")
            return

        col_values = list(map(float, col_values))
        col_values.sort()
        col_values = list(map(str, col_values))

        for key, value in zip(keys, col_values):
            window[key].update(value)

        return
