import datetime
import logging
import logging.handlers
from pathlib import Path
import sys

import appdirs
import wx

from qcpump import utils
from qcpump.settings import Settings

formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')

settings = Settings()


def get_log_level(level_display=None):
    """
    Takes a string like 'debug' and returns the corresponding logging level.
    Defaults to logging.DEBUG
    """
    try:
        return {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }[level_display.lower()]
    except KeyError:
        return logging.DEBUG


def get_log_dir():
    """Return a Path object corresponding to the directory where log files are stored"""
    return Path(appdirs.user_log_dir(Settings.APPNAME, Settings.VENDOR, version=Settings.VERSION))


def get_log_location(name):
    """
    Return a Path object corresponding to the log file with name provided.  The
    name will be cleaned to ensure it is a valid filename.
    """
    name = utils.clean_filename(name)
    return get_log_dir() / f"{name}.log"


def get_logger(name):
    """This function will set up a logger with the given name and ensure that a
    file exists to write the logs to"""
    # create logger and set logging level based on current settings
    logger = logging.getLogger(name)
    app_log_level = get_log_level(settings.LOG_LEVEL)
    logger.setLevel(app_log_level)

    try:
        f = get_log_location(name)
        if not f.parent.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(f, maxBytes=1_000_000, backupCount=1)
    except Exception:
        return None

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.LOG_TO_CONSOLE:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    if app_log_level == logging.DEBUG:
        import http.client
        http.client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(app_log_level)
        requests_log.propagate = True

    return logger


class LogGrid(wx.grid.Grid):
    """A wxPython grid for displaying Pump logs to the user"""

    LOG_DATE_COL = 0
    LOG_DATE_COL_WIDTH = 170

    LOG_LEVEL_COL = 1
    LOG_LEVEL_COL_WIDTH = 80

    LOG_MSG_COL = 2

    LOG_LEVEL_DISPLAY = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def __init__(self, *args, max_rows=100, **kwargs):
        """Create and configure the logging grid"""
        super().__init__(*args, **kwargs)

        # Grid
        self.CreateGrid(0, 0)
        self.EnableEditing(False)
        self.EnableGridLines(True)
        self.EnableDragGridSize(False)
        self.SetMargins(0, 0)
        self.SetSelectionMode(self.GridSelectionModes.GridSelectRows)

        # Columns
        self.EnableDragColMove(False)
        self.EnableDragColSize(False)
        self.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        # Rows
        self.max_rows = max(1, max_rows)
        self.EnableDragRowSize(False)
        self.SetRowLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        # Cell Defaults
        self.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)

        self.setup()

    def setup(self):
        """set col labels and sizes"""
        self.SetRowLabelSize(0)

        columns = ["Date/Time", "Log Level", "Message"]
        self.AppendCols(len(columns))
        for idx, label in enumerate(columns):
            self.SetColLabelValue(idx, label)
        self.SetColSize(self.LOG_DATE_COL, self.LOG_DATE_COL_WIDTH)
        self.SetColSize(self.LOG_LEVEL_COL, self.LOG_LEVEL_COL_WIDTH)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)

    def log(self, level, message):
        """Write a message to the logging grid"""
        self.InsertRows(pos=0, numRows=1)

        nrows = self.GetNumberRows()
        if nrows > self.max_rows:
            self.DeleteRows(pos=nrows-1, numRows=1)

        date = datetime.datetime.now()
        level_display = self.LOG_LEVEL_DISPLAY[level]
        log_row = 0
        self.SetCellValue(log_row, self.LOG_DATE_COL, utils.format_dt(date))
        self.SetCellValue(log_row, self.LOG_LEVEL_COL, level_display)
        self.SetCellValue(log_row, self.LOG_MSG_COL, str(message))
        self.AutoSizeColumn(self.LOG_MSG_COL)

    def clear(self):
        nrows = self.GetNumberRows()
        if nrows:
            self.DeleteRows(0, nrows)

    def OnKey(self, evt):
        """Handle Ctrl+C keyboard press"""
        C_KEY = 67
        if evt.ControlDown() and evt.GetKeyCode() == C_KEY:
            self.copy()

    def copy(self):
        """Copy the current selection to the clipboard formatted as TSV"""
        rows = self.GetSelectedRows()
        cols = self.GetSelectedCols()

        data = ''
        cols = list(range(self.GetNumberCols()))
        for r in rows:
            for c in cols:
                data = data + str(self.GetCellValue(r, c))
                if c < len(cols) - 1:
                    data = data + '\t'
            data = data + '\n'

        # Create text data object
        clipboard = wx.TextDataObject()
        # Set data object value
        clipboard.SetText(data)
        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")
