import itertools
import re
import sys

from PySimpleGUI import Button
from PySimpleGUI import Column
from PySimpleGUI import Frame
from PySimpleGUI import popup
from PySimpleGUI import RELIEF_SUNKEN
from PySimpleGUI import Submit
from PySimpleGUI import Text
from PySimpleGUI import TIMEOUT_KEY
from PySimpleGUI import Window
from PySimpleGUI import WINDOW_CLOSE_ATTEMPTED_EVENT
from PySimpleGUI import WINDOW_CLOSED

from paos import logger
from paos import Zernike
from paos.gui.simpleGui import SimpleGui


class ZernikeGui(SimpleGui):
    """
    Generates the Zernike editor for the main ``PAOS`` GUI as a secondary GUI window

    Parameters
    ----------
    config: :class:`~configparser.ConfigParser` object
        the main GUI window parsed configuration file
    values: dict
        the main GUI window dict of values (returned when the Window element is read)
    row: int
        the Zernike surface row index in the lens data editor
    key: str
        the Zernike surface key in the configuration file

    """

    def __init__(self, config, values, row, key):
        super().__init__()

        self.config = config
        self.values = values
        self.row = row
        self.key = key

        # ------ Instantiate global variables ------ #
        self.window = None
        self.zernike = {}
        self.ordering = None
        self.par = ["", "", "", "", ""]
        self.names = ["Par1", "Par2", "Par3", "Par4", "Par5"]
        self.headings = ["Zindex", "Z", "m", "n"]
        self.disabled_cols = [True, False, True, True]
        self.max_rows = None

    def add_row(self, row, dictionary, ordering):
        """

        Parameters
        ----------
        row: int
            the last row index in the Zernike tab
        dictionary: dict
            the dictionary with the Zindex and Z coefficients to update with the new Zernike table row
        ordering: str
            the Zernike coefficients ordering

        Returns
        -------
        out: tuple(int, tuple(int, int))
            Adds a row in the Zernike tab and returns the updated number of rows and the azimuthal number, m,
            and radial number, n for the Zernike coefficients

        """
        row += 1

        # Update the azimuthal and radial number for the Zernike coefficients
        m, n = Zernike.j2mn(N=row, ordering=ordering)
        dictionary["zindex"].append(str(row))
        dictionary["z"].append("0.0")

        # Define the input list to fill the new table row with
        input_list = [str(row - 1), "0.0", m[row - 1], n[row - 1]]

        # Extend the Column layout
        self.window.extend_layout(
            self.window["zernike"],
            [
                self.chain_widgets(
                    row=row,
                    input_list=input_list,
                    prefix="z",
                    disabled_list=self.disabled_cols,
                )
            ],
        )
        # Update the GUI Zernike tab
        self.window["zernike"].update()

        return row, (m, n)

    def make_window(self):
        """
        Generates the Zernike GUI window (secondary window to the main ``PAOS`` GUI window).
        The layout is composed of only one Tab, with four headers: 'Zindex', 'Z', 'm', 'n'.
        'Zindex' contains the index j for each Zernike coefficient (starting from 0), 'Z' contains the Zernike
        coefficients, 'm' contains the azimuthal number and 'n' the radial number for the Zernike coefficients

        Returns
        -------
        out: None
            Generates the Zernike GUI window
        """

        # Get the Zindex and Z coefficients from the parsed configuration file
        if self.key in self.config.keys() and {"zindex", "z"}.issubset(
            self.config[self.key].keys()
        ):
            zindex, z = (
                self.config[self.key]["zindex"],
                self.config[self.key]["z"],
            )
            self.zernike["zindex"] = zindex.split(",") if zindex != "" else ["0"]
            self.zernike["z"] = z.split(",") if z != "" else ["0"]
        else:
            self.zernike["zindex"] = ["0"]
            self.zernike["z"] = ["0"]
        self.max_rows = len(self.zernike["zindex"])
        if len(self.zernike["z"]) != self.max_rows:
            logger.critical(
                "Input zernike index and zernike coefficients differ in length. Quitting..."
            )
            sys.exit()

        # Get the Zernike parameters from the main GUI window (wavelength, ordering, normalization, radius of support
        # aperture of the polynomials and origin, which can be x (counterclockwise positive from x-axis) or y
        # (clockwise positive from y-axis)
        for c, head in enumerate(self.names):
            par_key = "{}_({},{})".format(head, self.row, c + 9)
            if par_key in self.values.keys() and self.values[par_key] != "":
                self.par[c] = self.values[par_key]
        wavelength, self.ordering, normalization, radius, origin = self.par
        if self.ordering == "":
            logger.debug(
                "Zernike ordering is not defined. Defaulting to ordering=standard."
            )
            self.ordering = "standard"
        assert self.ordering in [
            "ansi",
            "standard",
            "noll",
            "fringe",
        ], f"ordering {self.ordering} not supported"

        # ------ Instantiate the azimuthal and radial Zernike order ------ #
        m, n = Zernike.j2mn(N=self.max_rows, ordering=self.ordering)

        # ------ Define the Zernike tab layout ------ #
        layout = [
            [
                Frame(
                    "Parameters",
                    layout=[
                        list(
                            itertools.chain(
                                [
                                    Text(
                                        "Wavelength: {}".format(wavelength),
                                        key="wavelength",
                                    )
                                ],
                                [Text("", size=(6, 1))],
                                [
                                    Text(
                                        "Ordering: {}".format(self.ordering),
                                        key="ordering",
                                    )
                                ],
                                [Text("", size=(6, 1))],
                                [
                                    Text(
                                        "Normalization: {}".format(normalization),
                                        key="normalization",
                                    )
                                ],
                                [Text("", size=(6, 1))],
                                [
                                    Text(
                                        "Radius of S.A.: {}".format(radius),
                                        key="radius",
                                    )
                                ],
                                [Text("", size=(6, 1))],
                                [
                                    Text(
                                        "Origin: {}".format(origin),
                                        key="origin",
                                    )
                                ],
                            )
                        )
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="-ZERNIKE MEMO FRAME-",
                )
            ],
            [Text("", size=(10, 2))],
            [
                Frame(
                    "Zernike Setup",
                    layout=[
                        [Text("", size=(24, 1))],
                        [
                            Column(
                                layout=list(
                                    itertools.chain(
                                        [self.add_heading(self.headings)],
                                        [
                                            self.chain_widgets(
                                                row=i + 1,
                                                input_list=[
                                                    r,
                                                    float(self.zernike["z"][i]),
                                                    int(m[i]),
                                                    int(n[i]),
                                                ],
                                                prefix="z",
                                                disabled_list=self.disabled_cols,
                                            )
                                            for i, r in enumerate(
                                                self.zernike["zindex"]
                                            )
                                        ],
                                    )
                                ),
                                scrollable=True,
                                vertical_scroll_only=True,
                                expand_y=True,
                                key="zernike",
                            )
                        ],
                        [Text("", size=(10, 2))],
                        [
                            Frame(
                                "Zernike Actions",
                                layout=[
                                    [
                                        Text("Add a new row: ", size=(24, 1)),
                                        Button(
                                            tooltip="Click to add a new row",
                                            button_text="Add row",
                                            enable_events=True,
                                            key="-ADD ZERNIKE ROW-",
                                        ),
                                    ],
                                    [
                                        Text(
                                            "Add or complete a order: ",
                                            size=(24, 1),
                                        ),
                                        Button(
                                            tooltip="Click to add a radial order",
                                            button_text="Add/Complete order",
                                            enable_events=True,
                                            key="-ADD ZERNIKE RADIAL ORDER-",
                                        ),
                                    ],
                                    [
                                        Text(
                                            "Paste Zernike coefficients: ",
                                            size=(24, 1),
                                        ),
                                        Button(
                                            tooltip="Click to paste Zernike coefficients",
                                            button_text="Paste coefficients",
                                            enable_events=True,
                                            key="PASTE ZERNIKES",
                                        ),
                                    ],
                                ],
                                font=self.font_titles,
                                relief=RELIEF_SUNKEN,
                                key="-ZERNIKE ACTIONS FRAME-",
                            )
                        ],
                    ],
                    font=self.font_titles,
                    relief=RELIEF_SUNKEN,
                    key="ZERNIKE FRAME",
                    expand_y=True,
                )
            ],
            [
                # Submit(
                #     tooltip="Click to submit (debug)", key="-SUBMIT ZERNIKES-"
                # ),
                Button("Exit", key="-EXIT ZERNIKES-"),
            ],
        ]

        # ------ Window creation ------ #
        self.window = Window(
            "Zernike window",
            layout,
            default_element_size=(12, 1),
            return_keyboard_events=True,
            finalize=True,
            enable_close_attempted_event=True,
            resizable=True,
            element_justification="center",
            keep_on_top=False,
        )

    def __call__(self):
        """
        Returns a rendering of the GUI Zernike window and handles the event loop.
        """

        self.make_window()

        # ------ Instantiate local variables ------ #
        order_closed = False

        while True:
            event, values = self.window.read(timeout=1000)
            if event == TIMEOUT_KEY:
                continue
            logger.trace("============ Event = {} ==============".format(event))
            elem = self.window.find_element_with_focus()
            elem_key = (
                elem.Key
                if (elem is not None and isinstance(elem.Key, (str, tuple)))
                else (0, 0)
            )

            # ------- Move with arrow keys within the Zernike tab ------#
            if isinstance(elem_key, str):
                _ = self.move_with_arrow_keys(
                    self.window,
                    event,
                    values,
                    elem_key,
                    self.max_rows,
                    len(self.headings),
                )

            # ------- Properly close the Zernike window ------#
            if event == "-EXIT ZERNIKES-" or event in (
                WINDOW_CLOSE_ATTEMPTED_EVENT,
                WINDOW_CLOSED,
            ):
                self.close_window()
                break

            # ------- Add a new row in the Zernike tab below those already present ------#
            elif event == "-ADD ZERNIKE ROW-":
                # Add row
                self.max_rows, _ = self.add_row(
                    row=self.max_rows,
                    dictionary=self.zernike,
                    ordering=self.ordering,
                )
                # Update the 'zernike' Column scrollbar
                self.update_column_scrollbar(window=self.window, col_key="zernike")

            # ------- Paste from the clipboard to the desired Zernike coefficients 'Z' input cell and below ------#
            elif event == "PASTE ZERNIKES":
                # Find current position in the Zernike tab
                row, col = re.findall("[0-9]+", elem_key.partition("_")[-1])
                if self.headings[int(col)] != "Z":
                    logger.error(
                        "The user shall select any cell from from the Z column. Skipping.."
                    )
                    continue
                # Get the text from the clipboard
                text = self.get_clipboard_text()
                # Update the Z coefficients by pasting and adding new rows
                row0 = row = int(row)
                for text_item in text:
                    self.window["z_({},1)".format(row)].update(text_item)
                    if self.max_rows <= row < row0 + len(text) - 1:
                        self.max_rows, _ = self.add_row(
                            row=self.max_rows,
                            dictionary=self.zernike,
                            ordering=self.ordering,
                        )
                    row += 1
                # Update the Zernike tab scrollbar
                self.update_column_scrollbar(window=self.window, col_key="zernike")

            # ------- Add a radial order to the current Zernike tab by adding rows until the order is closed ------#
            elif event == "-ADD ZERNIKE RADIAL ORDER-":
                # Check ordering
                if self.ordering not in ["ansi", "standard"]:
                    logger.error(
                        "Not supported with {} as ordering. Skipping..".format(
                            self.ordering.capitalize()
                        )
                    )
                    continue
                # Get azimuthal and radial orders and closing order condition
                m, n = Zernike.j2mn(N=self.max_rows, ordering=self.ordering)
                if self.ordering == "standard":
                    order_closed = min(m) == -max(n)
                elif self.ordering == "ansi":
                    order_closed = max(m) == max(n)
                # Keep adding rows to the current Zernike tab until the current radial order (unclosed) is complete
                if not order_closed:
                    while not order_closed:
                        self.max_rows, (m, n) = self.add_row(
                            row=self.max_rows,
                            dictionary=self.zernike,
                            ordering=self.ordering,
                        )
                        if self.ordering == "standard":
                            order_closed = min(m) == -max(n)
                        elif self.ordering == "ansi":
                            order_closed = max(m) == max(n)
                    # When finished, exit
                    continue
                # If the current radial order is closed, keep adding rows to add a new complete radial order
                new_m = new_n = max(n) + 1
                if self.ordering == "standard":
                    new_m = -new_m
                jmax = Zernike.mn2j(m=new_m, n=new_n, ordering=self.ordering)
                while self.max_rows < jmax + 1:
                    self.max_rows, _ = self.add_row(
                        row=self.max_rows,
                        dictionary=self.zernike,
                        ordering=self.ordering,
                    )
                # Update the Zernike tab scrollbar
                self.update_column_scrollbar(window=self.window, col_key="zernike")

            # ------- Display a popup window with the Zernike GUI values given as a flat dictionary ------#
            elif event == "-SUBMIT ZERNIKES-":
                popup(
                    "Paos GUI Zernike window",
                    'You clicked on the "{}" button'.format(event),
                    "The values are",
                    values,
                    keep_on_top=True,
                )

        # ------- Return the updated Zernike dictionary based on the current Zernike tab contents ------#
        zernike = {"zindex": [], "z": []}
        for key, item in values.items():
            row, col = re.findall("[0-9]+", key.partition("_")[-1])
            if col == "0":
                # Column 'Zindex'
                zernike["zindex"].append(item)
            elif col == "1":
                # Column 'Z'
                zernike["z"].append(item)
        zernike["zindex"] = ",".join(zernike["zindex"])
        zernike["z"] = ",".join(zernike["z"])
        zernike["ordering"] = self.ordering

        return zernike
