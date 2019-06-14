import json
import pathlib

# Update a settings dict with the contents of a json file
def overwrite_settings(json_file, settings):
    with open(json_file) as f:
        d = json.load(f)
        for k, v in d.items():
            # Only already existing values may be updated
            assert k in settings, "Invalid setting: {}".format(k)
            settings[k] = v

# Take a list of (settings_dict, filename),
# search folder for the filename, and update each desired settings
# with the file's contents
def get_settings(settings_list, folder):
    folder_path = pathlib.Path(folder)
    for d, fname in settings_list:
        file_path = folder_path / fname
        # Ignore files that are not present
        if file_path.is_file():
            overwrite_settings(str(file_path), d)

