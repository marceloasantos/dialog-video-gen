from contextlib import contextmanager
from src.infrastructure.services.file_processing_service import FileProcessingService


class FileManagementService:
    """Service responsible for managing file operations during video creation."""

    def __init__(self, file_processing_service: FileProcessingService):
        self.file_processing_service = file_processing_service

    @contextmanager
    def prepare_input_video(self, input_video_path: str):
        """
        Context manager for preparing and cleaning up input video files.

        Args:
            input_video_path: Path to the input video file

        Yields:
            str: Local path to the prepared video file
        """
        local_input_video_path, _ = (
            self.file_processing_service.validate_and_prepare_input_video(
                input_video_path
            )
        )

        try:
            yield local_input_video_path
        finally:
            self.file_processing_service.cleanup_temp_file(local_input_video_path)
