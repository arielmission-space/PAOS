# This code is inspired by the logger developed for ExoSim2.0 which is in turn
# inspired by the logger developed for TauREx3.1
# Therefore, we attach here the ExoSim2.0 and the TauREx3.1 license:
#
# BSD 3-Clause License
#
# Copyright (c) 2020, arielmission-space
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
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
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

from decorator import decorator

from paos import __pkg_name__

__all__ = ["Logger"]

root_logger = logging.getLogger(__pkg_name__)
root_logger.propagate = False


class CustomFormatter(logging.Formatter):
    """Custom formatter for logging.
    Different colors propagate to the terminal depending on the level of the log.
    """

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    brown = "\x1b[0;33m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        10: grey + format + reset,
        15: grey + format + reset,
        20: green + format + reset,
        30: yellow + format + reset,
        40: red + format + reset,
        50: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
ch.setLevel(logging.DEBUG)
root_logger.addHandler(ch)
root_logger.setLevel(logging.DEBUG)


class Logger:
    """
    *Abstract class*

    Standard logging using logger library.
    It's an abstract class to be inherited to load its methods for logging.
    It define the logger name at the initialization, and then provides the logging methods.
    """

    def __init__(self):
        self._logger = None
        self._log_name = None
        self.set_log_name()

    def set_log_name(self):
        """
        Produces the logger name and store it inside the class.
        The logger name is the name of the class that inherits this Logger class.
        """
        self._log_name = "{}.{}".format(__pkg_name__, self.__class__.__name__)
        self._logger = logging.getLogger(
            "{}.{}".format(__pkg_name__, self.__class__.__name__)
        )

    def info(self, message, *args, **kwargs):
        """
        Produces INFO level log
        See :class:`logging.Logger`
        """
        self._logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """
        Produces WARNING level log
        See :class:`logging.Logger`
        """
        self._logger.warning(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """
        Produces DEBUG level log
        See :class:`logging.Logger`
        """
        self._logger.debug(message, *args, **kwargs)

    def trace(self, message, *args, **kwargs):
        """
        Produces TRACE level log
        See :class:`logging.Logger`
        """
        self._logger.trace(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """
        Produces ERROR level log
        See :class:`logging.Logger`
        """
        self._logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """
        Produces CRITICAL level log
        See :class:`logging.Logger`
        """
        self._logger.critical(message, *args, **kwargs)


@decorator
def traced(obj, *args, **kwargs):
    """
    Decorator to attach to functions and methods to log at TRACE level.
    Trace level produced a log anytime a function or a method is entered and exited.
    """
    logger = logging.getLogger(generate_logger_name(obj))

    logger.trace("called")
    value = obj(*args, **kwargs)
    logger.trace("exited")

    return value


def generate_logger_name(obj):
    """
    Given a class method or a function it returns the logger name.

    Parameters
    ----------
    obj
        class method or function

    Returns
    -------
    str
        logger name
    """
    parent_logger_name = obj.__module__
    return "{}.{}".format(
        parent_logger_name, getattr(obj, "__qualname__", obj.__name__)
    )
