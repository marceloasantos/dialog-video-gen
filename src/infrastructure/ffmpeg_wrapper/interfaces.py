"""Abstract interfaces for FFmpeg operations following Dependency Inversion Principle"""

import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any


class IBinaryManager(ABC):
    """Interface for binary management operations"""

    @abstractmethod
    def get_ffmpeg_path(self) -> str:
        pass

    @abstractmethod
    def get_ffprobe_path(self) -> str:
        pass


class ICommandExecutor(ABC):
    """Interface for command execution operations"""

    @abstractmethod
    def run_ffmpeg_command(
        self, args: List[str], timeout: int = 300
    ) -> subprocess.CompletedProcess:
        pass

    @abstractmethod
    def run_ffprobe_command(
        self, args: List[str], timeout: int = 30
    ) -> subprocess.CompletedProcess:
        pass


class IMediaInfoExtractor(ABC):
    """Interface for media information extraction"""

    @abstractmethod
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_audio_duration(self, file_path: str) -> float:
        pass

    @abstractmethod
    def get_video_duration(self, file_path: str) -> float:
        pass

    @abstractmethod
    def get_video_dimensions(self, file_path: str) -> Tuple[int, int]:
        pass

    @abstractmethod
    def get_image_dimensions(self, file_path: str) -> Tuple[int, int]:
        pass


class IFileValidator(ABC):
    """Interface for file validation operations"""

    @abstractmethod
    def validate_file_exists(self, file_path: str) -> bool:
        pass
