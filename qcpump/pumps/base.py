from queue import Queue
import copy
import inspect
import logging
from pathlib import Path
import threading
import traceback
from uuid import uuid4

import wx
import wx.lib.scrolledpanel
import wx.propgrid as wxpg

from qcpump.pumps import dependencies
from qcpump.logs import get_log_level
from qcpump.pumps.registry import register_pump_type
from qcpump.settings import Settings


class BaseValidator(wx.Validator):
    """Base validator class for configuration options"""

    def __init__(self, validation_info, *args, **kwargs):
        """initialize and set validation_info which may contain information
        about e.g.  maximum and minimum values, or other validation limits"""

        self.validation_info = validation_info
        super().__init__(*args, **kwargs)

    def Clone(self):
        """required for every wx.Validator sublcass"""
        return self.__class__(self.validation_info)

    def TransferToWindow(self):
        """required for every wx.Validator sublcass"""
        return True

    def Validate(self, value):
        """
        Always return True.  We are going to use custom validation done by the
        'ValidateValue' method during the OnGridChanging event.  This is a hack
        to work around the fact that normal validators don't seem to work
        with PropertyGridManager, even though they work with Property Grid :(
        """
        return True

    def ValidateValue(self, value):
        """Default validation always returns True"""
        return True


class MaxMinValidator(BaseValidator):
    """Validator to ensure a number falls within max and min limits"""

    def ValidateValue(self, value):
        """Check if input value falls in closed interval [min, max]"""
        minv = self.validation_info.get("min")
        maxv = self.validation_info.get("max")
        valid = (
            (minv is None or value >= minv) and
            (maxv is None or value <= maxv)
        )
        return valid


class DirValidator(BaseValidator):
    """Validator to ensure a string is a valid file path"""

    def Validate(self, win):
        """Check if inputs value is a valid file path"""

        value = win.GetSelection().GetValue()

        if not value:
            return True

        try:
            assert Path(value).is_dir()
        except (TypeError, AssertionError):
            return False

        return True


BOOLEAN = 'boolean'
STRING = 'string'
INT = 'int'
UINT = 'uint'
FLOAT = 'float'
MULTCHOICE = 'multchoice'
DIRECTORY = 'directory'

PROPERTY_TYPES = {
    BOOLEAN: wxpg.BoolProperty,
    STRING: wxpg.StringProperty,
    INT: wxpg.IntProperty,
    UINT: wxpg.UIntProperty,
    FLOAT: wxpg.FloatProperty,
    MULTCHOICE: wxpg.EnumProperty,
    DIRECTORY: wxpg.DirProperty,
}

PROPERTY_TYPE_DEFAULT = {
    BOOLEAN: False,
    STRING: "",
    INT: 0,
    UINT: 0,
    FLOAT: 0.0,
    MULTCHOICE: "",
    DIRECTORY: "",
}

PROPERTY_VALIDATORS = {
    INT: MaxMinValidator,
    UINT: MaxMinValidator,
    FLOAT: MaxMinValidator,
    DIRECTORY: DirValidator,
}


TEXT_COLOUR_VALID = (0, 166, 90)
TEXT_COLOUR_WARN = (243, 156, 18)
TEXT_COLOUR_FAIL = (221, 75, 57)

settings = Settings()

_EVT_PUMP_COMPLETE = wx.NewEventType()
EVT_PUMP_COMPLETE = wx.PyEventBinder(_EVT_PUMP_COMPLETE, 1)

_EVT_PUMP_PROGRESS = wx.NewEventType()
EVT_PUMP_PROGRESS = wx.PyEventBinder(_EVT_PUMP_PROGRESS, 1)

_EVT_PUMP_STARTING = wx.NewEventType()
EVT_PUMP_STARTING = wx.PyEventBinder(_EVT_PUMP_STARTING, 1)

_EVT_PUMP_LOG = wx.NewEventType()
EVT_PUMP_LOG = wx.PyEventBinder(_EVT_PUMP_LOG, 1)


_EVT_VALIDATION_COMPLETE = wx.NewEventType()
EVT_VALIDATION_COMPLETE = wx.PyEventBinder(_EVT_VALIDATION_COMPLETE, 1)


