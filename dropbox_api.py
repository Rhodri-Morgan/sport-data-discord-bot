import dropbox
from dropbox.exceptions import ApiError
import os
import shutil
import json


class DropBoxAPI:
    def __init__(self, user_commands, certifications):
        self.dropbox = dropbox.Dropbox(os.environ.get('dropbox_token'))
        self.download_required(user_commands, certifications)


    def check_path_exists(self, dropbox_path):
        ''' Checks if a file paths exists in dropbox '''
        try:
            metadata = self.dropbox.files_get_metadata(dropbox_path)
            if metadata != None:
                return True
        except ApiError:
            return False
    

    def upload_file(self, file_path, dropbox_path):
        ''' Deletes existing path and uploads file to dropbox '''
        if self.check_path_exists(dropbox_path):
            self.dropbox.files_delete(dropbox_path)

        with open(file_path, 'rb') as f:
            self.dropbox.files_upload(f.read(), dropbox_path)


    def download_file(self, local_path, dropbox_path):
        ''' Downloads specified file from dropbox and returns path (if not present creates empty file) '''
        file_path = os.getcwd()
        dropbox_subpaths = dropbox_path.split('/')
        for sub_path in dropbox_subpaths[1:-1:]:
            file_path = os.path.join(file_path, sub_path)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        file_path = os.path.join(file_path, dropbox_subpaths[-1])

        if local_path is not None and os.path.exists(local_path):
            return local_path
        elif self.check_path_exists(dropbox_path):
            self.dropbox.files_download_to_file(file_path, dropbox_path)
        else:
            with open(file_path, 'w') as f:
                empty = {}
                json.dump(empty, f)
       
        return file_path


    def download_required(self, user_commands, certifications):
        ''' Downloads the required files for the bot to function correctly '''
        if os.path.exists(user_commands):
            os.remove(user_commands)
        self.download_file(None, '/user_commands.json')

        if os.path.exists(certifications):
            shutil.rmtree(certifications)
        os.mkdir(certifications)
        self.download_file(None, '/client-2048.crt')
        self.download_file(None, '/client-2048.key')
        shutil.move(os.path.join(os.getcwd(), 'client-2048.crt'), os.path.join(certifications, 'client-2048.crt'))
        shutil.move(os.path.join(os.getcwd(), 'client-2048.key'), os.path.join(certifications, 'client-2048.key'))