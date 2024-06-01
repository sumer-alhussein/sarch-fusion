# check for updates
import http.client
import json
import os
import requests
import shutil
import zipfile

from ..constants import *
from ..helpers import *
from ..lib import fusion360utils as futil


def get_latest_version() -> str | None:
    lts_version = 'Unknown'
    # get latest version from the server
    h = http.client.HTTPSConnection('api.github.com')
    headers = {'User-Agent': 'Fusion360'}
    h.request('GET', LATEST_RELEASE_API, '', headers)
    res = h.getresponse()

    # Check the status code and content type
    if res.status != 200:
        futil.log(f'Request failed with status code {res.status}')
        return

    resBytes = res.read()
    resString = resBytes.decode('utf-8')

    # Check if the response is empty
    if not resString:
        futil.log('Empty response')
        return

    try:
        resJson = json.loads(resString)
        # futil.log(f'Command Created Event {resJson}')
        lts_version = resJson['tag_name'].replace('v', '')
    except json.JSONDecodeError:
        futil.log('Failed to decode JSON')
    # latest_release = http.
    # lts_version = resJson['tag_name'].replace('v', '')
    # return lts_version
    futil.log(f'Latest version: {lts_version}')
    return lts_version


def check_for_updates():
    _current_version = use_version()
    _latest_version = get_latest_version()
    if not _latest_version:
        futil.log('Failed to get the latest version')
        return
    if is_newer_version(_current_version, _latest_version):
        futil.log('Newer version available')
        return True
    futil.log('No updates available')
    return False


def download_and_installing_updates(url, root_directory):
    # Make sure .temp directory exists
    temp_directory = os.path.join(root_directory, ".temp")
    os.makedirs(temp_directory, exist_ok=True)

    # Send a HTTP request to the URL of the file
    response = requests.get(url, stream=True)

    # Check if the request is successful
    if response.status_code == 200:
        # Get the file name by joining it with the root directory
        file_name = os.path.join(temp_directory, url.split("/")[-1])

        # Open the file in write mode and download the file
        with open(file_name, 'wb') as file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)

        futil.log(f"Downloaded file: {file_name}")

        # Check if the file is a zip file
        if zipfile.is_zipfile(file_name):
            # Create a ZipFile object
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                # Extract all the contents of the zip file into the temp directory
                zip_ref.extractall(temp_directory)

                # Delete all files and folders in the root directory except .temp and .git
                for item in os.listdir(root_directory):
                    if item not in [".temp", ".git"]:
                        item_path = os.path.join(root_directory, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        else:
                            shutil.rmtree(item_path)

                # Define the source directory
                source_directory = os.path.join(
                    temp_directory, "sarch-fusion-main")

                # Copy the contents of the source directory to the root directory
                for item in os.listdir(source_directory):
                    shutil.move(os.path.join(
                        source_directory, item), root_directory)

                futil.log(
                    f"Copied files from {source_directory} to {root_directory}")
                shutil.rmtree(temp_directory)
                futil.log("Update successful")
        else:
            futil.log(f"{file_name} is not a zip file.")
    else:
        futil.log("Failed to download file")
