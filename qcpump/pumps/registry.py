import importlib.util
from pathlib import Path
import re
import sys

from qcpump.logs import get_logger
from qcpump.settings import Settings

logger = get_logger("qcpump")
settings = Settings()


# dictionary to hold all the registed pump types
__PUMP_REGISTRY = {}


BASE_PUMP_SUBCLASS_RE = re.compile(r"^\s*class\s+(?P<pump_type>.*)\(.*BasePump.*\)\s*\:\s*$")


def register_pump_type(target_class):
    """Called when BasePump is subclassed to add the new pump type to the registry"""
    if target_class.__name__ in __PUMP_REGISTRY:
        msg = "Trying to register %s but a class with the name %s already exists in the report registry" % (
            target_class, target_class.__name__
        )
        raise ValueError(msg)
    __PUMP_REGISTRY[target_class.__name__] = target_class


def get_pump_types():
    """Return the QC Pump Type Registry (in form {'PumpTypeClassName': PumpTypeClass})"""
    return __PUMP_REGISTRY


def register_pump_types():
    """Look in the pump directories for any python files which appear to define
    a Pump Type"""

    # look in default pump directory as well as any directories defined by users in settings
    dirs = [settings._DEFAULT_PUMP_DIRECTORY] + (settings.PUMP_DIRECTORIES or [])

    logger.info(f"Looking for pumps in {dirs}")
    for d in dirs:
        logger.debug(f"Looking for pumps in {d}")
        d = Path(d)
        if not d.is_dir():
            logger.info(f"When looking for Pump types, an invalid directory was encountered: {d}")
            continue

        for p in d.glob("*/*py"):
            logger.debug(f"Checking if file {p} defines a pump type")
            if is_pumptype_file(p):
                logger.debug(f"At least one pump type detected in {p}")
                import_pump_type(p)
            else:
                logger.debug(f"No pump types detected in {p}")


def is_pumptype_file(path):
    """Iterate over lines in a file and return True if we find a line that
    looks like it subclasses the BasePump class"""

    try:
        with open(path, "r") as f:
            for line in f:
                if BASE_PUMP_SUBCLASS_RE.match(line):
                    return True
    except Exception:
        logger.exception(f"Unable to read {path}")
    return False


def import_pump_type(path):
    """
    Directly import the Pump module from input path.  This will
    cause any subclasses of BasePump to be registed in qcpump.pumps.base.PUMP_REGISTRY

    Recipe for importing a Python source file directly taken from
    https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    """

    logger.debug(f"Trying to import {path.stem} module from {path}")

    try:
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        logger.debug(f"Successfully imported {path.stem}")
        return module
    except Exception:
        logger.exception(f"Tried to import {path} as {module_name} but an exception occured.")
