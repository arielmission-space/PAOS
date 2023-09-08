# This code is inspired by the logger developed for TauREx 3.1.
# Therefore, we attach here the TauREx3.1 license:
#
# BSD 3-Clause License
#
# Copyright (c) 2019, Ahmed F. Al-Refaie, Quentin Changeat, Ingo Waldmann, Giovanna Tinetti
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the names of the copyright holders nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import logging

from .logger import generate_logger_name
from .logger import Logger
from .logger import traced
from paos import __pkg_name__

last_log = logging.INFO

logging.TRACE = 15
logging.addLevelName(logging.TRACE, "TRACE")

def trace(self, message, *args, **kws):
    """
    Log TRACE level.
    Trace level log should be produced anytime a function or a methods is entered and exited."""
    if self.isEnabledFor(logging.TRACE):
        # Yes, logger takes its '*args' as 'args'.
        self._log(logging.TRACE, message, args, **kws)


logging.Logger.trace = trace


def setLogLevel(level, log_id=0):
    """
    Simple function to set the logger level

    Parameters
    ----------
    level: logging level
    log_id: int
        this is the index of the handler to edit. The basic handler index is 0.
        Every added handler is appended to the list. Default is 0.

    """
    global last_log
    from .logger import root_logger

    root_logger.handlers[log_id].setLevel(level)
    last_log = level


def disableLogging(log_id=0):
    """
    It disables the logging setting the log level to ERROR.

    Parameters
    ----------
    log_id: int
        this is the index of the handler to edit. The basic handler index is 0.
        Every added handler is appended to the list. Default is 0.

    """
    setLogLevel(logging.ERROR, log_id)


def enableLogging(level=logging.INFO, log_id=0):
    """
    It disables the logging setting the log level to ERROR.

    Parameters
    ----------
    level: logging level
        Default is logging.INFO.
    log_id: int
        this is the index of the handler to edit. The basic handler index is 0.
        Every added handler is appended to the list. Default is 0.

    """
    global last_log
    if last_log is None:
        last_log = level
    setLogLevel(level, log_id)


def addHandler(handler):
    """
    It adds a handler to the logging handlers list.

    Parameters
    ----------
    handler: logging handler

    """
    from .logger import root_logger

    root_logger.addHandler(handler)


def addLogFile(
    fname="{}.log".format(__pkg_name__), reset=False, level=logging.DEBUG
):
    """
    It adds a log file to the handlers list.

    Parameters
    ----------
    fname: str
        name for the log file. Default is exosim.log.
    reset: bool
        it reset the log file if it exists already. Default is False.
    level: logging level
        Default is logging.INFO.
    """
    if reset:
        import os

        try:
            os.remove(fname)
        except OSError:
            pass
    file_handler = logging.FileHandler(fname)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    addHandler(file_handler)
