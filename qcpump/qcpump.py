import json
import logging
import os
from pathlib import Path
import sys
import threading

import appdirs
import wx
import wx.adv
import wx.grid
import wx.lib.masked
import wx.lib.scrolledpanel

from qcpump import logs, utils
from qcpump.pumps.base import (
    EVT_PUMP_COMPLETE,
    EVT_PUMP_LOG,
    EVT_PUMP_PROGRESS,
)
from qcpump.pumps.registry import get_pump_types, register_pump_types
from qcpump.settings import Settings
import qcpump.ui as ui

settings = Settings()

PUMP_THREAD_JOIN_TIMEOUT = 5  # timeout after 5s while waiting for pump threads to finish

TOOL_TIP_PUMPING_START = "Click to begin pumping"
TOOL_TIP_PUMPING_PAUSE = "Click to pause pumping"
TOOL_TIP_PUMPING_DIRTY = "Please save or reset all Pump Configurations before beginning"


logger = logs.get_logger("qcpump")


class QCPumpUI(ui.VQCPumpUI):
    """Main user interface"""

    def __init__(self, parent, *args, **kwargs):
        """do any initial setup required for Orbis"""

        super().__init__(parent, *args, **kwargs)

        ico = wx.IconBundle()
        icon_path = settings.get_img_path("qcpump.ico")
        logger.debug(f"Loading icons from {icon_path}")
        ico.AddIcon(icon_path)
        self.SetTitle(f"QCPump - {settings.VERSION}")
        self.SetIcons(ico)
        self.SetMinSize((1024, 768))
        self.Fit()
        self.Center()

        self.pump_windows = {}

        # do expensive intialization after show event
        self._init_finished = False
        self._show_completed = True

        # used to track when user has asked to stop pumping
        self.kill_event = threading.Event()

    def log(self, pump_name, level, message):
        """write a log message for a pump. Level is e.g. logging.DEBUG"""
        logger.log(level, f"{pump_name}: {message}")

    def load_existing_pumps(self):
        """Read configs from disk and set up their pumps"""

        # root directy where configuration directories/files are stored
        config_path = self.get_pump_config_dir()
        pumps_to_load = []
        for path in config_path.glob("*/config.json"):
            try:
                logger.debug(f"Trying to load pump config from {path}")
                save_data = json.load(path.open("r"))
                logger.debug(f"Loaded pump config from {path}")
                pumps_to_load.append((save_data['name'], save_data))
            except Exception as e:
                self.non_fatal_error(f"Failed to load pump config from {path}", e)

        pump_types = get_pump_types()
        for name, save_data in sorted(pumps_to_load):
            if save_data['type'] not in pump_types:
                self.non_fatal_error(f"Failed to initialize pump config from {path}")
                continue

            try:
                self.add_pump_page(save_data['type'], name, save_data['state'])
            except Exception as e:
                self.non_fatal_error(f"Failed to initialize pump config from {path}", e)
                self.remove_pump_page(name)

        at_least_one_pump_loaded = self.pump_notebook.GetPageCount() > 0
        if at_least_one_pump_loaded:
            self.pump_notebook.SetSelection(0)

    def load_pump_state(self, name):
        """Load specific pump data from disk. (Used for resetting pump state)"""
        config_file = self.get_pump_config_path(name)
        state = None
        try:
            logger.debug(f"Attempting to load '{name}' pump state from {config_file}")
            state = json.load(open(config_file, "r"))
            logger.debug(f"Loaded '{name}' pump state from {config_file}")
        except Exception as e:
            self.non_fatal_error(f"Unable to load data from {config_file}", e)

        return state

    def OnAddPump(self, evt):
        """User requested a new pump to be added"""
        # ask user which type of pump to add
        dlg = AddPumpDialog(list(get_pump_types().keys()), list(self.pump_windows.keys()), self)
        if dlg.ShowModal() != wx.ID_OK:
            return

        pump_type_requested = ""
        try:
            pump_type_requested = dlg.get_pump_type()
            self.add_pump_page(pump_type_requested, dlg.get_pump_name())
        except Exception as e:
            self.fatal_error(f"Unable to add a '{pump_type_requested}' pump.", e)

    def add_pump_page(self, pump_type, pump_name, state=None):
        """Create a new PumpWindow and add it to our notebook"""
        parent = self.pump_notebook
        p = PumpWindow(pump_type, pump_name, parent, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.pump_notebook.AddPage(p, pump_name, select=True)
        self.pump_windows[pump_name] = p
        p.set_state(state)

        # I don't know why but you need a size event and to reset the focus
        # order to get the property controls to respond
        if 'win' not in sys.platform:
            p.Layout()
            p.Fit()
        self.SetFocus()
        p.SendSizeEvent()

    def save_pump(self, name, state):
        """persist pump state to disk"""
        pump_window = self.pump_windows[name]
        config_path = self.get_pump_config_path(name)
        save_data = {
            'type': pump_window.pump_type,
            'name': name,
            'version': settings.VERSION,
            'state': state,
        }

        try:
            f = open(config_path, "w")
        except Exception as e:
            self.non_fatal_error("Unable to open file to save: {config_path}", e)
            return False

        try:
            json.dump(save_data, f, indent=2)
            logger.debug(f"Wrote '{name}' state to {config_path}")
        except Exception as e:
            self.non_fatal_error("Unable to serialize configuration: {config_path}", e)
            return False

        return True

    def delete_pump(self, name):
        """Remove a pump by deleting its config file and removing it from the notebook"""
        config_file = self.get_pump_config_path(name)

        try:
            # TODO: Should we delete the whole directory?
            config_file.unlink()
        except Exception as e:
            self.non_fatal_error(f"Unable to delete {config_file} from disk", e)
            return False

        self.remove_pump_page(name)
        self.config_changed()

        return True

    def remove_pump_page(self, name):
        page = self.pump_windows.pop(name, None)
        if not page:
            return
        page_idx = self.pump_notebook.GetChildren().index(page)
        self.pump_notebook.DeletePage(page_idx)
        self.pump_notebook.SendSizeEvent()

    def set_pump_name(self, page_name, page_label):
        """Update a notebook page label"""
        idx = self.pump_notebook.GetChildren().index(self.pump_windows[page_name])
        try:
            self.pump_notebook.SetPageText(idx, page_label)
        except RuntimeError:
            # page already deleted
            pass

    def pump_stopped(self, name):
        """If there are no pumps actually running, but we are still in a pump
        running state put us back into a stopped state.  This can occur if say
        there is only one pump and it has an error and terminates itself"""

        pumps_running = self.run_pumps.GetValue()
        if not pumps_running:
            # we're already stopped so no need to do anything
            return False

        for pump_window in self.pump_windows.values():
            if pump_window.is_running():
                # at least one pump is running so quit looking
                return

        # no pumps running but we're still in a running state
        self.stop_pumps()

    def get_pump_config_dir(self):
        """Return the user directory used for saving pump configuration data"""
        pumps_dir = os.path.join(Settings.APPNAME, "pumps")
        return Path(appdirs.user_config_dir(pumps_dir, Settings.VENDOR))

    def get_pump_config_path(self, name):
        """Return the path of a specific pumps config file. If the file doesn't
        exist, it will be created."""
        name = utils.clean_filename(name)
        dir_path = self.get_pump_config_dir() / name
        path = dir_path / ("config.json")

        if not dir_path.is_dir():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.fatal_error(f"Unable to create configuration directory {dir_path}.", e)

        if not path.exists():
            try:
                path.touch()
                logger.debug(f"Created config file for {name} at {path}")
            except Exception as e:
                self.non_fatal_error(f"Unable to create configuration file at {path}.", e)

        return path

    def fatal_error(self, msg, exception=None):
        """The application can't recover from an error. Log the error, show user a message and quit"""
        if exception:
            logger.exception(msg)

        wx.CallAfter(self._fatal_error, msg)

    def _fatal_error(self, msg):
        wx.MessageBox(f"Fatal Error: {msg}\n\nPlease check the log file for details.")
        self.destroy()

    def non_fatal_error(self, msg, exception=None):
        """The application can recover from an error. Log the error, show user a message and continue"""
        if exception:
            logger.exception(msg)

        wx.CallAfter(wx.MessageBox, f"Warning: {msg}\n\nPlease check the log file for details.")

    def start_pumps(self):
        """Configs are all valid. Start the pumps!"""
        logger.debug("Starting pumps")

        # we don't want the user editing configuration data while pumping is occuring
        self.disable_pump_windows()

        # make sure kill event is cleared since it might be set from previous runs
        self.kill_event.clear()

        valid_count = 0
        for name, pump_window in self.pump_windows.items():

            if not pump_window.pump.active:
                pump_window.update_status(0, "Not running. Inactive")
                continue

            if pump_window.pump.valid:
                valid_count += 1
                logger.debug(f"Starting pump '{name}'")
                pump_window.start_pumping()
            else:
                pump_window.update_status(0, "Not running. Invalid configuration")

        if valid_count:
            self.status_bar.SetStatusText(f"Running {valid_count} pumps")
            self.run_pumps.SetLabelText("Stop Pumps")
            self.run_pumps.SetToolTip(TOOL_TIP_PUMPING_PAUSE)
        else:
            self.status_bar.SetStatusText("Pumps will not run since there are no valid pumps")
            self.stop_pumps()

    def stop_pumps(self):
        """Set the kill event and stop all pumps"""
        self.kill_event.set()
        logger.debug("Stopping pumps. Kill Event Set")

        npumps = len(self.pump_windows)
        for idx, (name, pump_window) in enumerate(self.pump_windows.items()):
            self.status_bar.SetStatusText(f"Waiting for {npumps - idx}/{npumps} Pumps to finish")
            if pump_window.is_running():
                logger.debug(f"Stopping pump {name}")
                pump_window.stop_pumping()
            else:
                logger.debug(f"Pump {name} already stopped")

        self.status_bar.SetStatusText("Pumps all stopped")
        self.enable_pump_windows()
        self.run_pumps.SetValue(False)
        self.run_pumps.SetLabelText("Run Pumps")
        self.run_pumps.SetToolTip(TOOL_TIP_PUMPING_START)

    def enable_pump_windows(self):
        """Prevent user from editing any pump configs"""
        for pump_window in self.pump_windows.values():
            pump_window.pump.Enable(True)
            pump_window.pump.SetToolTip("")
        self.add_pump.Enable(True)
        self.add_pump.SetToolTip("")

    def disable_pump_windows(self):
        """Enable user editing of pump configs"""
        for pump_window in self.pump_windows.values():
            pump_window.pump.Enable(False)
            pump_window.pump.SetToolTip("Please stop all Pumps before editing configurations")
        self.add_pump.Enable(False)
        self.add_pump.SetToolTip("Stop all pumps before adding new ones")

    def config_changed(self):
        """PumpWindows can use this to inform us configuration value changed"""
        # we don't want to let user run pumps if any of the configurations
        # have been modified and not saved or reset
        dirty = self.get_dirty_pumps()
        enable = len(dirty) == 0
        self.run_pumps.Enable(enable)
        self.run_pumps.SetToolTip(TOOL_TIP_PUMPING_START if enable else TOOL_TIP_PUMPING_DIRTY)

    def get_dirty_pumps(self):
        """Return any pump window which has a non-saved (dirty) state"""
        return [pw.name for pw in self.pump_windows.values() if pw.pump.dirty]

    def OnRunPumpsToggle(self, evt):
        """User manually toggled the run pumps button"""
        start_pumps = self.run_pumps.GetValue()
        if start_pumps:
            self.start_pumps()
        else:
            self.stop_pumps()

    def OnAbout(self, evt):
        """User asked to see About dialog"""
        items = [
            ("About QCPump Version", settings.VERSION),
            ("", ""),
            ("Config File Location", self.get_pump_config_dir()),
            ("Log File Location", str(logs.get_log_dir())),
            ("Settings File Location", str(settings.fname)),
            ("Author", "Randy Taylor (QATrack+ Project)"),
            ("Contact", "randy@multileaf.ca"),
            ("Web", "https://www.multileaf.ca"),
        ]
        lines = []
        for label, val in items:
            sep = ':\n      ' if val not in (None, '') else ''
            lines.append("%s%s %s" % (label, sep, str(val)))
        wx.MessageBox('\n'.join(lines), "About QCPump", style=wx.OK, parent=self)

    def OnClose(self, evt):
        """OS level close event"""
        # if the event can't be vetoed, the window must get destroyed.
        # https://www.wxpython.org/Phoenix/docs/html/wx.CloseEvent.html
        if evt.CanVeto() and not self.confirm_quit():
            evt.Veto()
            return

        self.destroy()

    def OnQuit(self, evt):
        """Menu/user level close event"""
        if self.confirm_quit():
            self.destroy()

    def confirm_quit(self):
        """Ensure that the user wants to quit if there are dirty pumps"""
        dirty = self.get_dirty_pumps()
        if dirty:
            if len(dirty) == 1:
                msg = f"The config file for {dirty[0]} has not been saved.  Quit without saving?"
            else:
                msg = f"The config files for {', '.join(dirty)} have not been saved.  Quit without saving?"

            if wx.MessageBox(msg, "Quit without saving?", wx.ICON_QUESTION | wx.YES_NO) != wx.YES:
                return False
        return True

    def destroy(self):
        """make sure pumps are stopped before killing"""
        self.stop_pumps()
        self.Destroy()

    def OnShow(self, event):
        self._show_completed = True

    def OnIdle(self, event):
        if not self._init_finished and self._show_completed:
            self._init_finished = True
            self.log("qcpump", logging.DEBUG, "Starting to load existing pumps")
            self.load_existing_pumps()
            self.log("qcpump", logging.DEBUG, "Completed load of existing pumps")


class StatusPanel(ui.VStatusPanel):
    """UI element for displaying progress and log messages from pumps"""

    def __init__(self, *args, **kwargs):
        """Set up this status panel by adding our logging grid"""
        super().__init__(*args, **kwargs)

        self.log_grid = logs.LogGrid(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.GetSizer().Add(self.log_grid, 1, wx.ALL | wx.EXPAND, 5)

    def update_progress(self, progress, status):
        """Update the progress bar for this pumps status panel"""
        self.progress.SetValue(min(100, max(progress, 0)))
        self.status.SetLabelText(status)

    def log(self, level, message):
        """Write a log message to the logging grid"""
        self.log_grid.log(level, message)

    def clear_log(self):
        """Clean out log grid"""
        self.log_grid.clear()


class PumpWindow(wx.SplitterWindow):
    """A split window consisting of a pumps config on one side and status panel on the other"""

    def __init__(self, pump_type, pump_name, *args, **kwargs):
        """Initial configuration our pump window with the pump config & status windows"""
        self.pump_type = pump_type
        self.name = pump_name
        self.logger = logs.get_logger(self.name)

        super().__init__(*args, **kwargs)

        self.app = self.GetTopLevelParent()

        # initialize the Pump Configuration UI window
        PumpTypeClass = get_pump_types()[self.pump_type]
        self.pump = PumpTypeClass(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.VSCROLL,
        )

        self.status_split = StatusPanel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL | wx.VSCROLL)

        self.SplitVertically(self.pump, self.status_split, int(0.5 * self.Parent.GetSize()[0]))
        self.SetSashPosition(int(0.5 * self.Parent.GetSize()[0]))

        self.timer = wx.Timer(self)
        self.pump_thread = None
        self.Bind(wx.EVT_TIMER, self.OnPumpTimer, source=self.timer)

        self.Bind(EVT_PUMP_PROGRESS, self.OnPumpProgress)
        self.Bind(EVT_PUMP_COMPLETE, self.OnPumpComplete)
        self.Bind(EVT_PUMP_LOG, self.OnPumpLog)

    def is_running(self):
        """Is our pump running?"""
        return self.timer.IsRunning() or self.pump_thread is not None

    def OnPumpTimer(self, evt):
        """Interval timer triggered. Run the pump!"""
        self._run_pump()

    def OnPumpProgress(self, evt):
        """Pump thread sent a progress event. Update the status accordingly"""
        result = evt.GetValue()
        self.update_status(result['progress'], result['message'])

    def OnPumpComplete(self, evt):
        """Pump thread sent a pumping complete message. We can clear the thread now"""
        self.pump_thread = None

    def OnPumpLog(self, evt):
        """Pump thread sent a logging message."""
        result = evt.GetValue()
        self.logger.log(result['level'], result['message'])
        self.status_split.log(result['level'], result['message'])

    def set_state(self, state):
        """Set the state for this pump"""
        self.pump.configure(self.pump_type, self.name, state=state)

    def start_pumping(self):
        """Run the pump immediately and then every interval seconds after (via OnPumpTimer)"""
        self.status_split.clear_log()
        self._run_pump()
        interval = self.pump.get_config_value("Pump", "interval (s)")
        self.timer.Start(interval * 1000)

    def _run_pump(self):
        """If our pump is not already running, start it up."""
        if self.pump_thread is None:
            self.pump_thread = threading.Thread(target=self.pump.run, args=(self.app.kill_event,), daemon=True)
            self.pump_thread.start()

    def stop_pumping(self):
        """App requested we stop pumping. Note the apps kill_event is set by this point"""
        self.timer.Stop()
        if self.pump_thread:
            # Give the thread some time to finish if it needs it
            self.pump_thread.join(PUMP_THREAD_JOIN_TIMEOUT)
            self.pump_thread = None
        self.app.pump_stopped(self.name)

    def set_dirty(self, dirty):
        """Tell main window whether this pump has changed fields"""
        name = self.name if not dirty else f"*{self.name}*"
        self.app.set_pump_name(self.name, name)
        self.app.config_changed()

    def update_status(self, progress, message):
        """Update the status indicators"""
        self.status_split.update_progress(progress, message)

    def delete(self):
        """Delete this pump"""
        self.app.delete_pump(self.name)

    def save(self):
        """Save pumps state to disk"""
        return self.app.save_pump(self.name, self.pump.state)

    def reset(self):
        """Reset the pumps state to last save"""
        return self.app.load_pump_state(self.name)['state']

    def log(self, level, message):
        self.status_split.log(level, message)


class AddPumpDialog(ui.VAddPumpDialog):
    """Dialog for user to select the pump type and name that they want to add.
    Checks for uniqueness of pump names."""

    def __init__(self, pump_types, existing_pump_names, *args, **kwargs):
        """Initialize AddPumpDialog by setting the available pump types and and
        pump names that are already in use so uniqueness of pump name can be
        enforced"""

        super().__init__(*args, **kwargs)
        self.existing_pump_names = [x.lower() for x in existing_pump_names]
        self.pump_type.SetItems(pump_types)

    def OnPumpTypeChange(self, evt):
        """User changed pump type, set default pump name if required"""
        cur_val = self.pump_name.GetValue()
        if not cur_val.strip():
            self.pump_name.SetValue(evt.GetString())

    def OnOk(self, evt):
        """Do validation after user clicks OK"""
        pump_name = self.pump_name.GetValue().lower()
        selected_pump_type = self.pump_type.GetStringSelection()

        if not selected_pump_type:
            wx.MessageBox("You must choose a Pump Type", "Missing Pump Type", wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR)
            return

        if pump_name in self.existing_pump_names:
            wx.MessageBox(
                "That Pump name is already in use. Please choose a new name", "Duplicate Pump Name",
                wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR
            )
            return
        elif not pump_name and selected_pump_type in self.existing_pump_names:
            wx.MessageBox(
                "Please enter a unique name for this Pump", "Missing Pump Name", wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR
            )
            return
        elif not pump_name and selected_pump_type not in self.existing_pump_names:
            # name was blank but no pump exists with name of selected pump type, so we'll use that
            self.pump_name.SetValue(selected_pump_type)

        evt.Skip()

    def get_pump_type(self):
        """Return the pump type name that is currently selected"""
        return self.pump_type.GetStringSelection()

    def get_pump_name(self):
        """Return the string currently entered for the pump name"""
        return self.pump_name.GetValue()


def main():
    """Launch the QCPump program"""

    app = wx.App(
        useBestVisual=True,
        redirect=False,  # leave as False.  stderr/stdout will be redirected below when not in debug mode
        clearSigInt=True,  # set to True to allow a Ctrl+C to kill app
    )

    if logger is None:
        loc = logs.get_log_location()
        msg = (
            f"Failed to create log file at {loc}.\n\n"
            f"Please ensure you have write permissions on the directory {loc.parent}"
        )
        wx.MessageBox(f"Fatal Error: {msg}", style=wx.ICON_ERROR, caption="Unable to launch")
        return

    try:

        # Before launching GUI we need to first see what kind of pump types are
        # available
        register_pump_types()

        frame = QCPumpUI(None)
        frame.Show()

    except Exception:

        logger.exception("Unhandled exception during initialization")
        msg = (
            "Unhandled exception during initialization. Check " +
            str(logs.get_log_location('qcpump')) + " for details"
        )
        wx.MessageBox(f"Fatal Error: {msg}", style=wx.ICON_ERROR, caption="Unable to launch.")
        return

    # everything started up ok let's go!
    if not settings.DEBUG:
        app.RedirectStdio()

    try:
        app.MainLoop()
    except Exception:
        logger.exception("Unhandled exception in app.MainLoop")


if __name__ == "__main__":
    main()
