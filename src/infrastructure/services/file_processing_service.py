import os
import tempfile
from typing import Tuple
from src.domain.ports.storage import IStorage


class FileProcessingService:
    """Infrastructure service for handling file operations and path validation."""

    def __init__(self, input_storage: IStorage):
        self.input_storage = input_storage

    def validate_and_prepare_input_video(
        self, input_video_path: str
    ) -> Tuple[str, str]:
        """
        Validates input video path and prepares it for processing.

        Returns:
            Tuple of (local_file_path, file_extension)
        """
        # Validate path format
        if os.path.isabs(input_video_path):
            raise ValueError(
                "input_video_path must be storage-relative (e.g., 'videos/foo.mp4'), not absolute"
            )

        # Get file handle and validate existence
        input_file_handle = self.input_storage.file(input_video_path)
        if not input_file_handle.exists():
            raise FileNotFoundError(
                f"Input video not found in storage at '{input_file_handle.relative_path}'"
            )

        # Materialize input video into a local temp file path for ffmpeg
        video_bytes = input_file_handle.read_bytes()
        _, ext = os.path.splitext(input_file_handle.relative_path)
        ext = ext or ".mp4"

        tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            tmp_input.write(video_bytes)
        finally:
            tmp_input.close()

        return tmp_input.name, ext

    def cleanup_temp_file(self, local_file_path: str) -> None:
        """Cleans up temporary file."""
        try:
            os.remove(local_file_path)
        except OSError:
            pass
