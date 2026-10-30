from .BaseController import BaseController
from .ProjectController import ProjectController
from models import ResponseSignal
from fastapi import UploadFile
import os
import re

class DataController(BaseController):
    """
    Handles everything related to uploaded files:
        - validating the file (type and size)
        - cleaning the file name
        - generating a unique path to store the file on disk
    """
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576  # 1 MB in bytes  

    def validate_uploaded_file(self, file: UploadFile):
        #Check that the uploaded file has an allowed type and is not too large.
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDS_LIMIT.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value


    def generate_unique_filepath(self, orig_file_name: str, project_id: str):
        """
        Build a unique path where the uploaded file will be saved.

        The file name is cleaned and prefixed with a random key, so two files
        with the same original name never overwrite each other.

        Example:
            "my report.pdf" -> "<project_path>/a1b2c3_myreport.pdf"

        Returns:
            (str, str): (full file path, file name with the random prefix)
        """
        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        return new_file_path, random_key + "_" + cleaned_file_name

    def get_clean_file_name(self, orig_file_name: str):

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name