import os
from datetime import date

from .__version__ import __version__

__pkg_name__ = 'paos'
__author__ = "Andrea Bocchieri, Enzo Pascale"
__description__ = "The Physical Ariel Optics Simulator"
__url__ = "https://github.com/arielmission-space/PAOS"
__license__ = "BSD-3-Clause"
__copyright__ = '2020-{:d}, {}'.format(date.today().year, __author__)

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
logger.info('code version {}'.format(__version__))

from .log import setLogLevel

# setLogLevel(logging.TRACE)
# setLogLevel(logging.DEBUG)
setLogLevel(logging.INFO)
