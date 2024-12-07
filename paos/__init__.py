import importlib.metadata as metadata
import os
from datetime import date

# load package info
__pkg_name__ = metadata.metadata("paos")["Name"].upper()
__version__ = metadata.version("paos")
__url__ = metadata.metadata("paos")["Project-URL"]
__author__ = metadata.metadata("paos")["Author"]
__license__ = metadata.metadata("paos")["License"]
__copyright__ = "2021-{:d}, {}".format(date.today().year, __author__)
__summary__ = metadata.metadata("paos")["Summary"]

try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    base_dir = None

__branch__ = None
if base_dir is not None and os.path.exists(os.path.join(base_dir, ".git")):
    git_folder = os.path.join(base_dir, ".git")
    with open(os.path.join(git_folder, "HEAD")) as fp:
        ref = fp.read().strip()
    ref_dir = ref[5:]
    __branch__ = ref[16:]
    try:
        with open(os.path.join(git_folder, ref_dir)) as fp:
            __commit__ = fp.read().strip()
    except FileNotFoundError:
        __commit__ = None
else:
    __commit__ = None

from loguru import logger

logger.level("Announce", no=100, color="<magenta>")

from paos.classes.wfo import WFO
from paos.classes.abcd import ABCD
from paos.classes.zernike import Zernike, PolyOrthoNorm
from paos.classes.psd import PSD

from paos.core.parseConfig import parse_config
from paos.core.coordinateBreak import coordinate_break
from paos.core.raytrace import raytrace
from paos.core.plot import plot_pop
from paos.core.saveOutput import save_output, save_datacube
from paos.core.run import run

# initialise plotter
import matplotlib.pyplot as plt

plt.rcParams["figure.facecolor"] = "white"
plt.rc("lines", linewidth=1.5)
plt.rc(
    "axes",
    axisbelow=True,
    titleweight="bold",
    labelcolor="dimgray",
    labelweight="bold",
)
plt.rc("font", size=14)
