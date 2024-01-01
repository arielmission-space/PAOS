import configparser
import copy
import gc
import itertools
import logging
import os
import re
import sys
import time
from typing import List
from webbrowser import open as openwb

import numpy as np
from astropy.io import ascii
from joblib import delayed
from joblib import Parallel
from matplotlib import pyplot as plt
from PySimpleGUI import Button
from PySimpleGUI import Checkbox
from PySimpleGUI import Column
from PySimpleGUI import Combo
from PySimpleGUI import Frame
from PySimpleGUI import get_versions
from PySimpleGUI import Image
from PySimpleGUI import Input
from PySimpleGUI import InputCombo
from PySimpleGUI import InputText
from PySimpleGUI import Listbox
from PySimpleGUI import main_global_pysimplegui_settings
from PySimpleGUI import Menu
from PySimpleGUI import Multiline
from PySimpleGUI import popup
from PySimpleGUI import popup_get_file
from PySimpleGUI import popup_get_folder
from PySimpleGUI import popup_ok_cancel
from PySimpleGUI import popup_scrolled
from PySimpleGUI import ProgressBar
from PySimpleGUI import RELIEF_FLAT
from PySimpleGUI import RELIEF_RIDGE
from PySimpleGUI import RELIEF_SUNKEN
from PySimpleGUI import Slider
from PySimpleGUI import Submit
from PySimpleGUI import Tab
from PySimpleGUI import TabGroup
from PySimpleGUI import Text
from PySimpleGUI import TIMEOUT_KEY
from PySimpleGUI import version
from PySimpleGUI import Window
from PySimpleGUI import WINDOW_CLOSE_ATTEMPTED_EVENT
from PySimpleGUI import WINDOW_CLOSED
from tqdm import tqdm

from paos import __author__
from paos import __pkg_name__
from paos import __url__
from paos import __version__
from paos import logger
from paos import parse_config
from paos import raytrace
from paos import run
from paos.core.parseConfig import getfloat
from paos.core.plot import plot_surface
from paos.gui.simpleGui import SimpleGui
from paos.gui.zernikeGui import ZernikeGui
from paos.log import setLogLevel


