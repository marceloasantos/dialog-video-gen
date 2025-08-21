from src.infrastructure.services.environment_service import (
    CACHE_STORAGE_PATH,
    TIGRIS_INPUT_BUCKET,
    TIGRIS_OUTPUT_BUCKET,
    STORAGE_BACKEND,
    FILESYSTEM_INPUT_PATH,
    FILESYSTEM_OUTPUT_PATH,
)
from .filesystem_storage import FilesystemStorage
from .tigris_storage import TigrisS3Storage


def create_cache_storage() -> FilesystemStorage:
    return FilesystemStorage(CACHE_STORAGE_PATH)


def create_output_storage():
    if STORAGE_BACKEND == "filesystem":
        if not FILESYSTEM_OUTPUT_PATH:
            raise ValueError(
                "FILESYSTEM_OUTPUT_PATH must be set when STORAGE_BACKEND=filesystem"
            )
        return FilesystemStorage(FILESYSTEM_OUTPUT_PATH)
    return TigrisS3Storage(TIGRIS_OUTPUT_BUCKET)


def create_input_storage():
    if STORAGE_BACKEND == "filesystem":
        if not FILESYSTEM_INPUT_PATH:
            raise ValueError(
                "FILESYSTEM_INPUT_PATH must be set when STORAGE_BACKEND=filesystem"
            )
        return FilesystemStorage(FILESYSTEM_INPUT_PATH)
    return TigrisS3Storage(TIGRIS_INPUT_BUCKET)
