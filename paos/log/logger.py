import sys

from paos import logger


def addLogFile(fname="paos.log"):
    """
    Adds a new log file for logging.

    Parameters
    ----------
    fname : str, optional
        The filename for the log file. Defaults to 'paos.log'.

    Returns
    -------
    None
    """
    logger.add(fname)


def setLogLevel(level="INFO"):
    """
    Configures the logging level for the logger.

    Parameters
    ----------
    level : str, optional
        The logging level to set. Defaults to 'INFO'. Possible values include
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', etc.

    Returns
    -------
    None
    """
    logger.configure(handlers=[{"sink": sys.stderr, "level": level}])


def disableLogging(name="paos"):
    """
    Disables the logger for the given module name.

    Parameters
    ----------
    name : str, optional
        The module name to disable logging for. Defaults to 'paos'.

    Returns
    -------
    None
    """
    logger.disable(name)


def enableLogging(name="paos"):
    """
    Enables the logger for the given module name.

    Parameters
    ----------
    name : str, optional
        The module name to enable logging for. Defaults to 'paos'.

    Returns
    -------
    None
    """
    logger.enable(name)