class PaosGui(SimpleGui):
    """
    Generates the Graphical User Interface (GUI) for ``PAOS``, built using the publicly available library PySimpleGUI

    Parameters
    ----------
    passvalue: dict
        input dictionary for the GUI.
        It contains the file path to the input configuration .ini file to pass (defaults to using a template if
        unspecified), the debug and logger keywords and the file path to the output file to write.
    font: tuple
        GUI default font. By default, it is set to ("Courier New", 16)


    Example
    -------
    >>> from paos.gui.paosGui import PaosGui
    >>> passvalue = {'conf': '/path/to/ini/file/', 'debug': False}
    >>> PaosGui(passvalue=passvalue)()

    Note
    ----
    The first implementation of PaosGUI is in ``PAOS`` v0.0.4

    """

    def __init__(self, passvalue, font=("Courier New", 16)):
        """
        Initializes the Paos GUI.
        This includes instantiating the global variables, setting up the debug logger (optional), defining the content
        to display in the main GUI Tabs and a fallback configuration file if the user did not specify it
        """

        # ------ Instantiate global variables ------ #
        super().__init__()
        self.passvalue = passvalue
        self.font = font

        # ------ Set up the debug logger ------ #
        if self.passvalue["debug"]:
            setLogLevel(logging.DEBUG)

        # ------ Tabs Definition ------ #
        # Wavelengths
        self.wavelengths = None
        self.wl_keys = None
        self.nrows_wl = None
        self.wl_data = {"Wavelength": ""}

        # Fields
        self.fields = None
        self.field_keys = None
        self.nrows_field = None
        self.field_data = {"X": "", "Y": ""}

        # Lens data surfaces
        self.ld_keys = None
        self.nrows_ld = None
        self.lens_data = {
            "SurfaceType": [
                "INIT",
                "Coordinate Break",
                "Standard",
                "Paraxial Lens",
                "ABCD",
                "Zernike",
            ],
            "Comment": "Comment",
            "Radius": "",
            "Thickness": "",
            "Material": [
                "",
                "MIRROR",
                "BK7",
                "BAF2",
                "CAF2",
                "SAPPHIRE",
                "SF11",
                "ZNSE",
            ],
            "Save": "Save",
            "Ignore": "Ignore",
            "Stop": "Stop",
            "aperture": {
                "Aperture Type": [
                    "",
                    "rectangular aperture",
                    "rectangular obscuration",
                    # "circular aperture",
                    # "circular obscuration",
                    "elliptical aperture",
                    "elliptical obscuration",
                ],
                "X-Half Width": "",
                "Y-Half Width": "",
                "Aperture X-Decenter": "",
                "Aperture Y-Decenter": "",
            },
            "Par1": "",
            "Par2": "",
            "Par3": "",
            "Par4": "",
            "Par5": "",
            "Par6": "",
            "Par7": "",
            "Par8": "",
        }

        # ------ Define fallback configuration file ------ #
        if "conf" not in self.passvalue.keys() or self.passvalue["conf"] is None:
            self.passvalue["conf"] = os.path.join("./lens data", "template.ini")

        # ------ Instantiate some more global variables (for dynamic updates) ------ #
        self.disable_wfe = True
        self.disable_wfe_color = ""

        # ------ Instantiate some more global variables (for running simulations and plotting) ------ #
        self.retval, self.retval_list, self.saving_groups = {}, [], []
        self.figure, self.figure_list_nwl, self.figure_list_wfe = None, [], []

        self.surface_zoom = None
        self.surface_number = None
        self.surface_scale = ""

    def init_window(self):
        """
        Initializes the main GUI window by parsing the configuration file and initializing the input data dimensions
        """

        # ------ Set up the configuration file parser ------ #
        self.config = configparser.ConfigParser()
        if "conf" in self.passvalue.keys() and self.passvalue["conf"] is not None:
            if not os.path.exists(self.passvalue["conf"]) or not os.path.isfile(
                self.passvalue["conf"]
            ):
                logger.error(
                    f'Input file {self.passvalue["conf"]} does not exist or is not a file. Quitting..'
                )
                sys.exit()
        else:
            logger.debug("Configuration file not found. Exiting..")
            sys.exit()

        # ------ Parse the configuration file ------ #
        self.config.read(self.passvalue["conf"])

        # ------- Initialize count of wavelengths, fields and optical surfaces ------#
        self.nrows_wl = (
            len(self.config["wavelengths"])
            if "wavelengths" in self.config.keys()
            else 1
        )
        self.nrows_field = (
            len(self.config["fields"]) if "fields" in self.config.keys() else 1
        )
        self.nrows_ld = len(
            [key for key in self.config.keys() if key.startswith("lens")]
        )

        # ------- Initialize keys of wavelengths, fields and surfaces ------#
        self.wl_keys = [f"w{k}" for k in range(1, self.nrows_wl + 1)]
        self.field_keys = [f"f{k}" for k in range(1, self.nrows_field + 1)]
        self.ld_keys = [f"S{k}" for k in range(1, self.nrows_ld + 1)]

        for key, item in self.config.items():
            if key.startswith("lens"):
                for subkey, subitem in item.items():
                    if subitem == "Zernike" and not self.config[key].getboolean(
                        "ignore"
                    ):
                        self.disable_wfe = False
        self.disable_wfe_color = "gray" if self.disable_wfe else "blue"

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

        default = item if item != "NaN" else None
        disabled = False if item != "NaN" else True

        if value in ["Save", "Ignore", "Stop"]:
            return Checkbox(
                text=value,
                default=default,
                key=key,
                size=(21, 2),
                disabled=disabled,
                enable_events=True,
            )
        elif value in ["Comment", "Radius", ""]:
            return InputText(
                default_text=default, key=key, size=size, disabled=disabled
            )
        elif key.startswith("aperture"):
            return self.aperture_tab(key=key, disabled=disabled)
        else:
            return InputCombo(
                default_value=default,
                values=value,
                key=key,
                size=(23, 2),
                disabled=disabled,
                enable_events=True,
            )

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
        config_key = "lens_{:02d}".format(row)
        aperture = None
        if config_key in self.config.keys():
            aperture = self.config[config_key].get("aperture", None)
            aperture = aperture if aperture != "" else None
        if aperture is not None:
            aperture = aperture.split(",")

        tab = []
        for k, (key, item) in enumerate(self.lens_data["aperture"].items()):
            key_item = key.replace(" ", "_") + f"_({row},{col})"
            config_item = "" if aperture is None else aperture[k]

            tab.append([Text(key, size=(20, 1))])
            tab.append(
                [
                    self.get_widget(
                        value=item,
                        key=key_item,
                        item=config_item,
                        size=(20, 1),
                    )
                ]
            )

        return tab

    def aperture_tab(self, key, disabled):
        """
        Given the row and column corresponding to the cell in the GUI lens data editor, returns the Column widget with
        the aperture parameters

        Parameters
        ----------
        key: str
            key to which the returned Column widget will be associated
        disabled: bool
            boolean to disable or enable events for the Button widget

        Returns
        -------
        out: Column
            the Column widget for the aperture

        """

        cell = re.findall("[0-9]+", key.partition("_")[-1])
        row, col = tuple(map(int, cell))

        button_symbol = self.symbol_disabled if disabled else self.triangle_right
        text_color = "gray" if disabled else "yellow"
        surface_tab_layout = Column(
            layout=[
                [
                    Button(
                        button_symbol,
                        enable_events=True,
                        disabled=disabled,
                        key=f"-OPEN TAB APERTURE-({row},{col})",
                        font=self.font_small,
                        size=(2, 1),
                    ),
                    Text(
                        "Aperture",
                        size=(20, 1),
                        text_color=text_color,
                        key=f"LD_Tab_Title_({row},{col})",
                    ),
                ],
                [
                    self.collapse_frame(
                        title="",
                        layout=[[Column(layout=self.fill_aperture_tab(row, col))]],
                        key=f"LD_Tab_({row},{col})",
                    )
                ],
            ],
            key=key,
        )

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

        headings = [
            "Par1",
            "Par2",
            "Par3",
            "Par4",
            "Par5",
            "Par6",
            "Par7",
            "Par8",
        ]
        if surface_type in ["INIT", "Standard"]:
            headings = ["", "", "", "", "", "", "", ""]
        elif surface_type == "Coordinate Break":
            headings = [
                "Xdecenter",
                "Ydecenter",
                "Xtilt",
                "Ytilt",
                "",
                "",
                "",
                "",
            ]
        elif surface_type == "Paraxial Lens":
            headings = ["Focal length", "", "", "", "", "", "", ""]
        elif surface_type == "ABCD":
            headings = ["Ax", "Bx", "Cx", "Dx", "Ay", "By", "Cy", "Dy"]
        elif surface_type == "Zernike":
            headings = [
                "Wavelength",
                "Ordering",
                "Normalization",
                "Radius of S.A.",
                "Origin",
                "",
                "",
                "",
            ]

        return headings

    def highlight_row(self, row, selected_row):
        """
        Highlights the elements in the currently selected row

        Parameters
        ----------
        selected_row
        row: int
            row corresponding to the optical surface in the GUI lens data editor

        Returns
        -------
        out: int
            the highlighted row index
        """
        if selected_row is not None:
            self.window[f"lenses_{selected_row:02d}"].Widget.config(relief=RELIEF_FLAT)

        self.window[f"lenses_{row:02d}"].Widget.config(relief=RELIEF_SUNKEN)

        return row

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
        par_headings = self.par_heading_rules(self.values[f"SurfaceType_({row},0)"])
        old_par_headings = [
            "Par1",
            "Par2",
            "Par3",
            "Par4",
            "Par5",
            "Par6",
            "Par7",
            "Par8",
        ]
        for head, new_head in zip(old_par_headings, par_headings):
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
        if surface_type == "INIT" and header.startswith(
            (
                "Radius",
                "Thickness",
                "Material",
                "Save",
                "Ignore",
                "Stop",
                "Par",
            )
        ):
            item = "NaN"

        elif surface_type == "Coordinate Break" and (
            header.startswith(("Radius", "Material", "aperture"))
            or header.startswith(("Par5", "Par6", "Par7", "Par8"))
        ):
            item = "NaN"

        elif surface_type == "Standard" and header.startswith("Par"):
            item = "NaN"

        elif surface_type == "Paraxial Lens" and (
            header.startswith(("Radius", "Material"))
            or header.startswith(
                ("Par2", "Par3", "Par4", "Par5", "Par6", "Par7", "Par8")
            )
        ):
            item = "NaN"

        elif surface_type == "ABCD" and header.startswith(("Radius", "Material")):
            item = "NaN"

        elif surface_type == "Zernike" and (
            header.startswith(("Radius", "Thickness", "Material", "aperture"))
            or header.startswith(("Par6", "Par7", "Par8"))
        ):
            item = "NaN"

        return item

    def chain_widgets(self, row, input_list, prefix, disabled_list=None):
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
        disabled_list: list[bool]
            from base method. Not used here

        Returns
        -------
        out: List[Text, List[Checkbox or Input or Column or Combo]]
            list of widgets to fill a GUI editor data row
        """
        row_widget = [Text(row, size=(6, 1), key=f"row idx {row}")]

        if prefix == "w":
            key = f"{prefix}{row}"
            item = self.config["wavelengths"].get(key, "")
            return list(
                itertools.chain(
                    row_widget,
                    [self.get_widget(value, key, item) for value in input_list],
                )
            )

        elif prefix == "f":
            key = f"{prefix}{row}"
            items = self.config["fields"].get(key, "0.0,0.0").split(",")
            keys = ["_".join([key, str(i)]) for i in range(len(items))]
            return list(
                itertools.chain(
                    row_widget,
                    [
                        self.get_widget(value, key, item)
                        for value, key, item in zip(input_list, keys, items)
                    ],
                )
            )

        elif prefix == "l":
            key = "lens_{:02d}".format(row)

            lens_dict = {}
            for c, name in enumerate(self.lens_data.keys()):
                name_key = f"{name}_({row},{c})"
                lens_dict[name_key] = None
                if key in self.config.keys() and name in self.config[key].keys():
                    if name in ["Save", "Ignore", "Stop"]:
                        lens_dict[name_key] = self.config[key].getboolean(name)
                    else:
                        lens_dict[name_key] = self.config[key][name]

                surface_type = lens_dict[f"SurfaceType_({row},0)"]
                lens_dict[name_key] = self.lens_data_rules(
                    surface_type=surface_type,
                    header=name_key,
                    item=lens_dict[name_key],
                )

            return list(
                itertools.chain(
                    row_widget,
                    [
                        self.get_widget(value, key, item)
                        for value, (key, item) in zip(input_list, lens_dict.items())
                    ],
                )
            )

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

        if column_key == "wavelengths":
            nrows = self.nrows_wl
            input_list = [""]
        elif column_key == "fields":
            nrows = self.nrows_field
            input_list = ["", ""]
        elif column_key == "lenses":
            nrows = self.nrows_ld
            input_list = [item for key, item in self.lens_data.items()]
        else:
            logger.error("Key error")

        nrows += 1

        if column_key == "lenses":
            new_row = [
                [
                    Frame(
                        "",
                        layout=[self.chain_widgets(nrows, input_list, prefix)],
                        key=f"{column_key}_{nrows:02d}",
                        relief=RELIEF_FLAT,
                    )
                ]
            ]
        else:
            new_row = [self.chain_widgets(nrows, input_list, prefix)]

        # Extend the Column layout
        self.window.extend_layout(self.window[column_key], new_row)
        self.window[column_key].update()

        if column_key == "lenses":
            self.config.add_section("lens_{:02d}".format(nrows))
            for c, head in enumerate(self.lens_data.keys()):
                self.window[f"{head}_({nrows},{c})"].bind("<Button-1>", "_LeftClick")

        return nrows

    def update_wfe_frame(self):
        """
        Checks if a Zernike surface is present in the lens data editor and whether it is ignored and
        updates the Wfe Frame accordingly, by enabling/disabling it and recalculates the Column scrollbar

        Returns
        -------
        out: None
            updates the Wfe Frame

        """
        disable_wfe = []
        for key, item in self.values.items():
            if item == "Zernike":
                row, col = re.findall("[0-9]+", key)
                if self.values[f"Ignore_({row},6)"]:
                    disable_wfe.append(True)
                else:
                    disable_wfe.append(False)

        self.disable_wfe = False if False in disable_wfe else True
        self.disable_wfe_color = "gray" if self.disable_wfe else "blue"

        self.window["-OPEN FRAME MC (wfe)-"].update(disabled=self.disable_wfe)
        self.window["-FRAME TITLE MC (wfe)-"].update(text_color=self.disable_wfe_color)

        if self.disable_wfe:
            self.window["-OPEN FRAME MC (wfe)-"].update(self.triangle_right)
            self.window["FRAME MC (wfe)"].update(visible=False)
            self.update_column_scrollbar(window=self.window, col_key="MC LAUNCHER COL")

        return

    def reset_simulation(self):
        """
        Clean up used memory, close matplotlib plots and reset variables before running new simulations

        Returns
        -------
        out: None
            Resets variables and matplotlib plots to free up memory

        """

        # Reset simulation variables
        del self.retval, self.figure
        self.retval, self.figure = {}, None
        self.retval_list.clear()
        self.figure_list_nwl.clear()
        self.figure_list_wfe.clear()
        # Clear Image elements
        for image_key in ["-IMAGE-", "-IMAGE (nwl)-", "-IMAGE (wfe)-"]:
            self.clear_image(self.window[image_key])
        # Close matplotlib plots
        plt.close("all")
        _ = gc.collect()
        # Reset progress bars
        _ = self.reset_progress_bar(self.window["progbar"])
        _ = self.reset_progress_bar(self.window["progbar (nwl)"])
        _ = self.reset_progress_bar(self.window["progbar (wfe)"])
        # Reset stoplights color
        for key in ["PLOT-STATE", "PLOT-STATE (nwl)", "PLOT-STATE (wfe)"]:
            self.window[key].update(text_color="red")
        return

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
        dictionary = {
            "general": {
                "project": self.values["project"],
                "version": self.values["version"],
                "grid_size": self.values["grid_size"],
                "zoom": self.values["zoom"],
                "lens_unit": self.values["lens_unit"],
                "Tambient": self.values["tambient"],
                "Pambient": self.values["pambient"],
            }
        }

        # ------- Get wavelengths data ------#
        key = "wavelengths"
        dictionary[key] = {}
        for k in range(1, self.nrows_wl + 1):
            if self.values[f"w{k}"] != "":
                dictionary[key][f"w{k}"] = self.values[f"w{k}"]

        # ------- Get fields data ------#
        key = "fields"
        dictionary[key] = {}
        for k in range(1, self.nrows_field + 1):
            fields = [
                self.values[f"f{k}_{c}"] for c in range(len(self.field_data.keys()))
            ]
            dictionary[key][f"f{k}"] = ",".join(map(str, fields))

        # ------- Get lens data editor data ------#
        for k in range(1, self.nrows_ld + 1):
            key = "lens_{:02d}".format(k)
            dictionary[key] = {}
            for c, head in enumerate(self.lens_data.keys()):
                section = dictionary[key]
                if head == "aperture":
                    section[head] = ",".join(
                        [
                            self.values[f'{name_key.replace(" ", "_")}_({k},{c})']
                            for name_key in self.lens_data["aperture"].keys()
                        ]
                    )
                    if section[head] == len(section[head]) * ",":
                        section[head] = ""
                else:
                    section[head] = self.values[f"{head}_({k},{c})"]
                    if section[head] == "Zernike":
                        section["zindex"] = self.config[key].get("zindex", "0")
                        section["z"] = self.config[key].get("z", "0")
                dictionary[key].update(section)

        if show:
            popup_scrolled(
                f"lens_data = {dictionary}",
                title="Copy your data from here",
                keep_on_top=True,
            )
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
            pass
        elif temporary:
            self.temporary_config = filename = os.path.join(
                os.path.dirname(self.passvalue["conf"]),
                "".join(["temp_", os.path.basename(self.passvalue["conf"])]),
            )
        else:
            filename = self.passvalue["conf"]

        with open(filename, "w") as cf:
            config.write(cf)
        return

    def draw_surface(
        self,
        retval_list,
        groups,
        figure_agg,
        image_key,
        surface_key,
        scale_key,
        zoom_key="",
        range_key=None,
    ):
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
        zoom_key: str
            key for the surface zoom factor
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
        plt.close("all")

        zoom = getfloat(self.values[zoom_key])
        if np.isnan(zoom):
            logger.warning("The input zoom value is not a scalar")
            zoom = 1

        if figure_agg is not None:
            # Reset figure canvas
            self.clear_image(self.window[image_key])
        # Get surface to plot
        key = int(self.values[surface_key][1:])
        # Get image scale
        ima_scale = self.values[scale_key].partition(" ")[0]
        if "nwl" in image_key or "wfe" in image_key:
            sim_range = self.values[range_key].split("-")
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
                    logger.error(
                        "Surface not present in POP output: it was either ignored or simply not saved"
                    )
                    break
                # Plot
                logger.debug(f"Plotting POP for group {group}")
                figure_list.append(
                    plot_surface(key=key, retval=ret, ima_scale=ima_scale, zoom=zoom)
                )
                # Get the index of the plotted figures
                idx.append(j)
                j += 1
            if "nwl" in image_key:
                self.window["-Slider (nwl)-"].update(range=(0, n_max - n_min - 1))
            elif "wfe" in image_key:
                self.window["-Slider (wfe)-"].update(range=(0, n_max - n_min - 1))
            return figure_list, idx
        else:
            ret = retval_list[0]
            # Check that surface is stored in POP output
            if key not in ret.keys():
                logger.error(
                    "Surface not present in POP output: it was either ignored or simply not saved"
                )
                return
            # Plot
            fig = plot_surface(key=key, retval=ret, ima_scale=ima_scale, zoom=zoom)
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
            logger.error("Plot first")
            return
        if figure_agg is not None:
            # Reset figure canvas
            self.clear_image(self.window[image_key])
        # Get the simulation index
        n = int(self.values[slider_key])
        # Draw the image
        figure_agg = self.draw_image(
            figure=figure_list[n], element=self.window[image_key]
        )
        # Update the 'MC LAUNCHER COL' Column scrollbar
        self.update_column_scrollbar(window=self.window, col_key="MC LAUNCHER COL")
        return figure_agg

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
            [
                Frame(
                    "General Setup",
                    layout=[
                        [Text("", size=(24, 1))],
                        [
                            Text("Project Name:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("project", ""),
                                tooltip="Insert project name",
                                key="project",
                                size=(80, 1),
                            ),
                        ],
                        [
                            Text("Comment:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("comment", ""),
                                tooltip="Insert comment",
                                key="comment",
                                size=(80, 1),
                            ),
                        ],
                        [
                            Text("Version:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("version", ""),
                                tooltip="Insert project version tag",
                                key="version",
                                size=(24, 1),
                            ),
                        ],
                        [
                            Text("Grid Size:", size=(24, 1)),
                            InputCombo(
                                values=["64", "128", "512", "1024"],
                                default_value=self.config["general"].getint(
                                    "grid_size", 512
                                ),
                                key="grid_size",
                                size=(24, 1),
                            ),
                        ],
                        [
                            Text("Zoom:", size=(24, 1)),
                            InputCombo(
                                values=["1", "2", "4", "8", "16"],
                                default_value=self.config["general"].getint("zoom", 4),
                                key="zoom",
                                size=(24, 1),
                            ),
                        ],
                        [
                            Text("Lens unit:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("lens_unit", ""),
                                key="lens_unit",
                                size=(24, 1),
                                disabled=True,
                            ),
                        ],
                        [
                            Text("Angles unit:", size=(24, 1)),
                            InputText(
                                "degrees",
                                size=(24, 1),
                                key="angle_units",
                                disabled=True,
                            ),
                        ],
                        [
                            Text("Wavelengths unit:", size=(24, 1)),
                            InputText(
                                "micrometers",
                                size=(24, 1),
                                key="lambda_units",
                                disabled=True,
                            ),
                        ],
                        [
                            Text("T ambient:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("Tambient", "20.0"),
                                tooltip="Insert ambient temperature",
                                key="tambient",
                                size=(24, 1),
                            ),
                        ],
                        [
                            Text("T unit:", size=(24, 1)),
                            InputText(
                                "(°C)",
                                key="T_unit",
                                size=(24, 1),
                                disabled=True,
                            ),
                        ],
                        [
                            Text("P ambient:", size=(24, 1)),
                            InputText(
                                self.config["general"].get("Pambient", "1.0"),
                                tooltip="Insert ambient pressure",
                                key="pambient",
                                size=(24, 1),
                            ),
                        ],
                        [
                            Text("P unit:", size=(24, 1)),
                            InputText(
                                "(atm)",
                                key="P_unit",
                                size=(24, 1),
                                disabled=True,
                            ),
                        ],
                        [Text("", size=(24, 1))],
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="GENERAL FRAME",
                    expand_x=True,
                )
            ],
            [
                Frame(
                    "Wavelength Setup",
                    layout=[
                        [Text("", size=(24, 1))],
                        list(
                            itertools.chain(
                                [
                                    Frame(
                                        "Wavelengths Actions",
                                        layout=[
                                            [
                                                Text(
                                                    "Add a wavelength: ",
                                                    size=(24, 1),
                                                ),
                                                Button(
                                                    tooltip="Click to add wavelength",
                                                    button_text="Add",
                                                    enable_events=True,
                                                    key="-ADD WAVELENGTH-",
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Paste wavelengths: ",
                                                    size=(24, 1),
                                                ),
                                                Button(
                                                    tooltip="Click to paste wavelengths",
                                                    button_text="Paste",
                                                    enable_events=True,
                                                    key="-PASTE WL-",
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Sort wavelengths: ",
                                                    size=(24, 1),
                                                ),
                                                Button(
                                                    tooltip="Click to sort wavelengths",
                                                    button_text="Sort",
                                                    enable_events=True,
                                                    key="-SORT WL-",
                                                ),
                                            ],
                                        ],
                                        font=self.font_titles,
                                        relief=RELIEF_SUNKEN,
                                        key="GENERAL ACTIONS FRAME",
                                    )
                                ],
                                [Text("", size=(15, 1))],
                                [
                                    Column(
                                        layout=list(
                                            itertools.chain(
                                                [self.add_heading(self.wl_data.keys())],
                                                [
                                                    self.chain_widgets(
                                                        r, [""], prefix="w"
                                                    )
                                                    for r in range(1, self.nrows_wl + 1)
                                                ],
                                            )
                                        ),
                                        key="wavelengths",
                                        scrollable=True,
                                        vertical_scroll_only=True,
                                        expand_y=True,
                                    )
                                ],
                            )
                        ),
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="WL FRAME",
                    expand_x=True,
                    expand_y=True,
                    element_justification="top",
                )
            ],
        ]
        # Define fields layout
        fields_layout = [
            [
                Frame(
                    "Fields Setup",
                    layout=[
                        [Text("", size=(24, 1))],
                        [
                            Column(
                                layout=list(
                                    itertools.chain(
                                        [self.add_heading(self.field_data.keys())],
                                        [
                                            self.chain_widgets(r, ["", ""], prefix="f")
                                            for r in range(1, self.nrows_field + 1)
                                        ],
                                    )
                                ),
                                scrollable=True,
                                vertical_scroll_only=True,
                                expand_x=True,
                                expand_y=True,
                                key="fields",
                            )
                        ],
                        [Text(" ")],
                        [
                            Frame(
                                "Fields Actions",
                                layout=[
                                    [
                                        Text("Add a field: ", size=(24, 1)),
                                        Button(
                                            tooltip="Click to add field row",
                                            button_text="Add Field",
                                            enable_events=True,
                                            key="-ADD FIELD-",
                                        ),
                                    ]
                                ],
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                                key="FIELDS ACTIONS FRAME",
                            )
                        ],
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="FIELDS FRAME",
                    expand_x=True,
                    expand_y=True,
                    element_justification="top",
                )
            ],
        ]
        # Define lens data layout
        lens_data_layout = [
            [
                Frame(
                    "Lens Data Setup",
                    layout=[
                        [Text("", size=(24, 1))],
                        [
                            Column(
                                layout=list(
                                    itertools.chain(
                                        [self.add_heading(self.lens_data.keys())],
                                        [[Text("")]],
                                        [
                                            [
                                                Frame(
                                                    "",
                                                    layout=[
                                                        self.chain_widgets(
                                                            r,
                                                            [
                                                                item
                                                                for key, item in self.lens_data.items()
                                                            ],
                                                            prefix="l",
                                                        )
                                                    ],
                                                    key=f"lenses_{r:02d}",
                                                    relief=RELIEF_FLAT,
                                                )
                                            ]
                                            for r in range(1, self.nrows_ld + 1)
                                        ],
                                    )
                                ),
                                scrollable=True,
                                expand_x=True,
                                expand_y=True,
                                key="lenses",
                            )
                        ],
                        [Text(" ")],
                        [
                            Frame(
                                "Lens Data Actions",
                                layout=[
                                    [
                                        Text("Add a surface: ", size=(24, 1)),
                                        Button(
                                            tooltip="Click to add surface row",
                                            button_text="Add Surface",
                                            enable_events=True,
                                            key="-ADD SURFACE-",
                                        ),
                                    ]
                                ],
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                                key="LENS DATA ACTIONS FRAME",
                            )
                        ],
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="FIELDS FRAME",
                    expand_x=True,
                    expand_y=True,
                    element_justification="top",
                )
            ],
        ]
        # Define launcher layout
        launcher_layout = [
            [
                Column(
                    layout=[
                        [
                            Frame(
                                "Select inputs",
                                layout=[
                                    list(
                                        itertools.chain(
                                            [
                                                Text(
                                                    "Select wavelength",
                                                    size=(12, 2),
                                                ),
                                                Listbox(
                                                    default_values=["w1"],
                                                    values=self.wl_keys,
                                                    size=(12, 4),
                                                    key="select wl",
                                                    enable_events=True,
                                                ),
                                            ],
                                            [Text("", size=(5, 2))],
                                            [
                                                Text(
                                                    "Select field",
                                                    size=(12, 2),
                                                ),
                                                Listbox(
                                                    default_values=["f1"],
                                                    values=self.field_keys,
                                                    size=(12, 4),
                                                    key="select field",
                                                    enable_events=True,
                                                ),
                                            ],
                                        )
                                    )
                                ],
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                                key="INPUTS FRAME",
                            )
                        ],
                        [Text("", size=(6, 1))],
                        list(
                            itertools.chain(
                                [
                                    Frame(
                                        "Run and Save",
                                        layout=[
                                            [Text("Run a diagnostic raytrace")],
                                            [
                                                Button(
                                                    tooltip="Launch raytrace",
                                                    button_text="Raytrace",
                                                    enable_events=True,
                                                    key="-RAYTRACE-",
                                                )
                                            ],
                                            [
                                                Column(
                                                    layout=[
                                                        [
                                                            Multiline(
                                                                key="raytrace log",
                                                                font=self.font_small,
                                                                autoscroll=True,
                                                                size=(90, 20),
                                                                pad=(
                                                                    0,
                                                                    (15, 0),
                                                                ),
                                                                disabled=False,
                                                            )
                                                        ]
                                                    ],
                                                    key="raytrace log col",
                                                )
                                            ],
                                            [
                                                Button(
                                                    tooltip="Save raytrace output",
                                                    button_text="Save raytrace",
                                                    enable_events=True,
                                                    key="-SAVE RAYTRACE-",
                                                )
                                            ],
                                            [Text("", size=(6, 1))],
                                            [
                                                Text(
                                                    "Run the POP: ",
                                                    size=(30, 1),
                                                ),
                                                Button(
                                                    tooltip="Launch POP",
                                                    button_text="POP",
                                                    enable_events=True,
                                                    key="-POP-",
                                                ),
                                                ProgressBar(
                                                    max_value=10,
                                                    orientation="horizontal",
                                                    size=(20, 8),
                                                    border_width=2,
                                                    key="progbar",
                                                    metadata=0,
                                                    bar_color=(
                                                        "Yellow",
                                                        "Gray",
                                                    ),
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Save the POP output: ",
                                                    size=(30, 1),
                                                ),
                                                Button(
                                                    tooltip="Save the POP output",
                                                    button_text="Save POP",
                                                    enable_events=True,
                                                    key="-SAVE POP-",
                                                ),
                                            ],
                                            [Text("", size=(6, 1))],
                                            [
                                                Text(
                                                    "Select surface zoom: ",
                                                    size=(30, 1),
                                                ),
                                                InputText(
                                                    tooltip="Surface zoom",
                                                    default_text="1",
                                                    key="Surface zoom",
                                                    enable_events=True,
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Select surface number: ",
                                                    size=(30, 1),
                                                ),
                                                InputCombo(
                                                    tooltip="Surface number",
                                                    values=self.ld_keys,
                                                    default_value=f"S{self.nrows_ld}",
                                                    key="S#",
                                                    enable_events=True,
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Select plot scale: ",
                                                    size=(30, 1),
                                                ),
                                                InputCombo(
                                                    tooltip="Color scale",
                                                    values=[
                                                        "linear scale",
                                                        "log scale",
                                                    ],
                                                    default_value="log scale",
                                                    key="Ima scale",
                                                    enable_events=True,
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Plot surface: ",
                                                    size=(30, 1),
                                                ),
                                                Button(
                                                    tooltip="Plot",
                                                    button_text="Plot",
                                                    enable_events=True,
                                                    key="-PLOT-",
                                                ),
                                                Text(
                                                    " " + self.symbol_state,
                                                    font=("Tahoma", 20),
                                                    text_color="red",
                                                    key="PLOT-STATE",
                                                ),
                                            ],
                                            [
                                                Text(
                                                    "Save the Plots",
                                                    size=(30, 1),
                                                ),
                                                Button(
                                                    tooltip="Save the plot",
                                                    button_text="Save Plot",
                                                    enable_events=True,
                                                    key="-SAVE FIG-",
                                                ),
                                            ],
                                        ],
                                        font=self.font_subtitles,
                                        relief=RELIEF_SUNKEN,
                                        expand_x=True,
                                        expand_y=True,
                                        key="-RUN AND SAVE FRAME-",
                                    )
                                ],
                                [
                                    Frame(
                                        "Display",
                                        layout=[
                                            [Text("", size=(6, 1))],
                                            [
                                                Button(
                                                    tooltip="Display plot",
                                                    button_text="Display plot",
                                                    enable_events=True,
                                                    key="-DISPLAY PLOT-",
                                                )
                                            ],
                                            [Image(key="-IMAGE-")],
                                        ],
                                        font=self.font_subtitles,
                                        relief=RELIEF_SUNKEN,
                                        expand_x=True,
                                        expand_y=True,
                                        key="IMAGE FRAME",
                                    )
                                ],
                            )
                        ),
                    ],
                    scrollable=True,
                    expand_x=True,
                    expand_y=True,
                    key="LAUNCHER COL",
                )
            ]
        ]
        # Define parallel launcher layout
        monte_carlo_layout = [
            [
                Column(
                    layout=[
                        [Text("", size=(6, 1))],
                        [
                            Button(
                                self.triangle_right,
                                enable_events=True,
                                disabled=False,
                                key="-OPEN FRAME MC (nwl)-",
                                font=self.font_small,
                                size=(2, 1),
                            ),
                            Text(
                                "MC Wavelengths",
                                size=(20, 1),
                                text_color="blue",
                                key="-FRAME TITLE MC (nwl)-",
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                            ),
                        ],
                        [
                            Column(
                                layout=[
                                    [
                                        self.collapse_frame(
                                            title="",
                                            layout=[
                                                [
                                                    Frame(
                                                        "Select inputs",
                                                        layout=[
                                                            [
                                                                Text(
                                                                    "Select field",
                                                                    size=(
                                                                        12,
                                                                        2,
                                                                    ),
                                                                ),
                                                                Listbox(
                                                                    default_values=[
                                                                        "f1"
                                                                    ],
                                                                    values=self.field_keys,
                                                                    size=(
                                                                        12,
                                                                        4,
                                                                    ),
                                                                    key="select field (nwl)",
                                                                    enable_events=True,
                                                                ),
                                                            ]
                                                        ],
                                                        font=self.font_subtitles,
                                                        relief=RELIEF_SUNKEN,
                                                        key="INPUTS FRAME (nwl)",
                                                    )
                                                ],
                                                list(
                                                    itertools.chain(
                                                        [
                                                            Frame(
                                                                "Run and Save",
                                                                layout=[
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Number of parallel jobs: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Number of jobs",
                                                                            default_text=2,
                                                                            key="NJOBS (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Run the multi-wl POP: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Launch POP",
                                                                            button_text="POP",
                                                                            enable_events=True,
                                                                            key="-POP (nwl)-",
                                                                        ),
                                                                        ProgressBar(
                                                                            max_value=10,
                                                                            orientation="horizontal",
                                                                            size=(
                                                                                20,
                                                                                8,
                                                                            ),
                                                                            border_width=2,
                                                                            key="progbar (nwl)",
                                                                            metadata=0,
                                                                            bar_color=(
                                                                                "Yellow",
                                                                                "Gray",
                                                                            ),
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Save the POP output: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Save the POP output",
                                                                            button_text="Save POP",
                                                                            enable_events=True,
                                                                            key="-SAVE POP (nwl)-",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Range to plot: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Select sim range to plot",
                                                                            default_text="0-1",
                                                                            key="RANGE (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select surface zoom: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Surface zoom",
                                                                            default_text="1",
                                                                            key="Surface zoom (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select surface number: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputCombo(
                                                                            tooltip="Surface number",
                                                                            values=self.ld_keys,
                                                                            default_value=f"S{self.nrows_ld}",
                                                                            key="S# (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select plot scale: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputCombo(
                                                                            tooltip="Color scale",
                                                                            values=[
                                                                                "linear scale",
                                                                                "log scale",
                                                                            ],
                                                                            default_value="log scale",
                                                                            key="Ima scale (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Plot surface: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Plot",
                                                                            button_text="Plot",
                                                                            enable_events=True,
                                                                            key="-PLOT (nwl)-",
                                                                        ),
                                                                        Text(
                                                                            " "
                                                                            + self.symbol_state,
                                                                            font=(
                                                                                "Tahoma",
                                                                                20,
                                                                            ),
                                                                            text_color="red",
                                                                            key="PLOT-STATE (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Figure prefix: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Figure prefix",
                                                                            default_text="Plot",
                                                                            key="Fig prefix (nwl)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Save the Plots",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Save the plots",
                                                                            button_text="Save Plot",
                                                                            enable_events=True,
                                                                            key="-SAVE FIG (nwl)-",
                                                                        ),
                                                                    ],
                                                                ],
                                                                font=self.font_subtitles,
                                                                relief=RELIEF_SUNKEN,
                                                                expand_x=True,
                                                                expand_y=True,
                                                                key="-RUN AND SAVE FRAME (nwl)-",
                                                            )
                                                        ],
                                                        [
                                                            Frame(
                                                                "Display",
                                                                layout=[
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                1,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Button(
                                                                            tooltip="Display plot",
                                                                            button_text="Display plot",
                                                                            enable_events=True,
                                                                            key="-DISPLAY PLOT (nwl)-",
                                                                        ),
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                2,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Slider(
                                                                            range=(
                                                                                0,
                                                                                10,
                                                                            ),
                                                                            orientation="horizontal",
                                                                            size=(
                                                                                40,
                                                                                15,
                                                                            ),
                                                                            default_value=0,
                                                                            key="-Slider (nwl)-",
                                                                            enable_events=True,
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Image(
                                                                            key="-IMAGE (nwl)-"
                                                                        )
                                                                    ],
                                                                ],
                                                                font=self.font_subtitles,
                                                                relief=RELIEF_SUNKEN,
                                                                expand_x=True,
                                                                expand_y=True,
                                                                key="IMAGE FRAME (nwl)",
                                                            )
                                                        ],
                                                    )
                                                ),
                                            ],
                                            key="FRAME MC (nwl)",
                                        )
                                    ]
                                ]
                            )
                        ],
                        [Text("", size=(6, 2))],
                        [
                            Button(
                                self.triangle_right,
                                enable_events=True,
                                disabled=self.disable_wfe,
                                key="-OPEN FRAME MC (wfe)-",
                                font=self.font_small,
                                size=(2, 1),
                            ),
                            Text(
                                "MC Wavefront error",
                                size=(20, 1),
                                text_color=self.disable_wfe_color,
                                key="-FRAME TITLE MC (wfe)-",
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                            ),
                        ],
                        [
                            Column(
                                layout=[
                                    [
                                        self.collapse_frame(
                                            title="",
                                            layout=[
                                                [
                                                    Frame(
                                                        "Select inputs",
                                                        layout=[
                                                            list(
                                                                itertools.chain(
                                                                    [
                                                                        Text(
                                                                            "Select wavelength",
                                                                            size=(
                                                                                12,
                                                                                2,
                                                                            ),
                                                                        ),
                                                                        Listbox(
                                                                            default_values=[
                                                                                "w1"
                                                                            ],
                                                                            values=self.wl_keys,
                                                                            size=(
                                                                                12,
                                                                                4,
                                                                            ),
                                                                            key="select wl (wfe)",
                                                                            enable_events=True,
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                5,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select field",
                                                                            size=(
                                                                                12,
                                                                                2,
                                                                            ),
                                                                        ),
                                                                        Listbox(
                                                                            default_values=[
                                                                                "f1"
                                                                            ],
                                                                            values=self.field_keys,
                                                                            size=(
                                                                                12,
                                                                                4,
                                                                            ),
                                                                            key="select field (wfe)",
                                                                            enable_events=True,
                                                                        ),
                                                                    ],
                                                                )
                                                            )
                                                        ],
                                                        key="INPUTS FRAME (wfe)",
                                                        font=self.font_subtitles,
                                                        relief=RELIEF_SUNKEN,
                                                    )
                                                ],
                                                list(
                                                    itertools.chain(
                                                        [
                                                            Frame(
                                                                "Run and Save",
                                                                layout=[
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Import Wavefront error table: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Import wfe table",
                                                                            button_text="Import wfe",
                                                                            enable_events=True,
                                                                            key="-IMPORT WFE-",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Unit of Zernike coefficients: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputCombo(
                                                                            tooltip="Zernike unit",
                                                                            values=[
                                                                                "meters",
                                                                                "millimeters",
                                                                                "micrometers",
                                                                                "nanometers",
                                                                            ],
                                                                            default_value="nanometers",
                                                                            key="ZUNIT (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Number of parallel jobs: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Number of jobs",
                                                                            default_text=2,
                                                                            key="NJOBS (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Index of Zernike surface: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Index of Zernike",
                                                                            default_text="",
                                                                            key="NSURF (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Run the POP for each wfe: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Launch POP",
                                                                            button_text="POP",
                                                                            enable_events=True,
                                                                            key="-POP (wfe)-",
                                                                        ),
                                                                        ProgressBar(
                                                                            max_value=10,
                                                                            orientation="horizontal",
                                                                            size=(
                                                                                20,
                                                                                8,
                                                                            ),
                                                                            border_width=2,
                                                                            key="progbar (wfe)",
                                                                            metadata=0,
                                                                            bar_color=(
                                                                                "Yellow",
                                                                                "Gray",
                                                                            ),
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Save the POP output: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Save the POP output",
                                                                            button_text="Save POP",
                                                                            enable_events=True,
                                                                            key="-SAVE POP (wfe)-",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                2,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Range to plot: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Select sim range to plot",
                                                                            default_text="0-1",
                                                                            key="RANGE (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select surface zoom: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Surface zoom",
                                                                            default_text="1",
                                                                            key="Surface zoom (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select surface number: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputCombo(
                                                                            tooltip="Surface number",
                                                                            values=self.ld_keys,
                                                                            default_value=f"S{self.nrows_ld}",
                                                                            key="S# (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Select plot scale: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputCombo(
                                                                            tooltip="Color scale",
                                                                            values=[
                                                                                "linear scale",
                                                                                "log scale",
                                                                            ],
                                                                            default_value="log scale",
                                                                            key="Ima scale (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Plot surface: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Plot",
                                                                            button_text="Plot",
                                                                            enable_events=True,
                                                                            key="-PLOT (wfe)-",
                                                                        ),
                                                                        Text(
                                                                            " "
                                                                            + self.symbol_state,
                                                                            font=(
                                                                                "Tahoma",
                                                                                20,
                                                                            ),
                                                                            text_color="red",
                                                                            key="PLOT-STATE (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Figure prefix: ",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        InputText(
                                                                            tooltip="Figure prefix",
                                                                            default_text="Plot",
                                                                            key="Fig prefix (wfe)",
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Text(
                                                                            "Save the Plots",
                                                                            size=(
                                                                                30,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Button(
                                                                            tooltip="Save the plots",
                                                                            button_text="Save Plot",
                                                                            enable_events=True,
                                                                            key="-SAVE FIG (wfe)-",
                                                                        ),
                                                                    ],
                                                                ],
                                                                font=self.font_subtitles,
                                                                relief=RELIEF_SUNKEN,
                                                                expand_x=True,
                                                                expand_y=True,
                                                                key="-RUN AND SAVE FRAME (wfe)-",
                                                            )
                                                        ],
                                                        [
                                                            Frame(
                                                                "Display",
                                                                layout=[
                                                                    [
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                6,
                                                                                1,
                                                                            ),
                                                                        )
                                                                    ],
                                                                    [
                                                                        Button(
                                                                            tooltip="Display plot",
                                                                            button_text="Display plot",
                                                                            enable_events=True,
                                                                            key="-DISPLAY PLOT (wfe)-",
                                                                        ),
                                                                        Text(
                                                                            "",
                                                                            size=(
                                                                                2,
                                                                                1,
                                                                            ),
                                                                        ),
                                                                        Slider(
                                                                            range=(
                                                                                0,
                                                                                10,
                                                                            ),
                                                                            orientation="horizontal",
                                                                            size=(
                                                                                40,
                                                                                15,
                                                                            ),
                                                                            default_value=0,
                                                                            key="-Slider (wfe)-",
                                                                            enable_events=True,
                                                                        ),
                                                                    ],
                                                                    [
                                                                        Image(
                                                                            key="-IMAGE (wfe)-"
                                                                        )
                                                                    ],
                                                                ],
                                                                font=self.font_subtitles,
                                                                relief=RELIEF_SUNKEN,
                                                                expand_x=True,
                                                                expand_y=True,
                                                                key="-IMAGE FRAME (wfe)-",
                                                            )
                                                        ],
                                                    )
                                                ),
                                            ],
                                            key="FRAME MC (wfe)",
                                        )
                                    ]
                                ]
                            )
                        ],
                    ],
                    scrollable=True,
                    expand_x=True,
                    expand_y=True,
                    key="MC LAUNCHER COL",
                )
            ]
        ]

        # Define info layout
        info_layout = [
            [
                Frame(
                    "GUI Info",
                    layout=[
                        [Text(f"Credits: {__author__}", key="-CREDITS-")],
                        [
                            Text(
                                f"{__pkg_name__.upper()} version: {__version__}",
                                key="-PAOS VERSION-",
                            )
                        ],
                        [Text("")],
                        [Text("Github Repo: ")],
                        [
                            Text(
                                f"{__url__}",
                                font=self.font_underlined,
                                text_color="blue",
                                enable_events=True,
                                key="-LINK-",
                            )
                        ],
                        [Text("")],
                        [
                            Text(
                                f"PySimpleGui version: {version}",
                                key="-GUI VERSION-",
                            )
                        ],
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="-INFO FRAME-",
                )
            ]
        ]

        # ------ Define GUI layout ------ #
        layout = [
            [Menu(self.menu_def, tearoff=True, key="-MENU-")],
            [
                Text(
                    "Configuration Tabs",
                    size=(38, 1),
                    justification="center",
                    relief=RELIEF_RIDGE,
                    key="-TEXT HEADING-",
                    enable_events=True,
                )
            ],
            [
                TabGroup(
                    [
                        [
                            Tab("General", general_layout, key="-GENERAL TAB-"),
                            Tab("Fields", fields_layout, key="-FIELDS TAB-"),
                            Tab(
                                "Lens Data",
                                lens_data_layout,
                                key="-LENS DATA TAB-",
                            ),
                            Tab(
                                "Launcher",
                                launcher_layout,
                                key="-LAUNCHER TAB-",
                            ),
                            Tab(
                                "Monte Carlo",
                                monte_carlo_layout,
                                key="-MC LAUNCHER TAB-",
                            ),
                            Tab("Info", info_layout, key="-INFO TAB-"),
                        ]
                    ],
                    key="-CONF TAB GROUP-",
                )
            ],
            [
                # Submit(tooltip="Click to submit (debug)", key="-SUBMIT-"),
                # Button(
                #     tooltip="Click to show dict",
                #     button_text="Show Dict",
                #     key="-SHOW DICT-",
                # ),
                # Button(
                #     tooltip="Click to copy dict to clipboard",
                #     button_text="Copy to clipboard",
                #     key="-TO CLIPBOARD-",
                # ),
                Button(
                    tooltip="Save to ini file",
                    button_text="Save",
                    key="-SAVE-",
                ),
                Button("Exit", key="-EXIT-"),
            ],
        ]

        # ------ Window creation ------ #
        self.window = Window(
            "PAOS GUI",
            layout,
            default_element_size=(12, 1),
            element_padding=(1, 1),
            return_keyboard_events=True,
            finalize=True,
            right_click_menu=self.right_click_menu_def,
            resizable=True,
            font=self.font,
            enable_close_attempted_event=True,
            element_justification="center",
            keep_on_top=False,
        )

        self.window["-CONF TAB GROUP-"].expand(True, True, True)

        # ------ Cursors definition ------ #
        self.window["-ADD SURFACE-"].set_cursor(cursor="hand1")
        # self.window["-SHOW DICT-"].set_cursor(cursor="target")
        self.window["-LINK-"].set_cursor(cursor="trek")
        self.window["-CREDITS-"].set_cursor(cursor="boat")
        self.window["-PAOS VERSION-"].set_cursor(cursor="coffee_mug")
        self.window["-GUI VERSION-"].set_cursor(cursor="clock")

        # ------- Bind method for Par headings ------#
        for r, (c, head) in itertools.product(
            range(1, self.nrows_ld + 1), enumerate(self.lens_data.keys())
        ):
            self.window[f"{head}_({r},{c})"].bind("<Button-1>", "_LeftClick")

        return

    def __call__(self):
        """
        Returns a rendering of the GUI window and handles the event loop.
        """

        # ------ Generate the main GUI window ------ #
        self.make_window()

        # ------ Instantiate local variables ------ #
        raytrace_log = ""
        fig_agg, fig_agg_nwl, fig_agg_wfe = None, None, None
        idx_nwl, idx_wfe = [], []

        # ------ Instantiate more local variables for dynamic interface ------ #
        aperture_tab_visible = False
        mc_wavelengths_frame_visible = False
        mc_wfe_frame_visible = False
        wfe_realizations_file = None
        selected_row = None

        pop = ""

        while True:  # Event Loop
            # ------- Read the current window ------#
            self.event, self.values = self.window.read(timeout=1000)
            if self.event == TIMEOUT_KEY:
                continue
            logger.trace(f"============ Event = {self.event} ==============")

            # ------- Save to temporary configuration file ------#
            self.to_ini(temporary=True)

            # ------- Find the window element with focus ------#
            elem = self.window.find_element_with_focus()
            elem_key = (
                elem.Key
                if (elem is not None and isinstance(elem.Key, (str, tuple)))
                else (0, 0)
            )

            # ------- Move with arrow keys within the editor tab and update the headings accordingly ------#
            if isinstance(elem_key, str) and elem_key.startswith(
                tuple([head for head in self.lens_data.keys()])
            ):
                # Move with arrow keys
                row = self.move_with_arrow_keys(
                    self.window,
                    self.event,
                    self.values,
                    elem_key,
                    self.nrows_ld,
                    len(self.lens_data.keys()),
                )
                # Update headings
                self.update_headings(row)

            # ------- Save (optional) and properly close the current window ------#
            if self.event in (
                WINDOW_CLOSED,
                WINDOW_CLOSE_ATTEMPTED_EVENT,
                "Exit",
                "-EXIT-",
            ):
                # Clear simulation outputs
                self.reset_simulation()
                # Close the current window
                self.close_window()
                break

            # ------- Update the headings according to mouse left click ------#
            elif isinstance(elem_key, str) and self.event == elem_key + "_LeftClick":
                cell = re.findall("[0-9]+", elem_key.partition("_")[-1])
                row, col = tuple(map(int, cell))
                self.update_headings(row)
                selected_row = self.highlight_row(row, selected_row)

            # # ------- Display a popup window with the output dictionary ------#
            # elif self.event == "-SHOW DICT-":
            #     # Show GUI window contents as a dict
            #     self.save_to_dict(show=True)

            # ------- Paste from the clipboard to the desired wavelength input cells ------#
            elif self.event == "-PASTE WL-":
                # Check if focus is on a wavelength input cell
                if not elem_key.startswith("w"):
                    logger.warning("Wavelength cell not selected. Skipping..")
                    continue
                # Get text from the clipboard
                text = self.get_clipboard_text()
                row0 = row = int(elem_key[1:])
                # Loop through text to insert the wavelengths one at a time
                for text_item in text:
                    self.window[f"w{row}"].update(text_item)
                    if self.nrows_wl <= row < row0 + len(text) - 1:
                        # Add the new wavelength and update wavelength count
                        self.nrows_wl = self.add_row("wavelengths")
                        self.wl_keys.append(f"w{self.nrows_wl}")
                        # Update 'select wl' Listbox widget in the launcher Tab
                        self.window["select wl"].update(self.wl_keys, set_to_index=0)
                    row += 1
                # Update the 'wavelengths' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="wavelengths")
                # Update 'select wl' Listbox widget in the launcher Tab
                self.window["select wl"].update(self.wl_keys, set_to_index=0)
                # Update 'select wl' Listbox widget in the Monte Carlo Tab
                self.window["select wl (wfe)"].update(self.wl_keys, set_to_index=0)

            # ------- Sort the wavelengths column in increasing order ------#
            elif self.event == "-SORT WL-":
                # Sort and display new order
                self.sort_column(window=self.window, values=self.values, col_key="w")

            # ------- Add a new wavelength input cell below those already present ------#
            elif self.event == "-ADD WAVELENGTH-":
                # Add the new wavelength and update wavelength count
                self.nrows_wl = self.add_row("wavelengths")
                self.wl_keys.append(f"w{self.nrows_wl}")
                # Update 'select wl' Listbox widget in the launcher Tab
                self.window["select wl"].update(self.wl_keys, set_to_index=0)
                # Update 'select wl' Listbox widget in the Monte Carlo Tab
                self.window["select wl (wfe)"].update(self.wl_keys, set_to_index=0)
                # Update the 'wavelengths' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="wavelengths")

            # ------- Add a new fields input row below those already present ------#
            elif self.event == "-ADD FIELD-":
                # Add the new field and update wavelength count
                self.nrows_field = self.add_row("fields")
                self.field_keys.append(f"f{self.nrows_field}")
                # Update 'select field' Listbox widget in the launcher Tab
                self.window["select field"].update(self.field_keys, set_to_index=0)
                # Update 'select field' Listbox widget in the Monte Carlo Tab
                self.window["select field (nwl)"].update(
                    self.field_keys, set_to_index=0
                )
                self.window["select field (wfe)"].update(
                    self.field_keys, set_to_index=0
                )
                # Update the 'fields' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="fields")

            # ------- Add a new optical surface in the lens data editor as a new row ------#
            elif self.event == "-ADD SURFACE-":
                # Add the new optical surface and update surface count
                self.nrows_ld = self.add_row("lenses")
                self.ld_keys.append(f"S{self.nrows_ld}")
                # Ignore newly added surface for precaution
                self.window[f"Ignore_({self.nrows_ld},6)"].update(True)
                # Update 'select surface' InputCombo widget in the Launcher and Monte Carlo Tabs
                for key in ["S#", "S# (nwl)", "S# (wfe)"]:
                    self.window[key].update(self.ld_keys[-1], values=self.ld_keys)
                # Update the 'lenses' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="lenses")

            # ------- Make the aperture tab visible/invisible by clicking on the triangle symbol ------#
            elif isinstance(self.event, str) and self.event.startswith(
                "-OPEN TAB APERTURE-"
            ):
                # Find current location in the lens data editor
                row, col = re.findall("[0-9]+", self.event)
                aperture_tab_key = f"LD_Tab_({row},{col})"
                # Make the aperture tab visible/invisible
                aperture_tab_visible = self.make_visible(
                    self.event, aperture_tab_visible, aperture_tab_key
                )
                # Update the 'Lens data' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="lenses")

            # ------- Assign/edit the surface type in the lens data editor ------#
            elif isinstance(self.event, str) and self.event.startswith("SurfaceType"):
                # Get the current row
                row, col = re.findall("[0-9]+", self.event)
                surface_type_key = f"SurfaceType_({row},0)"
                # Loop through all widgets in the current row
                for c, (key, value) in enumerate(self.lens_data.items()):
                    name_key = f"{key}_({row},{c})"
                    # Apply the pre-defined rules for the lens data editor to enable/disable a widget
                    item = self.lens_data_rules(
                        surface_type=self.values[surface_type_key],
                        header=name_key,
                    )
                    disabled = True if item == "NaN" else False
                    if key == "aperture":
                        item_column_key = f"-OPEN TAB APERTURE-({row},{c})"
                        # Update triangle symbol
                        self.window[item_column_key].update(
                            self.symbol_disabled if disabled else self.triangle_right
                        )
                        title_column_key = f"LD_Tab_Title_({row},8)"
                        text_color = "gray" if disabled else "yellow"
                        # Update aperture text color
                        self.window[title_column_key].update(text_color=text_color)
                    else:
                        item_column_key = f"{key}_({row},{c})"
                    # Enable/disable the row widgets
                    self.window[item_column_key].update(disabled=disabled)

                # Only if the selected surface type is Zernike...
                if self.values[surface_type_key] == "Zernike":
                    # Display popup to select action
                    action = popup_ok_cancel(
                        "Insert/Edit Zernike coefficients", keep_on_top=True
                    )
                    if action == "OK":
                        key = "lens_{:02d}".format(int(row))
                        # Launch the Zernike GUI editor
                        zernike = ZernikeGui(
                            config=self.config,
                            values=self.values,
                            row=row,
                            key=key,
                        )()
                        if key in self.config.keys():
                            # Update the zernike values in the config object
                            self.config[key].update(zernike)
                        else:
                            # Create ex-novo the zernike values in the config object
                            for subkey, subitem in zernike.items():
                                self.config.set(key, subkey, subitem)
                        # Update the zernike ordering (relevant only if previously not indicated)
                        col = list(self.lens_data.keys()).index("Par2")
                        self.window[f"Par2_({row},{col})"].update(zernike["ordering"])
                # Enable/Disable the wfe frame
                self.update_wfe_frame()

            # ------- Enable/Disable the wfe frame ------#
            elif isinstance(self.event, str) and self.event.startswith("Ignore"):
                self.update_wfe_frame()

            # ------- Update the stoplight color when the user changes the input ------#
            elif self.event in ["Surface zoom", "S#", "Ima scale"]:
                if np.logical_or.reduce(
                    (
                        self.values["Surface zoom"] != self.surface_zoom,
                        self.values["S#"] != self.surface_number,
                        self.values["Ima scale"] != self.surface_scale,
                    )
                ):
                    # Update stoplight color
                    self.window["PLOT-STATE"].update(text_color="red")
                    # Reset previous outputs
                    self.figure = None
                    # Reset figure canvas
                    self.clear_image(self.window["-IMAGE-"])

            # ------- Update 'Select wavelength' or 'Select field' Listbox widget in the Launcher tab ------#
            elif self.event in ["select wl", "select field"]:
                # Update stoplight color
                self.window["PLOT-STATE"].update(text_color="red")
                # Reset previous outputs
                del self.retval, self.figure
                self.retval, self.figure = {}, None
                self.retval_list.clear()
                # Reset figure canvas
                self.clear_image(self.window["-IMAGE-"])
                if self.event == "select field":
                    # Update the raytrace log Column
                    raytrace_log = ""
                    self.window["raytrace log"].update(raytrace_log)
                # Reset progress bar
                _ = self.reset_progress_bar(self.window["progbar"])
                _ = gc.collect()

            # ------- Update 'Select field' Listbox widget in MC Wavelengths frame ------#
            elif self.event == "select field (nwl)":
                # Update stoplight color
                self.window["PLOT-STATE (nwl)"].update(text_color="red")
                # Reset POP simulation output
                self.retval_list.clear()
                # Reset figure
                self.figure_list_nwl.clear()
                # Reset figure canvas
                self.clear_image(self.window["-IMAGE (nwl)-"])
                # Reset progress bar
                _ = self.reset_progress_bar(self.window["progbar (nwl)"])
                _ = gc.collect()

            # ------- Update 'Select wavelength' or 'Select field' Listbox widget in MC Wavefront error frame ------#
            elif self.event in ["select wl (wfe)", "select field (wfe)"]:
                # Update stoplight color
                self.window["PLOT-STATE (wfe)"].update(text_color="red")
                # Reset POP simulation output
                self.retval_list.clear()
                # Reset figures
                self.figure_list_wfe.clear()
                # Reset figure canvas
                self.clear_image(self.window["-IMAGE (wfe)-"])
                # Reset progress bar
                _ = self.reset_progress_bar(self.window["progbar (wfe)"])
                _ = gc.collect()

            # ------- Make the 'MC Wavelengths' frame visible/invisible by clicking on the triangle symbol ------#
            elif self.event == "-OPEN FRAME MC (nwl)-":
                # Make the 'MC Wavelengths' frame visible/invisible
                mc_wavelengths_frame_visible = self.make_visible(
                    self.event, mc_wavelengths_frame_visible, "FRAME MC (nwl)"
                )
                # Update the 'MC LAUNCHER COL' Column scrollbar
                self.update_column_scrollbar(
                    window=self.window, col_key="MC LAUNCHER COL"
                )

            # ------- Make the 'MC Wavefront error' frame visible/invisible by clicking on the triangle symbol ------#
            elif self.event == "-OPEN FRAME MC (wfe)-":
                # Make the 'MC Wavefront error' frame visible/invisible
                mc_wfe_frame_visible = self.make_visible(
                    self.event, mc_wfe_frame_visible, "FRAME MC (wfe)"
                )
                # Update the 'MC LAUNCHER COL' Column scrollbar
                self.update_column_scrollbar(
                    window=self.window, col_key="MC LAUNCHER COL"
                )

            # ------- Run a diagnostic raytrace and display the output in a Column widget ------#
            elif self.event == "-RAYTRACE-":
                # Get the wavelength and the field indexes from the respective Listbox widgets
                (n_wl,) = self.window["select wl"].GetIndexes()
                (n_field,) = self.window["select field"].GetIndexes()
                # Parse the temporary configuration file
                (
                    pup_diameter,
                    parameters,
                    wavelengths,
                    fields,
                    opt_chains,
                ) = parse_config(self.temporary_config)
                wavelength, field, opt_chain = (
                    wavelengths[n_wl],
                    fields[n_field],
                    opt_chains[n_wl],
                )
                # Run the raytrace
                raytrace_log = raytrace(field, opt_chain)
                # Update the raytrace log Column
                self.window["raytrace log"].update("\n".join(raytrace_log))
                # For later saving
                self.saving_groups = [wavelength]

            # ------- Run the POP ------#
            elif self.event == "-POP-":
                if self.values[self.values["select wl"][0]] == "":
                    logger.error(f"Invalid wavelength. Continuing..")
                    continue
                self.reset_simulation()
                progbar = self.window["progbar"]
                # Get the wavelength and the field indexes from the respective Listbox widgets
                (n_wl,) = self.window["select wl"].GetIndexes()
                (n_field,) = self.window["select field"].GetIndexes()
                # Parse the temporary configuration file
                (
                    pup_diameter,
                    parameters,
                    wavelengths,
                    fields,
                    opt_chains,
                ) = parse_config(self.temporary_config)
                wavelength, field, opt_chain = (
                    wavelengths[n_wl],
                    fields[n_field],
                    opt_chains[n_wl],
                )
                # Run the POP
                self.retval = run(
                    pup_diameter,
                    1.0e-6 * wavelength,
                    parameters["grid_size"],
                    parameters["zoom"],
                    field,
                    opt_chain,
                )
                # For later saving
                self.saving_groups = [wavelength]
                self.retval_list = [self.retval]
                # For later plotting
                pop = "simple"
                # Update progress bar
                progbar.metadata = progbar.Size[0]
                progbar.update_bar(progbar.metadata)

            # ------- Run the POP (nwl) ------#
            elif self.event == "-POP (nwl)-":
                # Clean up the GUI before running the POP
                self.reset_simulation()
                progbar_nwl = self.window["progbar (nwl)"]
                # Get the field index from the Listbox widget
                (n_field,) = self.window["select field (nwl)"].GetIndexes()
                # Get the number of parallel jobs
                n_jobs = int(self.values["NJOBS (nwl)"])
                # Parse the temporary configuration file
                (
                    pup_diameter,
                    parameters,
                    wavelengths,
                    fields,
                    opt_chains,
                ) = parse_config(self.temporary_config)
                field = fields[n_field]
                # Run the POP
                start_time = time.time()
                logger.info("Start POP in parallel...")
                for i in range(0, len(wavelengths), n_jobs):
                    wl_batch = wavelengths[i : i + n_jobs]
                    opt_batch = opt_chains[i : i + n_jobs]
                    self.retval_list.append(
                        Parallel(n_jobs=n_jobs)(
                            delayed(run)(
                                pup_diameter,
                                1.0e-6 * wavelength,
                                parameters["grid_size"],
                                parameters["zoom"],
                                field,
                                opt_chain,
                            )
                            for wavelength, opt_chain in tqdm(zip(wl_batch, opt_batch))
                        )
                    )
                    # Update progress bar
                    progress = np.ceil(
                        progbar_nwl.Size[0] * len(wl_batch) / len(wavelengths)
                    )
                    progbar_nwl.metadata += progress
                    progbar_nwl.update_bar(progbar_nwl.metadata)
                logger.info(
                    "Parallel POP completed in {:6.1f}s".format(
                        time.time() - start_time
                    )
                )
                # For later saving
                self.saving_groups = wavelengths
                self.retval_list = list(itertools.chain.from_iterable(self.retval_list))
                # For later plotting
                self.window["RANGE (nwl)"].update(
                    value="-".join(["0", str(len(self.retval_list))])
                )
                pop = "nwl"

            # ------- Select wfe table to import ------#
            elif self.event == "-IMPORT WFE-":
                wfe_realizations_file = popup_get_file(
                    "Choose wavefront error (CSV) file", keep_on_top=True
                )
                if wfe_realizations_file is None:
                    logger.warning("Pressed Cancel. Continuing...")
                    continue

            # ------- Run the POP (wfe) ------#
            elif self.event == "-POP (wfe)-":
                # Clean up the GUI before running the POP
                self.reset_simulation()
                progbar_wfe = self.window["progbar (wfe)"]
                # Get the Zernike surface index
                surf = self.values["NSURF (wfe)"]
                if surf == "":
                    logger.warning(
                        "The indicated surface index is not valid. Continuing..."
                    )
                    continue
                elif self.values[f"SurfaceType_({int(surf)},0)"] != "Zernike":
                    logger.warning(
                        "The indicated surface index does not belong to a Zernike surface. Continuing..."
                    )
                    continue
                elif self.values[f"Ignore_({int(surf)},6)"]:
                    logger.warning(
                        "Zernike surface is currently ignored. Continuing..."
                    )
                    continue
                elif wfe_realizations_file is None:
                    logger.error("Import Wavefront error table first")
                    continue
                # Read the wfe table
                wfe = ascii.read(wfe_realizations_file)
                wave = 1.0
                if self.values["ZUNIT (wfe)"] == "meters":
                    pass
                elif self.values["ZUNIT (wfe)"] == "millimeters":
                    wave = 1.0e-3
                elif self.values["ZUNIT (wfe)"] == "micrometers":
                    wave = 1.0e-6
                elif self.values["ZUNIT (wfe)"] == "nanometers":
                    wave = 1.0e-9
                # Get the number of wfe realizations
                sims = len(wfe.columns) - 3
                # Get the wavelength and the field indexes from the respective Listbox widgets
                (n_wl,) = self.window["select wl (wfe)"].GetIndexes()
                (n_field,) = self.window["select field (wfe)"].GetIndexes()
                # Get the number of parallel jobs
                n_jobs = int(self.values["NJOBS (wfe)"])
                # Parse the temporary configuration file
                (
                    pup_diameter,
                    parameters,
                    wavelengths,
                    fields,
                    opt_chains,
                ) = parse_config(self.temporary_config)
                wavelength, field, opt_chain = (
                    wavelengths[n_wl],
                    fields[n_field],
                    opt_chains[n_wl],
                )
                opt = []
                for k in range(sims):
                    temp = copy.deepcopy(opt_chain)
                    ck = wfe["col%i" % (k + 4)].data * wave
                    temp[int(surf)]["Z"] = np.append(np.zeros(3), ck)
                    opt.append(temp)
                # Run the POP
                start_time = time.time()
                logger.info("Start POP in parallel...")
                for i in range(0, sims, n_jobs):
                    opt_batch = opt[i : i + n_jobs]
                    self.retval_list.append(
                        Parallel(n_jobs=n_jobs)(
                            delayed(run)(
                                pup_diameter,
                                1.0e-6 * wavelength,
                                parameters["grid_size"],
                                parameters["zoom"],
                                field,
                                o_chain,
                            )
                            for o_chain in tqdm(opt_batch)
                        )
                    )
                    # Update progress bar
                    progress = np.ceil(progbar_wfe.Size[0] * len(opt_batch) / len(opt))
                    progbar_wfe.metadata += progress
                    progbar_wfe.update_bar(progbar_wfe.metadata)
                logger.info(
                    "Parallel POP completed in {:6.1f}s".format(
                        time.time() - start_time
                    )
                )
                # For later saving
                self.saving_groups = list(range(sims))
                self.retval_list = list(itertools.chain.from_iterable(self.retval_list))
                # For later plotting
                self.window["RANGE (wfe)"].update(
                    value="-".join(["0", str(len(self.retval_list))])
                )
                # For later plotting
                pop = "wfe"

            # ------- Save the output of the diagnostic raytrace ------#
            elif self.event == "-SAVE RAYTRACE-":
                # Save the raytrace output
                self.to_txt(text_list=raytrace_log)

            # ------- Save the output of the POP ------#
            elif self.event == "-SAVE POP-":
                if pop != "simple" or not self.retval_list:
                    logger.error("Run POP first")
                    continue
                # Save the POP output
                self.to_hdf5(self.retval_list, self.saving_groups)

            # ------- Save the output of the POP (nwl) ------#
            elif self.event == "-SAVE POP (nwl)-":
                if pop != "nwl" or not self.retval_list:
                    logger.error("Run POP (nwl) first")
                    continue
                # Save the POP output
                self.to_hdf5(self.retval_list, self.saving_groups)

            # ------- Save the output of the POP (wfe) ------#
            elif self.event == "-SAVE POP (wfe)-":
                if pop != "wfe" or not self.retval_list:
                    logger.error("Run POP (wfe) first")
                    continue
                # Save the POP output
                self.to_hdf5(self.retval_list, self.saving_groups)

            # ------- Plot at the given optical surface ------#
            elif self.event == "-PLOT-":
                if pop != "simple" or not self.retval_list:
                    logger.error("Run POP first")
                    continue
                self.figure = self.draw_surface(
                    retval_list=self.retval_list,
                    groups=self.saving_groups,
                    figure_agg=fig_agg,
                    image_key="-IMAGE-",
                    surface_key="S#",
                    scale_key="Ima scale",
                    zoom_key="Surface zoom",
                )
                # Update stoplight color
                if self.figure is not None:
                    self.window["PLOT-STATE"].update(text_color="green")

                # Save the current values
                self.surface_zoom = self.values["Surface zoom"]
                self.surface_number = self.values["S#"]
                self.surface_scale = self.values["Ima scale"]

            elif self.event == "-PLOT (nwl)-":
                if pop != "nwl" or not self.retval_list:
                    logger.error("Run POP (nwl) first")
                    continue
                self.figure_list_nwl, idx_nwl = self.draw_surface(
                    retval_list=self.retval_list,
                    groups=self.saving_groups,
                    figure_agg=fig_agg_nwl,
                    image_key="-IMAGE (nwl)-",
                    surface_key="S# (nwl)",
                    scale_key="Ima scale (nwl)",
                    zoom_key="Surface zoom (nwl)",
                    range_key="RANGE (nwl)",
                )
                # Update stoplight color
                if self.figure_list_nwl:
                    self.window["PLOT-STATE (nwl)"].update(text_color="green")

            elif self.event == "-PLOT (wfe)-":
                if pop != "wfe" or not self.retval_list:
                    logger.error("Run POP (wfe) first")
                    continue
                self.figure_list_wfe, idx_wfe = self.draw_surface(
                    retval_list=self.retval_list,
                    groups=self.saving_groups,
                    figure_agg=fig_agg_wfe,
                    image_key="-IMAGE (wfe)-",
                    surface_key="S# (wfe)",
                    scale_key="Ima scale (wfe)",
                    zoom_key="Surface zoom (wfe)",
                    range_key="RANGE (wfe)",
                )
                # Update stoplight color
                if self.figure_list_wfe:
                    self.window["PLOT-STATE (wfe)"].update(text_color="green")

            elif self.event == "-DISPLAY PLOT-":
                # Draw the figure canvas
                fig_agg = self.draw_image(
                    figure=self.figure, element=self.window["-IMAGE-"]
                )
                # Update the 'LAUNCHER COL' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="LAUNCHER COL")

            # ------- Display the plot for a given wavelength (MC) ------#
            elif self.event in ["-DISPLAY PLOT (nwl)-", "-Slider (nwl)-"]:
                # Display the plot for a given wavelength
                self.display_plot_slide(
                    self.figure_list_nwl,
                    fig_agg_nwl,
                    "-IMAGE (nwl)-",
                    "-Slider (nwl)-",
                )
                # Update the 'MC LAUNCHER COL' Column scrollbar
                self.update_column_scrollbar(
                    window=self.window, col_key="MC LAUNCHER COL"
                )

            # ------- Display the plot for a given wfe realization (MC) ------#
            elif self.event in ["-DISPLAY PLOT (wfe)-", "-Slider (wfe)-"]:
                # Display the plot for a given wfe realization
                self.display_plot_slide(
                    self.figure_list_wfe,
                    fig_agg_wfe,
                    "-IMAGE (wfe)-",
                    "-Slider (wfe)-",
                )
                # Update the 'MC LAUNCHER COL' Column scrollbar
                self.update_column_scrollbar(
                    window=self.window, col_key="MC LAUNCHER COL"
                )

            # ------- Save the Plot ------#
            elif self.event == "-SAVE FIG-":
                # Save figure
                self.save_figure(figure=self.figure)

            # ------- Save the Plot (nwl) ------#
            elif self.event == "-SAVE FIG (nwl)-":
                if not self.figure_list_nwl:
                    logger.error("Create plot first")
                    continue
                # Get the folder to save to
                folder = popup_get_folder("Choose folder to save to", keep_on_top=True)
                if folder is None:
                    logger.warning("Pressed Cancel. Continuing...")
                    continue
                for wl, figure in zip(
                    np.array(self.saving_groups)[idx_nwl],
                    np.array(self.figure_list_nwl),
                ):
                    filename = os.path.join(
                        folder,
                        f'{self.values["Fig prefix (nwl)"]}_{self.values["S# (nwl)"]}_'
                        f'{self.values["select field (nwl)"][0]}_wl{wl}micron.png',
                    )
                    # Save the plot to the specified .png or .jpg file
                    self.save_figure(figure, filename)

            # ------- Save the Plot (wfe) ------#
            elif self.event == "-SAVE FIG (wfe)-":
                if not self.figure_list_wfe:
                    logger.error("Create plot first")
                    continue
                # Get the folder to save to
                folder = popup_get_folder("Choose folder to save to", keep_on_top=True)
                if folder is None:
                    logger.warning("Pressed Cancel. Continuing...")
                    continue
                for n, figure in zip(
                    np.array(self.saving_groups)[idx_wfe],
                    np.array(self.figure_list_wfe),
                ):
                    filename = os.path.join(
                        folder,
                        f'{self.values["Fig prefix (wfe)"]}_{self.values["S# (wfe)"]}_'
                        f'{self.values["select field (wfe)"][0]}_N{n}.png',
                    )
                    # Save the plot to the specified .png or .jpg file
                    self.save_figure(figure, filename)

            # # ------- Display a popup window with the GUI values given as a flat dictionary ------#
            # elif self.event == "-SUBMIT-":
            #     popup(
            #         f"PAOS GUI v{__version__}",
            #         f'You clicked on the "{self.event}" button',
            #         f"The values are {self.values}",
            #         keep_on_top=True,
            #     )

            # # ------- Copy the relevant data from the GUI to the local clipboard ------#
            # elif self.event == "-TO CLIPBOARD-":
            #     self.copy_to_clipboard(
            #         dictionary=self.save_to_dict(show=False)
            #     )

            # ------- Display a Open File popup window with text entry field and browse button ------#
            elif self.event == "Open":
                # Get the new configuration file path
                filename = popup_get_file(
                    "Choose configuration (INI) file", keep_on_top=True
                )
                if filename is None:
                    logger.warning("Pressed Cancel. Continuing...")
                    continue
                self.passvalue["conf"] = filename
                # Close the current window
                self.close_window()
                # Relaunch the GUI for the new configuration file
                PaosGui(passvalue=self.passvalue)()

            # ------- Display a Save As popup window with text entry field and browse button ------#
            elif self.event in ["Save", "-SAVE-", "Save As"]:
                # Get the file path to save to
                filename = popup_get_file(
                    "Choose file (INI) to save to",
                    save_as=True,
                    keep_on_top=True,
                )
                if filename is None:
                    logger.warning("Pressed Cancel. Continuing...")
                    continue
                if not filename.endswith((".INI", ".ini")):
                    logger.debug("Saving file format not provided. Defaulting to .ini")
                    filename = "".join([filename, ".ini"])
                # Save as a new configuration file
                self.to_ini(filename=filename)

            # ------- Display a window to set the global PySimpleGUI settings (e.g. the color theme) ------#
            elif self.event == "Global Settings":
                main_global_pysimplegui_settings()

            # ------- Display a popup with the PySimpleGUI version ------#
            elif self.event == "Version":
                popup_scrolled(get_versions(), keep_on_top=True)

            # ------- Display url using the default browser ------#
            elif self.event == "-LINK-":
                openwb(self.window["-LINK-"].DisplayText)

            # ------- Display a popup window with the ``PAOS`` GUI info ------#
            elif self.event == "About":
                popup(f"PAOS GUI v{__version__}")

        # Exit the ``PAOS`` GUI for good
        sys.exit()
