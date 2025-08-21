"""Factory for creating configured FFmpeg components"""

from .binary_manager import FFmpegBinaryManager
from .command_executor import FFmpegCommandExecutor
from .file_validator import FileValidator
from .media_info_extractor import MediaInfoExtractor
from .video_processor import VideoProcessor
from .pipeline import VideoGenerationPipeline
from src.domain.ports.storage import IStorage


class FFmpegFactory:
    """Factory class for creating configured FFmpeg components"""

    @staticmethod
    def create_minimal_setup(input_storage: IStorage = None):
        """Create only the components needed by the main application (media_info_extractor and pipeline)"""
        binary_manager = FFmpegBinaryManager()
        command_executor = FFmpegCommandExecutor(binary_manager)
        file_validator = FileValidator()
        media_info_extractor = MediaInfoExtractor(command_executor, file_validator)
        video_processor = VideoProcessor(
            command_executor, media_info_extractor, file_validator, input_storage
        )
        pipeline = VideoGenerationPipeline(video_processor)

        return {
            "media_info_extractor": media_info_extractor,
            "pipeline": pipeline,
        }
