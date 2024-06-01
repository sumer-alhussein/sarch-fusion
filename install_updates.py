import os
import requests
import shutil
import zipfile

from constants import GITHUB_LATEST_RELEASE_DOWNLOAD


url = GITHUB_LATEST_RELEASE_DOWNLOAD

current_dir = os.path.dirname(os.path.realpath(__file__))
# root_dir = os.path.abspath(os.path.join(currrnt_directory, os.pardir))

dir_path = current_dir

# Create .temp folder in root directory
temp_directory = os.path.join(dir_path, ".temp")

print('installing updates...')
# Make sure .temp directory exists
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

    print(f"Downloaded file: {file_name}")
    # Check if the file is a zip file
    if zipfile.is_zipfile(file_name):
        # Create a ZipFile object
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            # Extract all the contents of the zip file into the temp directory
            zip_ref.extractall(temp_directory)

            # Define the source and destination directories
            source_directory = os.path.join(
                temp_directory, "sarch-fusion-main")
            destination_directory = os.path.join(dir_path, "sarch-fusion")

            # Make sure the destination directory exists
            os.makedirs(destination_directory, exist_ok=True)

            # Copy the contents of the source directory to the destination directory
            for file_name in os.listdir(source_directory):
                shutil.move(os.path.join(source_directory,
                            file_name), destination_directory)

            print(
                f"Copied files from {source_directory} to {destination_directory}")
    else:
        print(f"{file_name} is not a zip file.")
else:
    print("Failed to download file")
