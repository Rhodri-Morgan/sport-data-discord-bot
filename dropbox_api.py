import dropbox
from dropbox.exceptions import ApiError
import os
import json


class DropBoxAPI:
    def __init__(self):
        with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
            self.credentials = json.loads(f.read())['dropbox']

        self.dropbox = dropbox.Dropbox(self.credentials['access_token'])


    def check_path_exists(self, dropbox_path):
        try:
            metadata = self.dropbox.files_get_metadata(dropbox_path)
            if metadata != None:
                return True
        except ApiError:
            return False
    

    def upload(self, file_path, dropbox_path):
        if self.check_path_exists(dropbox_path):
            self.dropbox.files_delete(dropbox_path)

        with open(file_path, 'rb') as f:
            self.dropbox.files_upload(f.read(), dropbox_path)


    def download_file(self, dropbox_path):
        if self.check_path_exists(dropbox):
            self.dropbox.files_download(dropbox_path)
            return dropbox_path.split('/')[-1]
        else:
            return None


'''
Dropbox layout
├── user_commands.json
├── EVENT_NAME
    ├── EVENT_NAME_MARKET_NAME.JSON
    └── ...
├── ...
'''