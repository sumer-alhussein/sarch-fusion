import traceback
from typing import List
import adsk.cam
from sys import prefix
import adsk.core
import adsk.fusion
import os
from ...lib import fusion360utils as futil
from ... import config


import http.client
import json

import re

app = adsk.core.Application.get()
ui = app.userInterface

SAFE_COMPONENT_NAME_PATTERN = r'\w+_\d{2,3}$'
SAFE_PROJECT_NAME_PATTERN = r'^[A-Za-z]{2}\d{1,2}_\d{3,5}$'

# TODO *** Define the categories and sub-categories for the command. ***
# This is used to create a drop-down list in the command dialog.
# Categories and Sub-Categories type


class Category:
    def __init__(self, name, id=None, description=None, subcategories=None):
        self.id = id
        self.name = name
        self.description = description
        self.subcategories = subcategories or []

    def add_subcatogries(self, name, id):
        self.subcategories.append(
            {'id': id, 'name': name})


CATEGORIES = [
    {
        'id': 'WND',
        'name': 'Windows',
        'description': 'Windows',
        'subcategories': [
            {
                'id': 'W1',
                'name': 'Indoor/ outdoor window',
            },
            {
                'id': 'W2',
                'name': 'Outdoor/ outdoor window',
            },
            {
                'id': 'W3',
                'name': 'Indoor/ indoor window',
            },
            {
                'id': 'RWN',
                'name': 'Rowshan',
            },
            {
                'id': 'MSH',
                'name': 'Mashrabia',
            },
            {
                'id': 'RGN',
                'name': 'Wrought Iron',
            },
        ]
    },
    {
        'id': 'DRS',
        'name': 'Doors',
        'description': 'Doors',
        'subcategories': [
            {
              'id': 'D1',
              'name': 'Indoor/ outdoor door',
            },
            {
                'id': 'D2',
                'name': 'Outdoor/ outdoor door',
            },
            {
                'id': 'D3',
                'name': 'Indoor/ indoor door',
            },
        ]
    },
    {
        'id': 'CBN',
        'name': 'Cabinets',
        'description': 'Cabinets',
        'subcategories': [
            {
                'id': 'C1',
                'name': 'Indoor Cabinet',
            },
            {
                'id': 'C2',
                'name': 'Outdoor Cabinet',
            },
            {
                'id': 'CE',
                'name': 'Electrical Cabinet',
            },
        ]
    },
    {
        'id': 'WDB',
        'name': 'Wooden Beams and Lintels',
        'description': 'Wooden Beams and Lintels',
        'subcategories': [
            {
              'id': 'B1',
              'name': 'Wooden Beam',
            },
            {
                'id': 'B2',
                'name': 'Wooden Plank',
            },
        ]
    },
    {
        'id': 'DCR',
        'name': 'Decorative Elements',
        'description': 'Decorative Elements',
        'subcategories': [
            {
              'id': 'PR',
              'name': 'Decorative Plaster / Stucco Element',
            },
            {
                'id': 'WD',
                'name': 'Decorative Wood Element',
            },
        ]
    }, {
        'id': 'HDR',
        'name': 'Handrails',
        'description': 'Handrails',
        'subcategories': [
            {
              'id': 'H1',
              'name': 'Indoor Handrail',
            },
            {
                'id': 'H2',
                'name': 'Outdoor Handrail',
            },
        ]
    }, {
        'id': 'STR',
        'name': 'Stairs',
        'description': 'Stairs',
        'subcategories': [
            {
              'id': 'S1',
              'name': 'Indoor Stair',
            },
            {
                'id': 'S2',
                'name': 'Outdoor Stair',
            },
        ]
    }, {
        'id': 'CLM',
        'name': 'Columns',
        'description': 'Columns',
        'subcategories': [
            {
              'id': 'WD',
              'name': 'Wooden Column',
            },
            {
                'id': 'DR',
                'name': 'Decorative Column',
            },
        ]
    }, {
        'id': 'ARY',
        'name': 'Arayes',
        'description': 'Arayes',
        'subcategories': [
            {
              'id': 'A1',
              'name': 'Indoor Arayes',
            },
            {
                'id': 'A2',
                'name': 'Outdoor Arayes',
            },
        ]
    }

]