class PumpEvent(wx.PyCommandEvent):
    """Event to signal that a count value is ready"""

    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        super().__init__(etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value


class BasePump(wx.Panel):
    """Base class for all first party & user defined Pump Types.

    The current config options are stored in dictionary called `state` which is
    updated when any config option is changed by the user.  Likewise, when the
    state is updated by the program (e.g. when loading from config file), the
    controls will be updated to reflect the current state.


    The state dictionary is a dictionary of dictionaries with the following
    form:
    {
        # Name displayed to user for this config section
        'SectionName': {

            # what is this section named in the configuration options
            'config_name': 'DQA3Reader',

            # Most state sections will only have a single subsection however,
            # some sections will have multiple subsections. For example, when
            # you are configuring multiple units for a pump each of which will
            # need to have say a mapping from the DQA3 database name to the
            # QATrack name
            'subsections': [

                # each subsection consists of a list of dicts of a config_name
                # and it's current value
                [
                    {
                        'config_name': 'host',
                        'value': 'localhost'
                    },
                ]
            ]
        },
    }
    """

    # All pumps have some common options which are defined by the BASE_CONFIG
    BASE_CONFIG = [
        {
            'name': 'Pump',
            'multiple': False,
            'fields': [
                {
                    'name': 'type',
                    'type': STRING,
                    'required': True,
                    'readonly': True,
                    'help': "Enter the type of Pump this is.",
                },
                {
                    'name': 'name',
                    'type': STRING,
                    'required': True,
                    'readonly': True,
                },
                {
                    'name': 'interval (s)',
                    'type': INT,
                    'required': True,
                    'help': "Enter how often this Pump should run in seconds.",
                    'default': 300,
                    'validation': {
                        'max': 24 * 60 * 60,
                        'min': 1,
                    }
                },
                {
                    'name': 'log level',
                    'type': MULTCHOICE,
                    'choices': 'get_log_level_choices',
                    'required': False,
                    'help': "Enter the logging level for this Pump",
                    'default': 'info',
                },
                {
                    'name': 'active',
                    'type': BOOLEAN,
                    'required': False,
                    'help': "Enable or disable this Pump",
                    'default': True,
                },
            ]
        },
    ]

    CONFIG = []

    def __init_subclass__(cls, **kwargs):
        """When a subclass of this class is created, register it as a pump type"""
        register_pump_type(cls)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.Bind(EVT_VALIDATION_COMPLETE, self.OnValidationComplete)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

    def configure(self, pump_type, name, state=None):
        """Configure this pump window.  If state is passed then those config
        options will be set.  Otherwise the default configuration will be
        used"""

        # a couple of useful variables for talking to application
        self.app = self.GetTopLevelParent()
        self.parent = self.GetParent()

        self.pump_type = pump_type
        self.name = name

        # Pump is in a dirty sate while configuring
        self.dirty = True

        # setup UI
        self.layout()

        # Set the validation order of sections based on their dependencies
        self.set_dependencies()

        # input state was null which means this pump was not loaded from a
        # config file
        self.is_new = state is None

        # first set up state with default values
        self.state = self.state_from_config()
        if state:
            # and now update with saved state if necessary
            self._update_state(state)

        # ensure the controls match the current state
        self.update_controls_from_state()

        # list of lists of sections that need to to be validated. For example if we have
        # self.validation_stacks = [
        #     ['section 4', 'section 5'],
        #     ['section 3', 'section 2'],
        #     ['section1']
        # ]
        # then a thread would be created to validate section 1, once that was
        # complete, then 2 threads to validate sections 2 & 3, and once those were complte
        # finally 2 threads to validate section 4 & 5.  This order is based on which
        # sections are dependent on the others
        self.validation_stack = []
        self.validation_queue = Queue()
        self.most_recent_validation_group = {s: None for s in self.dependencies.keys()}

        # the sections which currently have validation threads running (poppped off the validation_stack)
        self.sections_currently_validating = set()

        # run validation based on initial state
        self.validate_all()

        # if this is a new pump then it is dirty by definition. Otherwise
        # it was loaded from a config file and hence is not dirty
        self.set_dirty(self.is_new)

        # Call the Base classes setup method to do any post config setup required
        self.setup()

    def setup(self):
        """Override this method to do any custom setup you want (e.g. setting
        properties, precomputing values etc)."""
        pass

    def _update_state(self, new_state):
        """Update self.state by merging in the state dictionary contained in new_state

        Note, this is method has lots of nesting and is tough to wrap your head around.
        Sorry future debuggers :( Room for improvment...
        """

        # iterate over the current state and update it from the input state.
        # For information about structure of state see this class' doc string
        for section in self.state.keys():

            # this can happend when loading an old config file that doesn't
            # have all the options that are available in the current config
            if section not in new_state:
                continue

            new_section_state = new_state[section]

            # make sure there are enough subsections to handle state
            nsubs = len(new_section_state['subsections'])

            # copy the fields for the first subsection and then create enough
            # subsections to handle all the subsections defined in the new state
            sub_fields = lambda: copy.deepcopy(self.state[section]['subsections'][0])  # noqa: E731
            self.state[section]['subsections'] = [sub_fields() for _ in range(nsubs)]

            # iterate over new states subsections and update the current state
            for idx, new_subsection in enumerate(new_section_state['subsections']):

                # iterate over fields in the current states corresponding subsection
                for current_field_state in self.state[section]['subsections'][idx]:

                    # iterate over fields in the new state
                    for new_field_state in new_subsection:

                        # and if we found the right field to update
                        if new_field_state['config_name'] == current_field_state['config_name']:

                            # then update all the current field values
                            for k, v in current_field_state.items():
                                current_field_state[k] = new_field_state.get(k, v)

    @property
    def config(self):
        """returns ordered list of configuration sections"""
        return self.BASE_CONFIG + self.CONFIG

    @property
    def configd(self):
        """returns configuration dictionary of form:

        {
            'Section Name': {
                'multiple': True|False,
                'dependencies': [],
                'fields': {
                    field_name: field_config_dict
                }
            }
        }
        """

        cd = {}
        for c in self.config:
            cd[c['name']] = {
                'multiple': c.get('multiple', False),
                'dependencies': c.get('dependencies', []),
                'fields': {f['name']: f for f in c['fields']}
            }

        return cd

    def state_from_config(self):
        """
        Set the initial state based on the default configuration.

        Unifying the state and config dictionaries might simplify things
        """

        state = {}

        for config_section in self.config:
            state[config_section['name']] = {
                'config_name': config_section['name'],
                'subsections': [],
            }
            subsection = self.state_fields_from_subsection(config_section)

            state[config_section['name']]['subsections'].append(subsection)

        return state

    def state_fields_from_subsection(self, config_section):
        """Convert the config_section fields into state fields"""
        fields = []
        for field in config_section['fields']:
            fields.append(self.state_field_from_field_conf(config_section['name'], field))
        return fields

    def state_field_from_field_conf(self, section, field_conf):
        """Convert a single config field into a state field including setting
        default values"""

        # handle pump name and type differently since they're not editable
        if section == 'Pump' and field_conf['name'] == 'type':
            value = self.pump_type
        elif section == 'Pump' and field_conf['name'] == 'name':
            value = self.name
        else:
            # If there is a default set for the config option use it,
            # otherwise use the default for the field type
            value = field_conf.get("default", PROPERTY_TYPE_DEFAULT[field_conf['type']])

        return {
            'config_name': field_conf['name'],
            'value': value,
        }

    def layout(self):
        """Main setup method. Should only be called once. Handles laying everything
        out and adding all of the property grids."""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.create_controls()
        self.create_grid_panel()
        self.SetSizerAndFit(self.main_sizer)

    def create_controls(self):
        """Create delete/save/reset controls and add them to the window"""

        self.control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.control_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.delete = wx.Button(self, wx.ID_ANY, "Delete", wx.DefaultPosition, wx.DefaultSize, 0)
        self.delete.SetToolTip("Click to remove this Pump")
        self.delete.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.control_sizer.Add(self.delete, 0, wx.ALL, 5)

        self.save = wx.Button(self, wx.ID_ANY, "Save", wx.DefaultPosition, wx.DefaultSize, 0)
        self.save.SetToolTip("Click to save this configuration")
        self.save.Bind(wx.EVT_BUTTON, self.OnSave)
        self.control_sizer.Add(self.save, 0, wx.ALL, 5)

        self.reset = wx.Button(self, wx.ID_ANY, u"Reset", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reset.SetToolTip("Click to reload this configuration from the previously saved state")
        self.reset.Bind(wx.EVT_BUTTON, self.OnReset)
        self.control_sizer.Add(self.reset, 0, wx.ALL, 5)

        self.validate = wx.Button(self, wx.ID_ANY, u"Revalidate", wx.DefaultPosition, wx.DefaultSize, 0)
        self.validate.SetToolTip("Click to force revalidation of all config options")
        self.validate.Bind(wx.EVT_BUTTON, self.OnRevalidate)
        self.control_sizer.Add(self.validate, 0, wx.ALL, 5)

        self.main_sizer.Add(self.control_sizer, 0, wx.EXPAND | wx.ALL, 5)

    def create_grid_panel(self):
        """Handle adding panel and grids"""

        self.grids_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.grids_panel.SetScrollRate(0, 5)
        self.grids_sizer = wx.BoxSizer(wx.VERTICAL)
        self.create_grids()
        self.grids_panel.SetSizer(self.grids_sizer)
        self.grids_panel.Layout()
        self.grids_sizer.Fit(self.grids_panel)
        self.main_sizer.Add(self.grids_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.Layout()

    def create_grids(self):
        """Add required configuration grids to main sizer"""

        self.grids = {}  # lookup of PropertyGrid by config name
        self.grids_by_id = {}  # allow lookup of PropertyGrid by wx ID
        self.grid_configs = {}  # get the config section for a property grid by it's ID
        self.grid_validators = {}  # get validator for property grid by ID
        self.grid_validation_text = {}  # get static text control for a property grid by ID
        self.grid_validation_state = {}  # get validation state for a property grid by ID
        self.toolbar_buttons = {}

        # iterate over each config section and create a property grid for it
        for config_section in self.config:

            # static box sizer to display the config sections name
            sb = wx.StaticBox(self.grids_panel, wx.ID_ANY, config_section['name'] + " Configuration")
            config_sizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

            # if we will have multiple subsections then we need a toolbar for
            # adding/removing subsections
            grid_style = wxpg.PG_SPLITTER_AUTO_CENTER

            grid = wxpg.PropertyGridManager(sb, style=grid_style, size=(-1, -1))
            grid.SetValidationFailureBehavior(
                wxpg.PG_VFB_MARK_CELL |  # show cell as red colour
                wxpg.PG_VFB_STAY_IN_PROPERTY |  # don't leave the grid property unless it is valid
                wxpg.PG_VFB_SHOW_MESSAGE_ON_STATUSBAR  # show the validation error in the status bar
            )

            # hook the mousewheel event to override the default behaviourt. See OnGridScroll for details
            grid.GetGrid().Bind(wx.EVT_MOUSEWHEEL, self.OnGridScroll)

            grid.AddPage(config_section['name'])

            # bind grid events
            grid.Bind(wxpg.EVT_PG_CHANGED, self.OnGridChanged)
            grid.Bind(wxpg.EVT_PG_CHANGING, self.OnGridChanging)

            # configure validation
            validator = config_section.get("validation", "default_section_validator")
            self.grid_validators[grid.GetId()] = getattr(self, validator)
            self.grid_validation_state[grid.GetId()] = False, "Not Validated Yet"
            validation_text = wx.StaticText(sb, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT)
            self.grid_validation_text[grid.GetId()] = validation_text
            config_sizer.Add(validation_text, 0, wx.EXPAND | wx.ALL, 5)

            if config_section.get('multiple'):
                actions = [('add', 'plus-24', f"Click To add another {config_section['name']}"),
                           ('rem', 'minus-24', f"Click to remove currently selected {config_section['name']}")]
                but_sizer = wx.BoxSizer(wx.HORIZONTAL)
                for action, icon, help_text in actions:
                    img = wx.Bitmap(settings.ico(icon), wx.BITMAP_TYPE_PNG)
                    but = wx.BitmapButton(
                        sb, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW | 0
                    )
                    but.SetBitmap(img)
                    but_sizer.Add(but, 0, wx.ALL, 5)
                    but.Bind(wx.EVT_BUTTON, self.OnMultipleButton)
                    self.toolbar_buttons[but.GetId()] = {'action': action, 'grid_id': grid.GetId()}
                config_sizer.Add(but_sizer, 0, wx.EXPAND | wx.ALL, 5)

            config_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)

            # add grids to lookups for use elsewhere
            self.grids[config_section['name']] = grid
            self.grids_by_id[grid.GetId()] = grid
            self.grid_configs[grid.GetId()] = config_section

            self.grids_sizer.Add(config_sizer, 0, wx.EXPAND | wx.ALL, 5)

    def update_controls_from_state(self):
        """Take the existing state dictionary and set up all the controls for it"""

        for section, state in self.state.items():

            grid = self.grids[section]
            # remove all existing props from the grid since we will be re-configuring them
            self.clear_grid(grid)
            page = grid.GetCurrentPage()

            conf = self.configd[section]
            for idx, subsection in enumerate(state['subsections']):

                # when there is multiple sub sections add a sub section number
                # to its displayed name
                sub_name = section if not conf['multiple'] else f"{section} #{idx + 1}"

                # Add a "Category" header to the grid for each subsection
                cat = wxpg.PropertyCategory(sub_name)
                cat.SetClientData({
                    'is_category': True,
                    'field_name': sub_name,
                    'property_name': sub_name,
                    'field_idx': None,
                    'subsection_idx': idx,
                })
                page.Append(cat)

                # for each field in a subsection, add a new grid property to the grid
                for field_idx, field_state in enumerate(subsection):

                    try:
                        field_conf = conf['fields'][field_state['config_name']]
                    except KeyError:
                        # can happen when loading a config file with a field that is
                        # no longer part of the configuration fields
                        continue

                    # create a property of the correct datatype for this field and add
                    # it to the grid
                    has_dependencies = len(self.dependencies[section]) > 0
                    field_prop = self.create_grid_property(
                        grid, field_conf, field_state['value'], field_idx, idx, conf['multiple'], has_dependencies,
                    )
                    page.Append(field_prop)

        self.resize_grids()

    def OnDelete(self, event):
        """Handle user asking to delete this pump"""
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to permanently delete this Pump",
            f"Delete {self.name} Pump?",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION,
        )
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.delete_pump()

    def delete_pump(self):
        """Remove this pump.  This will call up to the parent to tell that user
        wants to delete this pump"""
        self.parent.delete()

    def OnSave(self, event):
        """Handle user asking to save this pump"""
        self.save_pump()

    def save_pump(self):
        """Tell the parent to save our state.  If it succeeds set the dirty state appropriately"""
        saved = self.parent.save()
        if saved:
            self.is_new = False
            self.set_dirty(False)

    def OnReset(self, event):
        """Handle user asking to reset this pump"""

        if self.is_new:
            msg = "Are you sure you want to reset this pump to its default state?"
        else:
            msg = "Are you sure you want to reset this pump to its currently saved state?"

        dlg = wx.MessageDialog(
            self, msg, "Reset Pump?",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION
        )
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.reset_pump()

    def reset_pump(self):
        """Reset pump to default state if it is a new pump, or to previously saved state if it was an existing pump"""

        if self.is_new:
            state = self.state_from_config()
        else:
            state = self.parent.reset()

        if state:
            self.state = state
            self.update_controls_from_state()
            self.validate_all()
            self.set_dirty(False)
            self.Layout()

    def OnRevalidate(self, event):
        self.validate_all()

    def OnGridScroll(self, evt):
        """
        Since we always show all properties in the grid, we can pass grid
        scroll events onto the ScrolledWindow which makes for a nice UX when
        using the mouse wheel.

        Note that the GetScrollPos method only ever returns 0 or 1 so can't
        be used (see http://wxpython-users.1045709.n5.nabble.com/GetScrollPos-return-0-or-1-with-wx-SHOW-SB-NEVER-td5724832.html).
        """  # noqa: E501

        pos = self.grids_panel.GetViewStart()[1]
        direction = 1 if evt.GetWheelRotation() < 0 else - 1
        offset = self.grids_panel.GetScrollPixelsPerUnit()[1]
        new_pos = max(0, pos + direction * offset)
        self.grids_panel.Scroll(0, new_pos)

    def OnMultipleButton(self, evt):
        """Handle adding & removing subsection controls for multi valued config sections"""

        button = evt.GetEventObject()
        tb_data = self.toolbar_buttons[button.GetId()]
        grid = self.grids_by_id[tb_data['grid_id']]
        action = tb_data['action']

        # count categories
        page = grid.GetCurrentPage()
        nsections = len(set(prop.GetParent() for prop in page.Properties))

        config = self.grid_configs[grid.GetId()]
        state_section = self.state[config['name']]
        selection = page.GetSelection()
        if action == 'rem' and selection and nsections > 1:
            sub_idx = selection.GetClientData()['subsection_idx']
            state_section['subsections'].pop(sub_idx)
            self.update_controls_from_state()
            grid.ClearSelection()
        elif action == 'add':
            state_section['subsections'].append(self.state_fields_from_subsection(config))
            self.update_controls_from_state()

            # need to set choices for this section since the properties in
            # the new subsection
            self.update_grid_section_choices(self.grids[config['name']], config['name'])

    def OnGridChanging(self, evt):
        """Do our field by field validation here since PropertyGridManager's
        property validation doesn't work in the same way as PropertyGrid. See
        note on BaseValidator."""

        prop = evt.GetProperty()
        self.old_value = prop.GetValue()
        new_value = evt.GetPropertyValue()
        validator = prop.GetValidator()

        if validator and not validator.ValidateValue(new_value):
            evt.Veto()
        else:
            evt.Skip()

    def OnGridChanged(self, evt):
        """Event handler for anytime a property is changed by user"""

        if evt.GetPropertyValue() == self.old_value:
            return

        self.set_dirty(True)

        grid = evt.GetEventObject()
        grid_id = grid.GetId()

        # update the relevant state field
        config = self.grid_configs[grid_id]
        prop = evt.GetProperty()
        prop_data = prop.GetClientData()
        subsection_idx = prop_data['subsection_idx']
        section = self.grid_configs[grid_id]['name']
        field_idx = prop_data['field_idx']
        field = config['fields'][field_idx]

        value = evt.GetPropertyValue()
        if field['type'] == MULTCHOICE:
            # mult choice GetPropertyValue() returns an integer but we want string
            value = prop.GetValueAsString()

        self.state[config['name']]['subsections'][subsection_idx][field_idx]['value'] = value

        levels = dependencies.generate_validation_level_subset(section, self.dependencies)
        self.add_levels_to_queue(levels)

    def make_validation_group_id(self):
        """Return a unique string to identify a validation group"""
        return str(uuid4())

    def run_grid_validators(self, group):
        group_id, levels = group

        # first display in UI that we are going to validate some grids
        for level in levels:
            for section in level:
                grid = self.grids[section]
                grid_id = grid.GetId()
                self.grid_validation_state[grid_id] = None, "Currently validating..."
                self.update_grid_validation_message(grid_id, None, "Currently validating...")

        # Run all the validator threads in this parent thread so we can ignore
        # the results from validators which were started before the most recent
        # user input
        validation_thread = threading.Thread(
            target=self._run_grid_validators,
            args=(group,),
            daemon=True,
        )
        validation_thread.start()

    def _run_grid_validators(self, group):

        group_id, levels = group

        result_set = {
            'group_id': group_id,
            'results': []
        }
        for level in levels:

            threads = []

            # container to hold results from validation threads
            thread_results = {}

            for section in level:

                self.log_debug(f"Starting validation for section {section} {group_id}")

                grid = self.grids[section]
                grid_id = grid.GetId()
                validation_data = self.get_validation_data_for_grid(grid)
                validator = self.grid_validators[grid_id]

                t = threading.Thread(
                    target=self._run_validation_thread,
                    args=(grid_id, section, validator, validation_data, thread_results),
                    daemon=True,
                )
                t.start()
                threads.append((section, t))

            # wait for all threads to finish and set the results
            for section, t in threads:
                t.join()
                result_set['results'].append(thread_results[section])

        # tell main thread validation is finished
        evt = PumpEvent(_EVT_VALIDATION_COMPLETE, wx.ID_ANY, result_set)
        wx.PostEvent(self, evt)

    def _run_validation_thread(self, grid_id, section, validator, validation_data, thread_results):
        """Wrapper around the pumps validator to set results required for updating UI later"""

        try:
            valid, msg = validator(validation_data)
            exception = None
        except Exception:
            valid, msg = False, "Invalid Validator Implementation"
            exception = traceback.format_exc()

        data = {
            'valid': valid,
            'message': msg,
            "exception": exception,
            "section": section,
            'grid_id': grid_id,
        }
        thread_results[section] = data

    def _grid_validator(self, section, grid_id, validator, validation_data):

        try:
            valid, msg = validator(validation_data)
            exception = None
        except Exception:
            valid, msg = False, "Invalid Validator Implementation"
            exception = traceback.format_exc()

        data = {
            'valid': valid,
            'message': msg,
            "exception": exception,
            "section": section,
            'grid_id': grid_id,
        }
        return data

    def OnValidationComplete(self, evt):
        """After any validator thread finishes, set the grid validation state,
        and updated any dynamic choices which were dependent on this
        validator"""

        result_set = evt.GetValue()
        group_id = result_set['group_id']
        for result in result_set['results']:
            if result['exception']:
                self.logger.critical(result['exception'])

            if self.most_recent_validation_group[result['section']] != group_id:
                self.log_debug(
                    f"Ignoring results from group {group_id} for "
                    "section {result['section']} because they are not the latest"
                )
                continue

            self.log_debug(
                f"Using results from group {group_id} for "
                "section {result['section']} because they are the most recent"
            )

            self.grid_validation_state[result['grid_id']] = result['valid'], result['message']

            self.update_grid_validation_message(result['grid_id'], result['valid'], result['message'])
            self.update_grid_status(result['section'])

    def resize_grids(self):
        """Set the grid sizes so that no scrollbars are required"""

        for section, state in self.state.items():
            g = self.grids[section]
            size = g.GetBestSize()
            nrows = len(list(g.Items))
            row_height = g.GetGrid().GetRowHeight() + g.GetGrid().GetVerticalSpacing()
            tool_bar_height = (g.ToolBar.GetSize()[1]) if g.ToolBar else 0
            height = nrows * row_height + tool_bar_height
            g.SetSize((size[0], height))
            g.SetMinSize((size[0], height))

        self.Layout()

    def clear_grid(self, grid):
        """Remove all properties from input grid"""
        while grid.GetFirst():
            grid.DeleteProperty(grid.GetFirst())

    def create_grid_property(self, grid, field, value, field_idx, subsection_idx, multiple, has_dependencies):
        """Create a grid property with the correct property type for a configuration field"""

        ftype = field.get('type', STRING)
        label = field.get('label', field['name'].title())
        fname = field['name'] if not multiple else f"{field['name']} #{subsection_idx}"

        # set up the kwargs to pass to the PropertyType class constructor and
        # then construct the property
        PropertyTypeClass = PROPERTY_TYPES[ftype]
        kwargs = {'label': label, 'name': fname, 'value': value}
        if ftype == MULTCHOICE:

            if has_dependencies:
                # Since the choices for this field may depend on other grids,
                # the choices will have to be set after those dependencies are
                # validated.  Right now set placeholder choices/value so that
                # we can keep track of what the value should be
                choices, idx = [value], 0
            else:
                # these choices are not dependent on other grids so we can
                # grab them now and save having to do them after validation
                choices = self.get_field_choices(field)
                idx = choices.index(value) if value in choices else 0

            kwargs['labels'] = choices
            kwargs['value'] = idx

        prop = PropertyTypeClass(**kwargs)

        # set special control types where appropritate
        if ftype in [INT, UINT]:
            grid.SetPropertyEditor(prop, "SpinCtrl")

        # add help text to the property when it is defined in the config
        grid.SetPropertyHelpString(prop, field.get("help", "No help available"))

        # grab the validation class for this property type and
        # add validation info if available
        ValidatorClass = PROPERTY_VALIDATORS.get(ftype)
        if ValidatorClass:
            validation_info = field.get('validation', {})
            prop.SetValidator(ValidatorClass(validation_info))

        # set readonly state
        prop.ChangeFlag(wxpg.PG_PROP_READONLY, field.get('readonly', False))

        # add data to the property that we can use in events
        prop.SetClientData({
            'is_category': False,
            'field_name': field['name'],
            'field_type': ftype,
            'property_name': fname,
            'field_idx': field_idx,
            'subsection_idx': subsection_idx,
        })
        return prop

    def get_field_choices(self, field):
        """Lookup choices for a multiple choice field.  If choices is set to a
        string, QCPump will assume it is a method name on the Pump and call it
        to get the choices dynamically"""
        choices = field.get('choices', [])
        if isinstance(choices, str):
            choices = getattr(self, choices)()
        return choices

    def get_log_level_choices(self):
        """Return the available log level choices for the log level multiple choice test"""
        return ['debug', 'info', 'warning', 'error', 'critical']

    def default_section_validator(self, grid):
        """Default validator always returns True"""
        return True, "OK"

    def set_dependencies(self):
        self.dependencies = {s: set(f['dependencies']) for s, f in self.configd.items()}
        self.validation_levels = dependencies.generate_validation_levels(self.dependencies)

    def validate_all(self):
        """Validate all grids/sections"""

        levels = copy.deepcopy(self.validation_levels)
        self.add_levels_to_queue(levels)

    def add_levels_to_queue(self, levels):
        print("Adding levels to queue", levels)
        group_id = self.make_validation_group_id()
        for level in levels:
            self.most_recent_validation_group.update({section: group_id for section in level})
        self.validation_queue.put((group_id, levels))

    def get_validation_data_for_grid(self, grid):
        """Return a dict of form {field_name: value} for all properties from a grid"""
        validation_data = {}
        for p in grid.Properties:
            data = p.GetClientData()
            val = p.GetValue()
            if data['field_type'] == MULTCHOICE:
                val = p.GetValueAsString()
            validation_data[data['field_name']] = val

        return validation_data

    def update_grid_validation_message(self, grid_id, valid, msg, do_layout=True):
        validation_text = self.grid_validation_text[grid_id]
        if valid is None:
            col = TEXT_COLOUR_WARN
        elif valid:
            col = TEXT_COLOUR_VALID
        else:
            col = TEXT_COLOUR_FAIL

        validation_text.SetForegroundColour(col)
        validation_text.SetLabel(f"Validation: {msg}")
        parent = validation_text.GetParent()
        validation_text.Wrap(parent.GetSize()[0])

        if valid is False:
            section_name = self.grid_configs[grid_id]['name']
            self.log_debug(f"Validation Error for {section_name}: {msg}")

        if do_layout:
            # layout call necesary for static text resize so validation text
            # doesn't overlay grid
            self.Layout()

    def update_grid_status(self, section):
        """
        Checks grid section to see if its dependencies are met and enables/disables
        the grid accordingly.
        """

        grid = self.grids[section]
        deps_not_completed = self.incomplete_dependencies_of_section(section)
        grid.GetParent().Enable(len(deps_not_completed) == 0)

        if deps_not_completed:
            validation_text = self.grid_validation_text[grid.GetId()]
            validation_text.SetForegroundColour(TEXT_COLOUR_WARN)
            s = ['Config Sections', 'Config Section'][len(deps_not_completed) == 1]
            validation_text.SetLabel(f"Please complete {s} {', '.join(deps_not_completed)} to enable this section")

    def incomplete_dependencies_of_section(self, section):
        """return list of dependencies for input section which are not complete/valid"""
        deps_not_completed = []
        for dep in self.dependencies[section]:
            dep_grid_id = self.grids[dep].GetId()
            valid, msg = self.grid_validation_state[dep_grid_id]
            if not valid:
                deps_not_completed.append(dep)
        return deps_not_completed

    def update_grid_section_choices(self, grid, section_name):
        """Iterate over all properties in a grid and update choices for
        all properties which have choices.  This is necessary because the
        choices can be set dynamically based on other sections"""

        # For grids with multiple subsections we can cache the choices so
        # that we don't need to get them for each subsection
        choice_cache = {}

        for prop in grid.Properties:

            field_name = prop.GetClientData()['field_name']
            field_config = self.configd[section_name]['fields'][field_name]

            is_not_multiple_choice = field_config['type'] != MULTCHOICE
            if is_not_multiple_choice:
                continue

            # get the currently selected choice so we can reselect it after if
            # it is present in the new chocies
            cur_selected = prop.GetValueAsString()

            try:
                new_choices = choice_cache[field_config['name']]
            except KeyError:
                new_choices = self.get_field_choices(field_config)
                choice_cache[field_config['name']] = new_choices

            prop.SetChoices(wxpg.PGChoices(new_choices))

            # and select appropriate choices
            if cur_selected in new_choices:
                # reselect previous choice if possible
                prop.SetValue(new_choices.index(cur_selected))
            else:
                # previous selection not available so set to default if possible
                default = field_config.get('default', "")
                val = new_choices.index(default) if default in new_choices else None
                prop.SetValue(val)

    def get_config_values(self, section):
        """
        Takes the name of a configuration section and returns a list of all the
        currently set values from each of the configuration subsections (i.e.
        this will return a list of length 1 if it is not a multiple value
        config section
        """
        if section not in self.state:
            return []

        vals = []
        for sub in self.state[section]['subsections']:
            vals.append({f['config_name']: f['value'] for f in sub})
        return vals

    def get_config_value(self, section, field, subsection_index=None):
        """
        Takes the name of a configuration section, a field name, and optionally
        a subsection index and returns a list of all the currently set values
        for that field from each of the configuration subsections.

        For a non multiple value section the value of the field from the single
        subsection will be returned.

        For a multiple value section a list of values for that field will be
        returned, unless subsection_index is non None. In that case the value
        from the given subsection will be returned.
        """

        vals = []
        for sub in self.state[section]['subsections']:
            for f in sub:
                if f['config_name'] == field:
                    vals.append(f['value'])

        if subsection_index is None and len(vals) == 1:
            return vals[0]
        elif subsection_index is not None:
            return vals[subsection_index]

        return vals

    def get_pump_path(self, filename=""):
        """Return file path where this pump type is defined.  If filename is
        defined then it will be a file path, otherwise it will be the
        directory."""
        p = Path(inspect.getmodule(self).__file__).parent.absolute()
        if filename:
            p /= filename
        return p.absolute()

    def set_dirty(self, dirty):
        """Set the dirty (unsaved) state"""
        self.dirty = dirty
        self.reset.Enable(dirty)
        self.parent.set_dirty(dirty)

    @property
    def valid(self):
        """A pump is valid if and only if each of its property grids is currently valid"""
        return all(valid for valid, __ in self.grid_validation_state.values())

    @property
    def active(self):
        """Is this pump marked as active?"""
        return self.get_config_value("Pump", "active")

    def should_terminate(self):
        """Should the current pumping operation be stopped?"""
        return self.kill_event.is_set()

    def terminate(self):
        """Set the kill event"""
        self.kill_event.set()

    def update_progress(self, progress, msg):
        """Send a message to the GUI that we want the progress bar updated"""
        data = {
            'name': self.name,
            'progress': progress,
            'message': msg,
        }
        evt = PumpEvent(_EVT_PUMP_PROGRESS, wx.ID_ANY, data)
        wx.PostEvent(self.parent, evt)

    def pump_complete(self):
        """Send event indicating that this pumping iteration is complete"""
        evt = PumpEvent(_EVT_PUMP_COMPLETE, wx.ID_ANY)
        wx.PostEvent(self.parent, evt)

    def run(self, kill_event):
        """Run the actual pump. Note this function runs in its own thread"""
        self.kill_event = kill_event
        if not self.should_terminate():
            self.update_progress(0, "Starting to pump...")
            try:
                # pump can return a message to show with the progress bar or
                # else just use a default message
                pump_msg = self.pump() or "Pump Complete"
                self.update_progress(100, pump_msg)
            except Exception:
                self.log_critical(traceback.format_exc())

            # tell application this pump is finished
            self.pump_complete()

    def OnIdle(self, evt):
        """Check if there's any validation to do"""
        validation_waiting = self.validation_queue.qsize() > 0
        if validation_waiting:
            validation_group = self.validation_queue.get()
            self.run_grid_validators(validation_group)

    def pump(self):
        raise NotImplementedError("You must implement this in all subclasses")

    def log(self, level, msg):
        """Send a log message to the application.  We use Events here because
        the pumps will be running in their own threads"""

        data = {
            'name': self.name,
            'level': level,
            'message': msg,
        }
        log_level_str = self.get_config_value("Pump", "log level")
        pump_log_level = get_log_level(log_level_str)
        if level >= pump_log_level:
            evt = PumpEvent(_EVT_PUMP_LOG, wx.ID_ANY, data)
            wx.PostEvent(self.parent, evt)

    def log_debug(self, msg):
        """convenience method for sending a debug message"""
        self.log(logging.DEBUG, msg)

    def log_info(self, msg):
        """convenience method for sending an info message"""
        self.log(logging.INFO, msg)

    def log_warning(self, msg):
        """convenience method for sending a warning message"""
        self.log(logging.ERROR, msg)

    def log_error(self, msg):
        """convenience method for sending an error message"""
        self.log(logging.ERROR, msg)

    def log_critical(self, msg):
        """convenience method for sending a critical message"""
        tb = traceback.format_exc()
        if msg != tb:
            msg += f"\n{tb}"
        self.log(logging.CRITICAL, msg)
