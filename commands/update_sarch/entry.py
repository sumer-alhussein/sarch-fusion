import traceback
from typing import List
import adsk.cam
from sys import prefix
import adsk.core
import adsk.fusion
import os

from ...services import *

from ...helpers import *
from ...lib import fusion360utils as futil
from ... import config


import http.client
import json

import re

app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Define the categories and sub-categories for the command. ***
# This is used to create a drop-down list in the command dialog.
# Categories and Sub-Categories type


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_UPDATE_CMD'
CMD_NAME = 'Update SARCH-FUSION'
CMD_Description = 'Check for updates and download the latest version of SARCH-FUSION.'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = False

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
    check_for_updates()
    
    # futil.log(f'Current Version: {current_version}')
    # h = http.client.HTTPSConnection('api.github.com')
    # headers = {'User-Agent': 'Fusion360'}
    # h.request('GET', '/users/autodeskfusion360/repos', '', headers)
    # res = h.getresponse()

    # resBytes = res.read()
    # resString = resBytes.decode('utf-8')
    # resJson = json.loads(resString)

    # futil.log(f'Command Created Event {resJson}')


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

    # # ? Prefix Text Input
    # prefix_input = inputs.addStringValueInput(
    #     'prefix_input', 'Project name with prefix', f"{_project_name.upper()}")
    # prefix_input.tooltip = 'Prefix to component name eg. UC1_999 will create UC1_999_CATEGORY_SUBCATEGORY_1'
    # prefix_input.isEnabled = False


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



def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # use_project_name_input: adsk.core.BoolValueCommandInput = adsk.core.BoolValueCommandInput.cast(inputs.itemById(
    #     'use_project_name_input'))
    # prefix_input: adsk.core.StringValueCommandInput = adsk.core.StringValueCommandInput.cast(
    #     inputs.itemById(
    #         'prefix_input'))
    # category_input: adsk.core.DropDownCommandInput = adsk.core.DropDownCommandInput.cast(inputs.itemById(
    #     'category_input'))
    # subcategories_input: adsk.core.ButtonRowCommandInput = adsk.core.ButtonRowCommandInput.cast(
    #     inputs.itemById(
    #         'subcategories_input'))
    # subcategories_input_listItems = subcategories_input.listItems

    # if changed_input.id == use_project_name_input.id:
    #     prefix_input.isEnabled = not use_project_name_input.value
    #     futil.log(f'prefix_input: {prefix_input.value}')
    #     if use_project_name_input:
    #         prefix_input.value = _project_name.upper()

    # if changed_input.id == category_input.id:
    #     if category_input.selectedItem is not None:
    #         subcategories_input_listItems.clear()
    #         selected_category = next(
    #             (category for category in CATEGORIES if category['name'] == category_input.selectedItem.name), None)
    #         if selected_category is None:
    #             return
    #         for subcategory in selected_category['subcategories']:
    #             _icon = os.path.join(
    #                 ICON_FOLDER, f'{selected_category["id"]}_{subcategory["id"]}')

    #             subcategories_input_listItems.add(
    #                 subcategory['name'], False, _icon, -1)

    #         subcategories_input.isVisible = True

    #     else:
    #         subcategories_input_listItems.clear()
    #         subcategories_input.isVisible = False
    #         pass

    # General logging for debug.
    futil.log(
        f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    # futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    prefix_input: adsk.core.StringValueCommandInput = adsk.core.StringValueCommandInput.cast(inputs.itemById(
        'prefix_input'))
    category_input: adsk.core.DropDownCommandInput = adsk.core.DropDownCommandInput.cast(inputs.itemById(
        'category_input'))
    subcategories_input: adsk.core.ButtonRowCommandInput = adsk.core.ButtonRowCommandInput.cast(inputs.itemById(
        'subcategories_input'))

    # if re.match(SAFE_PROJECT_NAME_PATTERN, prefix_input.value) and category_input.selectedItem is not None and subcategories_input.selectedItem is not None:
    #     args.areInputsValid = True

    # else:
    #     args.areInputsValid = False


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []


