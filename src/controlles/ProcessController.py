from .BaseController import BaseController
from .ProjectController import ProjectController
from models import ResponseSignal, ProcessingEnums
from fastapi import UploadFile
import os
import re
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter



class ProcessController(BaseController):
    """
    Handles reading a project's files and splitting their text into chunks.

    Pipeline:
        file name -> loader (PDF/TXT) -> loaded documents -> text chunks
    """
    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=self.project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        """
        Pick the right LangChain loader for the file based on its extension.

        Returns:
            A loader object, or None if the file doesn't exist on disk.

        Raises:
            ValueError: if the file type is not supported.
        """
        file_path = os.path.join(self.project_path, file_id)
        file_extension = self.get_file_extension(file_id)

        if not os.path.exists(file_path):
            return None

        if file_extension == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)
        elif file_extension == ProcessingEnums.TXT.value:
            return TextLoader(file_path, "utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


    def get_file_content(self, file_id: str):
        """
        Load a file and return its content as a list of LangChain Documents
        (for PDFs, typically one Document per page).

        Returns:
            list of Documents, or None if the file couldn't be found.
        """
        loader = self.get_file_loader(file_id)
        if loader:
            return loader.load() 
        return None

    def process_file_content(self, file_id: str, file_content: list, 
                             chunk_size: int=1000, chunk_overlap: int=20):
        """
        Split loaded documents into smaller overlapping chunks.

        Returns:
            list of Documents, one per chunk, each with its original metadata.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

        file_content_texts = [rec.page_content for rec in file_content]
        file_content_metadata = [rec.metadata for rec in file_content]

        chunks = text_splitter.create_documents(
            file_content_texts, metadatas=file_content_metadata
        )

        return chunks
        