from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers import get_settings, Settings
from controlles import DataController, ProjectController, ProcessController
from .schemes.data import processRequest
from models import ProjectModel, ChunkModel, AssetModel, ResponseSignal
from models.db_schemes import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
import aiofiles
import logging
import os 


logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_file(request: Request, project_id: str, file: UploadFile, 
                      app_settings: Settings = Depends(get_settings)):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project(project_id=project_id)

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

    #Store Assets in DB
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    asset_resource = Asset(
        asset_project_id = project.id,
        asset_type = AssetTypeEnum.FILE.value,
        asset_name = file_id,
        asset_size = os.path.getsize(file_path)
    )

    asset_record= await asset_model.Create_asset(asset= asset_resource)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"File '{file.filename}' uploaded successfully for project '{project_id}'.",
                 "file_id": str(asset_record.id)
            }
    )


@data_router.post("/process/{project_id}")
async def process(request: Request, project_id: str, process_request: processRequest):
    """
    Split project files into text chunks and store them in the database.

    Flow:
        1. Read chunking settings from the request body.
        2. Load the project and figure out which files to process
           (one specific file, or all files in the project).
        3. Optionally delete existing chunks (reset).
        4. For each file: read content -> split into chunks -> save chunks.
        5. Return the number of files processed and chunks inserted.
    """

    # ------------------------------------------------------------------
    # 1. Read processing settings from the request body
    # ------------------------------------------------------------------
    # file_id = process_request.file_id   (handled below; kept for reference)

    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.overlap
    do_reset = process_request.do_reset

    # ------------------------------------------------------------------
    # 2. Initialize models and controllers
    # ------------------------------------------------------------------
    # Each model is created asynchronously with the app's shared DB client
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    # Fetch the project from the DB (it is created if it doesn't exist yet)
    project = await project_model.get_project(project_id=project_id)

    # Controller responsible for reading files and splitting them into chunks
    process_controller = ProcessController(project_id=project_id)

    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    # ------------------------------------------------------------------
    # 3. Decide which files to process
    # ------------------------------------------------------------------
    # Maps: asset DB id -> file name
    project_files_ids = {}
    # Case A: the client asked for ONE specific file
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.id,
            asset_name=process_request.file_id
        )
        # The file doesn't exist in this project -> return 400
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )

        project_files_ids = {
            asset_record.id: asset_record.asset_name
        }

    # Case B: no file specified -> process ALL file assets of the project
    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {
            record.id: record.asset_name
            for record in project_files
        }
    # Nothing to process (project has no files) -> return 400
    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
            }
        )
    # ------------------------------------------------------------------
    # 4. Prepare counters and (optionally) reset old data
    # ------------------------------------------------------------------
    no_records = 0
    no_files = 0
    # If requested, remove all existing chunks of this project
    # so we don't end up with duplicates after re-processing
    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )

    # ------------------------------------------------------------------
    # 5. Process each file
    # ------------------------------------------------------------------

    for asset_id, file_id in project_files_ids.items():
         # Read the raw content of the file from storage
        file_content = process_controller.get_file_content(file_id=file_id)
        # If the file couldn't be read, log it and skip to the next file
        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue
        # Split the content into smaller chunks using the requested size/overlap
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Splitting produced nothing -> abort the whole request with a 400
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": ResponseSignal.PROCESSING_FAILED.value
                }
            )
        
        # Convert each chunk into a DataChunk database record.
        # chunk_order starts at 1 so we can rebuild the original order later.
        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "message": ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            "Number of Inserted Chunks": no_records,
            "Number of Processed Files": no_files
        }
    )
