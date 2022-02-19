import boto3
import os
import shutil


class AmazonS3:
    def __init__(self, user_commands, certifications):
        self.s3 = boto3.client('s3',
                               aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                               aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                               region_name='eu-west-2')
        self.bucket_name = os.environ.get('AWS_BUCKET_NAME')
        self.download_required(user_commands, certifications)


    def download_file(self, aws_filename, output_filename):
        ''' Downloads file hosted on AWS S3 with same filename '''
        output_path = os.path.join(os.getcwd(), output_filename)
        if os.path.exists(output_path):
            os.remove(output_path)

        self.s3.download_file(self.bucket_name, aws_filename, output_filename)


    def upload_file(self, input_filename, aws_filename):
        ''' Uploads file to be hosted on AWS S3 '''
        self.s3.upload_file(input_filename, self.bucket_name, aws_filename)


    def download_required(self, user_commands, certifications):
        """ Downloads the required files for the bot to function correctly """
        if os.path.exists(user_commands):
            os.remove(user_commands)
        self.download_file('user_commands.json', 'user_commands.json')

        if os.path.exists(certifications):
            shutil.rmtree(certifications)
        os.mkdir(certifications)
        self.download_file('client-2048.crt', 'client-2048.crt')
        self.download_file('client-2048.key', 'client-2048.key')
        shutil.move(os.path.join(os.getcwd(), 'client-2048.crt'), os.path.join(certifications, 'client-2048.crt'))
        shutil.move(os.path.join(os.getcwd(), 'client-2048.key'), os.path.join(certifications, 'client-2048.key'))
