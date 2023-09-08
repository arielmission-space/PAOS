import importlib.metadata as metadata
import os
from datetime import date

from .__version__ import __version__

# load package info
__pkg_name__ = metadata.metadata("paos")["Name"]
__url__ = metadata.metadata("paos")["Home-page"]
__author__ = metadata.metadata("paos")["Author"]
__email__ = metadata.metadata("paos")["Author_email"]
__license__ = metadata.metadata("paos")["license"]
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

# initialise logger
import logging

logger = logging.getLogger(__pkg_name__)
logger.info(f"code version {__version__}")

from paos.log import setLogLevel, addLogFile

setLogLevel(logging.INFO)
addLogFile(level=logging.INFO)