categories: list[Category] = []
for category_data in CATEGORIES:
    category = Category(
        name=category_data['name'], id=category_data['id'], description=category_data['description'])
    for subcategory_data in category_data['subcategories']:
        category.add_subcatogries(
            name=subcategory_data['name'], id=subcategory_data['id'])
    categories.append(category)


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Rename'
CMD_Description = 'Rename selected Components'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
# WORKSPACE_ID = 'FusionSolidEnvironment'
# PANEL_ID = 'SolidScriptsAddinsPanel'
# COMMAND_BESIDE_ID = 'ScriptsManagerCommand'
# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'resources', '')
# button_icons = os.path.join(ICON_FOLDER, 'buttons')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(
            PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # h = http.client.HTTPSConnection('api.github.com')
    # headers = {'User-Agent': 'Fusion360'}
    # h.request('GET', '/users/autodeskfusion360/repos', '', headers)
    # res = h.getresponse()

    # resBytes = res.read()
    # resString = resBytes.decode('utf-8')
    # resJson = json.loads(resString)

    # futil.log(f'Command Created Event {resJson}')

    _project_name = get_project_name()

    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs

    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    ######################### ? Start My Inputs #########################

    # ? Use Project Name Input
    use_project_name_input = inputs.addBoolValueInput(
        'use_project_name_input', 'Use file name', True, '', True)
    use_project_name_input.tooltip = 'Use the project name as a prefix for the component name.'

    # ? Prefix Text Input
    prefix_input = inputs.addStringValueInput(
        'prefix_input', 'Project name with prefix', f"{_project_name.upper()}")
    prefix_input.tooltip = 'Prefix to component name eg. UC1_999 will create UC1_999_CATEGORY_SUBCATEGORY_1'
    prefix_input.isEnabled = False

    # ? Select Entities Input
    selected_intities_input = inputs.addSelectionInput(
        'selected_intities_input', 'Select components', 'Select components to rename')

    selected_intities_input.addSelectionFilter('Occurrences')
    selected_intities_input.setSelectionLimits(1, 0)

    # ? Categories list
    # Create a drop-down list of categories and sub-categories.
    drop_down_style = adsk.core.DropDownStyles.LabeledIconDropDownStyle
    category_input = inputs.addDropDownCommandInput(
        'category_input', 'Select category', drop_down_style)
    category_input.tooltip = 'Select the category of the components.'

    subcategories_input_listItems = category_input.listItems

    for category in categories:
        subcategories_input_listItems.add(category.name,
                                          False, os.path.join(ICON_FOLDER, f'{category.id}'))

    # ? Sub Categorires
    subcategory_input = inputs.addButtonRowCommandInput(
        'subcategories_input', 'Subcategories', False)
    subcategory_input.isVisible = False

    # ? Force Mode Input
    force_mode_input = inputs.addBoolValueInput(
        'force_mode_input', 'Force mode', True, '', False)
    force_mode_input.tooltip = 'Force mode will override all components names.'

    ######################### ? End My Inputs ###########################

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute,
                      local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged,
                      command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview,
                      command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs,
                      command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy,
                      local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):

    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Get a reference to your command's inputs.

    inputs = args.command.commandInputs
    prefix_input: adsk.core.StringValueCommandInput = adsk.core.StringValueCommandInput.cast(
        inputs.itemById(
            'prefix_input'))
    category_input: adsk.core.DropDownCommandInput = adsk.core.DropDownCommandInput.cast(
        inputs.itemById(
            'category_input'))
    subcategories_input: adsk.core.ButtonRowCommandInput = adsk.core.ButtonRowCommandInput.cast(inputs.itemById(
        'subcategories_input'))
    force_mode_input: adsk.core.BoolValueCommandInput = adsk.core.BoolValueCommandInput.cast(inputs.itemById(
        'force_mode_input'))

    _prefix = prefix_input.value.strip().upper()
    _selected_category = category_input.selectedItem
    _selected_subcategory = subcategories_input.selectedItem
    _category = next(
        (category for category in categories if category.name == _selected_category.name), None)
    _category_id = ''
    if _category:
        _category_id = _category.id

    _subcategory_id = ''

    if _category:
        _subcategory = next(
            (_subcategory for _subcategory in _category.subcategories if _subcategory['name'] == _selected_subcategory.name), None)
        if _subcategory:
            _subcategory_id = _subcategory['id']

    _force_mode = force_mode_input.value
    _selected_intities = ui.activeSelections

    _design: adsk.fusion.Design = adsk.fusion.Design.cast(app.activeProduct)
    _selected_occurrences: List[adsk.fusion.Occurrence] = [
        adsk.fusion.Occurrence.cast(_occ.entity) for _occ in _selected_intities]

    _all_components = _design.allComponents
    # Loop through each selected component

    # This event handler is called when the command needs to compute a new preview in the graphics window.
    counter = 1

    filtered_occurrences = []
    for _occ in _selected_occurrences:
        if isinstance(_occ, adsk.fusion.Occurrence):
            if re.match(SAFE_COMPONENT_NAME_PATTERN, _occ.component.name) and not _force_mode:
                futil.log(
                    f'component name is match and not force mode: {_occ.component.name}')
                futil.log(
                    f'{re.match(SAFE_COMPONENT_NAME_PATTERN, _occ.component.name)}')
                continue
            elif re.search(SAFE_COMPONENT_NAME_PATTERN, _occ.component.name) is None or _force_mode:
                futil.log(
                    f'component name is not match or force mode: {_occ.component.name}')
                futil.log(
                    f'{re.match(SAFE_COMPONENT_NAME_PATTERN, _occ.component.name)}')
                _occ.component.name = '_temp_'
                filtered_occurrences.append(_occ)
            else:
                continue
        else:
            pass
    _all_components_names = [_comp.name for _comp in _all_components]
    for _occ in filtered_occurrences:

        # Get the component from the occurrence
        _component = _occ.component

        while True:
            new_name = f'{_prefix}_{_category_id}_{_subcategory_id}_{counter:02d}'

            if _occ.component.name.startswith(f'{_prefix}_{_category_id}_{_subcategory_id}') and _occ.component.name.split('_')[-1] <= str(counter):
                break

            elif new_name in _all_components_names:
                futil.log(f'component exists in allComponents: {new_name}')
                counter += 1
                continue
            else:
                _component.name = new_name
                futil.log(
                    f'component renamed to {_component.name}')
                break


