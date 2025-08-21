"""
FFmpeg wrapper module - A modular, SOLID-compliant FFmpeg wrapper

This module provides a clean interface for FFmpeg operations.
Users should instantiate components using the FFmpegFactory.
"""

import logging

# Import all components
from .exceptions import FFmpegError
from .interfaces import (
    IBinaryManager,
    ICommandExecutor,
    IMediaInfoExtractor,
    IFileValidator,
)
from .binary_manager import FFmpegBinaryManager
from .command_executor import FFmpegCommandExecutor
from .file_validator import FileValidator
from .media_info_extractor import MediaInfoExtractor
from .video_processor import VideoProcessor
from .pipeline import VideoGenerationPipeline
from .factory import FFmpegFactory


# Configure logging
logging.basicConfig(level=logging.INFO)

# Export public API
__all__ = [
    "FFmpegError",
    "IBinaryManager",
    "ICommandExecutor",
    "IMediaInfoExtractor",
    "IFileValidator",
    "FFmpegBinaryManager",
    "FFmpegCommandExecutor",
    "FileValidator",
    "MediaInfoExtractor",
    "VideoProcessor",
    "VideoGenerationPipeline",
    "FFmpegFactory",
]
