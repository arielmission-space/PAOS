import sys
from paos import logger


def addLogFile(filename):
    logger.add(filename)


def setLogLevel(level="INFO"):
    logger.configure(handlers=[{"sink": sys.stderr, "level": level}])


def disableLogging(name="paos"):
    logger.disable(name)


def enableLogging(name="paos"):
    logger.enable(name)
