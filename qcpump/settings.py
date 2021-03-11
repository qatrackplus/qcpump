import json
import os
from pathlib import Path
import sys

import appdirs

# first figure out where our application is running.  This will differ
# depending on platform and whether or not the application is frozen by
# py2exe/pyinstaller/cx_freeze/other
frozen = getattr(sys, 'frozen', '')
if not frozen:  # not frozen: in regular python interpreter
    root = os.path.abspath(os.path.dirname(__file__))
    frozen = False
elif frozen in ('dll', 'console_exe', 'windows_exe', 1):  # py2exe/pyinstaller:
    frozen = True
    try:
        # pyinstaller
        base_path = sys._MEIPASS
        root = os.path.dirname(base_path)
    except Exception:
        # cx_freeze
        root = os.path.dirname(sys.executable)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if frozen:
        return os.path.join(root, "qcpump", relative_path)
    return os.path.join(root, relative_path)


class Settings:
    """A class to hold QCPump Application settings.  Default settings can be
    overridden using a settings.json file"""

    ROOT = root  # where is the root directory
    FROZEN = frozen  # is the application "compiled" by py2exe/pyinstaller/cx_freeze?
    RESOURCES = resource_path("resources")  # root resource directory
    IMG_RESOURCES = os.path.join(RESOURCES, "img")  # where are images stored?

    DEBUG = False  # primarily controls how things are logged
    LOG_LEVEL = "info"  # debug | info | warning | error | critical
    LOG_TO_CONSOLE = False  # should logs be written to console as well as log files?

    VERSION = "v0.1.1"  # current QCPump version
    VENDOR = "QATrack Project"
    APPNAME = "qcpump"

    if frozen:
        _DEFAULT_PUMP_DIRECTORY = os.path.join(root, "qcpump", "contrib", "pumps")  # first party pump type directory
    else:
        _DEFAULT_PUMP_DIRECTORY = os.path.join(root, "contrib", "pumps")  # first party pump type directory

    PUMP_DIRECTORIES = None  # set to list of other directories to include user defined pump types from

    DB_CONNECT_TIMEOUT = 30  # timeout for database connections where available

    BROWSER_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
    )

    def __init__(self):
        """Load settings.json file and override any settings defined in it"""

        settings_dir = Path(appdirs.user_config_dir(Settings.APPNAME, Settings.VENDOR))
        self.fname = settings_dir / "settings.json"
        if not self.fname.parent.exists():
            self.fname.parent.mkdir(parents=True, exist_ok=True)

        # if the settings.json file doesn't exist, create it and stick an empty json doc in it
        if not os.path.exists(self.fname):
            try:
                with open(self.fname, "w") as f:
                    f.write(json.dumps({
                        "LOG_LEVEL": "info",
                        "DEBUG": False,
                        "PUMP_DIRECTORIES": [],
                        "DB_CONNECT_TIMEOUT": 3,
                    }, indent=2))
            except Exception as e:
                raise Exception("Unable to create settings file %s. Error was %s" % (self.fname, str(e)))

        # now load settings file
        try:
            with open(self.fname, 'rt') as f:
                settings = json.load(f)
        except Exception as e:
            raise Exception("Settings file %s is not valid json. Error was %s" % (self.fname, str(e)))

        # override any settings user has set in settings.json
        for k, v in settings.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def get_img_path(self, img_file_name):
        """return full path for image resource with filename"""
        return os.path.join(self.IMG_RESOURCES, img_file_name)

    def ico(self, icon_name):
        """return full path to icon named icon_name"""
        return os.path.join(self.IMG_RESOURCES, "icons", icon_name + ".png")