def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    _project_name = get_project_name()
    changed_input = args.input
    inputs = args.inputs

    use_project_name_input: adsk.core.BoolValueCommandInput = adsk.core.BoolValueCommandInput.cast(inputs.itemById(
        'use_project_name_input'))
    prefix_input: adsk.core.StringValueCommandInput = adsk.core.StringValueCommandInput.cast(
        inputs.itemById(
            'prefix_input'))
    category_input: adsk.core.DropDownCommandInput = adsk.core.DropDownCommandInput.cast(inputs.itemById(
        'category_input'))
    subcategories_input: adsk.core.ButtonRowCommandInput = adsk.core.ButtonRowCommandInput.cast(
        inputs.itemById(
            'subcategories_input'))
    subcategories_input_listItems = subcategories_input.listItems

    if changed_input.id == use_project_name_input.id:
        prefix_input.isEnabled = not use_project_name_input.value
        futil.log(f'prefix_input: {prefix_input.value}')
        if use_project_name_input:
            prefix_input.value = _project_name.upper()

    if changed_input.id == category_input.id:
        if category_input.selectedItem is not None:
            subcategories_input_listItems.clear()
            selected_category = next(
                (category for category in CATEGORIES if category['name'] == category_input.selectedItem.name), None)
            if selected_category is None:
                return
            for subcategory in selected_category['subcategories']:
                _icon = os.path.join(
                    ICON_FOLDER, f'{selected_category["id"]}_{subcategory["id"]}')

                subcategories_input_listItems.add(
                    subcategory['name'], False, _icon, -1)

            subcategories_input.isVisible = True

        else:
            subcategories_input_listItems.clear()
            subcategories_input.isVisible = False
            pass

    # General logging for debug.
    futil.log(
        f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    prefix_input: adsk.core.StringValueCommandInput = adsk.core.StringValueCommandInput.cast(inputs.itemById(
        'prefix_input'))
    category_input: adsk.core.DropDownCommandInput = adsk.core.DropDownCommandInput.cast(inputs.itemById(
        'category_input'))
    subcategories_input: adsk.core.ButtonRowCommandInput = adsk.core.ButtonRowCommandInput.cast(inputs.itemById(
        'subcategories_input'))

    if re.match(SAFE_PROJECT_NAME_PATTERN, prefix_input.value) and category_input.selectedItem is not None and subcategories_input.selectedItem is not None:
        args.areInputsValid = True

    else:
        args.areInputsValid = False


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []


def get_project_name():
    app = adsk.core.Application.get()
    design = app.activeProduct
    dataFile = None
    if design:
        try:
            dataFile = design.parentDocument.dataFile
        except:
            futil.log(f'ERROR: LOCAL CACH, CAN\'T GET FILE NAME')
            pass
    project_name = 'TEMP'
    if dataFile is not None:
        project_name = dataFile.name
    return project_name
