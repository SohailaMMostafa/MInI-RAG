from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from models import ResponseSignal
import os
from helpers import get_settings, Settings
from controlles import DataController, ProjectController
import aiofiles
import logging


logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_file(project_id: str, file: UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    # Check if the file type is allowed
    is_valid, message = DataController().validate_uploaded_file(file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": message}
        )

    project_dir_path = ProjectController().get_project_path(project_id = project_id)
    file_path, file_id = DataController().generate_unique_filepath(orig_file_name=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):  # Read in chunks of the default size
                await f.write(chunk)
    except Exception as e:
            logger.error(f"Error occurred while saving the file: {e}")

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": ResponseSignal.FILE_UPLOAD_FAILED.value}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"File '{file.filename}' uploaded successfully for project '{project_id}'.",
                 "file_id": file_id}
    )
