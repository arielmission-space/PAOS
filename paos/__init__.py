import importlib.metadata as metadata
import os
from datetime import date

__version__ = metadata.version("paos")

# load package info
__pkg_name__ = __title__ = metadata.metadata("paos")["Name"].upper()
__url__ = metadata.metadata("paos")["Project-URL"]
__author__ = metadata.metadata("paos")["Author"]
__license__ = metadata.metadata("paos")["License"]
__copyright__ = f"2021-{date.today().year:d}, {__author__}"
__summary__ = metadata.metadata("paos")["Summary"]

# load package commit number
try:
    __base_dir__ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    __base_dir__ = None

__commit__ = None
__branch__ = None
if __base_dir__ is not None and os.path.exists(os.path.join(__base_dir__, ".git")):
    git_folder = os.path.join(__base_dir__, ".git")
    with open(os.path.join(git_folder, "HEAD")) as fp:
        ref = fp.read().strip()
    ref_dir = ref[5:]
    __branch__ = ref[16:]
    try:
        with open(os.path.join(git_folder, ref_dir)) as fp:
            __commit__ = fp.read().strip()
    except FileNotFoundError:
        __commit__ = None


import matplotlib.pyplot as plt
from loguru import logger

from paos.classes.abcd import ABCD
from paos.classes.psd import PSD
from paos.classes.wfo import WFO
from paos.classes.zernike import PolyOrthoNorm, Zernike
from paos.core.coordinateBreak import coordinate_break
from paos.core.parseConfig import parse_config
from paos.core.plot import plot_pop
from paos.core.raytrace import raytrace
from paos.core.run import run
from paos.core.saveOutput import save_datacube, save_output

# initialise logger
logger.level("Announce", no=100, color="<magenta>")

# initialise plotter
plt.rcParams["figure.facecolor"] = "white"
plt.rc("lines", linewidth=1.5)
plt.rc(
    "axes",
    axisbelow=True,
    titleweight="bold",
    labelcolor="dimgray",
    labelweight="bold",
)
plt.rc("font", size=12)

import shutil

has_latex = shutil.which("latex") is not None
has_renderer = shutil.which("dvipng") is not None or shutil.which("dvisvgm") is not None

plt.rc("text", usetex=(has_latex and has_renderer))
