"""Media information extraction using ffprobe"""

import json
from typing import Dict, Any, Tuple
from .interfaces import IMediaInfoExtractor, ICommandExecutor, IFileValidator
from .exceptions import FFmpegError


class MediaInfoExtractor(IMediaInfoExtractor):
    """Handles media information extraction"""

    def __init__(
        self, command_executor: ICommandExecutor, file_validator: IFileValidator
    ):
        self.command_executor = command_executor
        self.file_validator = file_validator

    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive media information using ffprobe

        Args:
            file_path: Path to media file

        Returns:
            Dictionary containing media information

        Raises:
            FFmpegError: If file doesn't exist or ffprobe fails
        """
        if not self.file_validator.validate_file_exists(file_path):
            raise FFmpegError(f"File not found or not readable: {file_path}")

        args = [
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        result = self.command_executor.run_ffprobe_command(args)

        try:
            media_info = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse ffprobe JSON output: {e}")

        return media_info

    def get_audio_duration(self, file_path: str) -> float:
        """
        Get audio file duration using ffprobe (replaces AudioFileClip.duration)

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds
        """
        media_info = self.get_media_info(file_path)

        # Look for audio stream
        for stream in media_info.get("streams", []):
            if stream.get("codec_type") == "audio":
                duration = stream.get("duration")
                if duration:
                    return float(duration)

        # Fallback to format duration
        format_info = media_info.get("format", {})
        duration = format_info.get("duration")
        if duration:
            return float(duration)

        raise FFmpegError(f"Unable to determine audio duration for: {file_path}")

    def get_video_duration(self, file_path: str) -> float:
        """
        Get video file duration using ffprobe (replaces VideoFileClip.duration)

        Args:
            file_path: Path to video file

        Returns:
            Duration in seconds
        """
        media_info = self.get_media_info(file_path)

        # Look for video stream
        for stream in media_info.get("streams", []):
            if stream.get("codec_type") == "video":
                duration = stream.get("duration")
                if duration:
                    return float(duration)

        # Fallback to format duration
        format_info = media_info.get("format", {})
        duration = format_info.get("duration")
        if duration:
            return float(duration)

        raise FFmpegError(f"Unable to determine video duration for: {file_path}")

    def get_video_dimensions(self, file_path: str) -> Tuple[int, int]:
        """
        Get video dimensions using ffprobe (replaces video_clip.size)

        Args:
            file_path: Path to video file

        Returns:
            Tuple of (width, height)
        """
        media_info = self.get_media_info(file_path)

        # Look for video stream
        for stream in media_info.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    return (int(width), int(height))

        raise FFmpegError(f"Unable to determine video dimensions for: {file_path}")

    def get_image_dimensions(self, file_path: str) -> Tuple[int, int]:
        """
        Get image dimensions using ffprobe.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (width, height)
        """
        media_info = self.get_media_info(file_path)

        # Look for the first stream (for images, there's usually just one)
        for stream in media_info.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    return (int(width), int(height))

        raise FFmpegError(f"Unable to determine image dimensions for: {file_path}")
