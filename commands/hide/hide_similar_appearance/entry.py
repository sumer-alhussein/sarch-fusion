from typing import List
import adsk.core
import adsk.fusion
import os

from ...hide import GROUP_ICON


from .... import config
from ....lib import fusion360utils as futil
app = adsk.core.Application.get()


ui = app.userInterface

# CMD_NAME = os.path.basename(os.path.dirname(__file__))
CMD_NAME = 'Similar Appearance'

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_{CMD_NAME}'
CMD_Description = 'Hide all bodies with similar appearance.'
IS_PROMOTED = False

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

HIDE_GROUP_ID = config.hide_group_id
HIDE_GROUP_NAME = config.hide_group_name


# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources',)


# Holds references to event handlers
local_handlers = []


# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******************************** Create Command Control ********************************
    # Get target workspace for the command.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get target panel for the command and and create the panel if necessary.
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    # Add the selection group to the panel if it doesn't exist
    # selection_group = panel.controls.itemById(SELECTION_GROUP_ID)
    selection_group = panel.controls.addDropDown(HIDE_GROUP_NAME, GROUP_ICON, HIDE_GROUP_ID)
    if selection_group:
        # Create the command control, i.e. a button in the UI.
        control = selection_group.controls.addCommand(cmd_def)
        control.isPromoted = IS_PROMOTED

    # Now you can set various options on the control such as promoting it to always be shown.


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_group = panel.controls.itemById(HIDE_GROUP_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the selection group if it is empty
    if command_group:
        command_group.deleteMe()
    # Delete the panel if it is empty
    if panel.controls.count == 0:
        panel.deleteMe()

    # Delete the tab if it is empty
    if toolbar_tab.toolbarPanels.count == 0:
        toolbar_tab.deleteMe()

# Function to be called when a user clicks the corresponding button in the UI
# Here you define the User Interface for your command and identify other command events to potentially handle
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug
    futil.log(f'{CMD_NAME} Command Created Event')

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This function will be called when the user hits the OK button in the command dialog
def command_execute(args: adsk.core.CommandEventArgs):
    design = adsk.fusion.Design.cast(app.activeProduct)
    
    futil.log(f'{CMD_NAME} Command Execute Event')

    # ? get the the active selection

    _selected_intities = ui.activeSelections

    _selected_faces: List[adsk.fusion.BRepFace] = [
    adsk.fusion.BRepFace.cast(_face.entity) for _face in _selected_intities if _face.entity.objectType == adsk.fusion.BRepFace.classType()
    ]

    _selected_appearances = [face.appearance.name.lower() for face in _selected_faces if face.appearance]

    # _all_bodies = root_component.bRepBodies
    _root_component = design.rootComponent
    _all_components = design.allComponents
    _all_occurrences = [occ for comp in _all_components for occ in comp.allOccurrences]
    # _all_bodies = [comp.bRepBodies for comp in _all_components ]
    # _all_bodies = [body for comp in _all_components for body in comp.bRepBodies]
    _all_bodies = [body for occ in _all_occurrences for body in occ.bRepBodies]
    _all_bodies += _root_component.bRepBodies

    futil.log(f'all_bodies, {len(_all_bodies)}')
    # _all_bodies = [comp.bRepBodies for comp in _all_components ]
    
    _bodies_with_similar_appearances = [body for body in _all_bodies if body.appearance.name.lower() in _selected_appearances]

    futil.log(f'_selected_materials, {_selected_appearances}')
    futil.log(f'similar_appearances, {len(_bodies_with_similar_appearances)}')

    ui.activeSelections.clear()
    
    for _match in _bodies_with_similar_appearances :
        ui.activeSelections.add(_match)
        _match.isVisible = False

    # msg = f'Hello World'
    # ui.messageBox(msg)


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')
