import json
import os
from ..lib import fusion360utils as futil

# Get the absolute path of the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Move one directory up (to the root directory)
root_dir = os.path.dirname(current_dir)

# Construct the path to sarch.manifest in the root directory
manifest_path = os.path.join(root_dir, "sarch.manifest")


def use_version():
    # futil.log('Using version from sarch.manifest file')
    # futil.log(f'Current working directory: {os.getcwd()}')
    # futil.log(os.path.abspath('../sarch.manifest'))
    futil.log(manifest_path)
    with open(manifest_path) as f:
        data = json.load(f)
        return data['version']