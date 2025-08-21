"""FFmpeg binary management and validation"""

import subprocess
import shutil
import logging
from .interfaces import IBinaryManager
from .exceptions import FFmpegError

logger = logging.getLogger(__name__)


class FFmpegBinaryManager(IBinaryManager):
    """Handles FFmpeg binary discovery and validation"""

    def __init__(self):
        self._ffmpeg_path = None
        self._ffprobe_path = None

    def get_ffmpeg_path(self) -> str:
        """Get ffmpeg binary path, discovering it if needed"""
        if self._ffmpeg_path is None:
            self._ffmpeg_path = self._find_ffmpeg_binary()
        return self._ffmpeg_path

    def get_ffprobe_path(self) -> str:
        """Get ffprobe binary path, discovering it if needed"""
        if self._ffprobe_path is None:
            self._ffprobe_path = self._find_ffprobe_binary()
        return self._ffprobe_path

    def _find_ffmpeg_binary(self) -> str:
        """Find and verify ffmpeg binary installation"""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise FFmpegError("ffmpeg binary not found. Please install ffmpeg.")

        # Verify ffmpeg works
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise FFmpegError("ffmpeg binary found but not functional")
        except subprocess.TimeoutExpired:
            raise FFmpegError("ffmpeg binary check timed out")
        except Exception as e:
            raise FFmpegError(f"Error verifying ffmpeg: {e}")

        logger.info(f"FFmpeg found at: {ffmpeg_path}")
        return ffmpeg_path

    def _find_ffprobe_binary(self) -> str:
        """Find and verify ffprobe binary installation"""
        ffprobe_path = shutil.which("ffprobe")
        if not ffprobe_path:
            raise FFmpegError(
                "ffprobe binary not found. Please install ffmpeg package."
            )

        # Verify ffprobe works
        try:
            result = subprocess.run(
                [ffprobe_path, "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise FFmpegError("ffprobe binary found but not functional")
        except subprocess.TimeoutExpired:
            raise FFmpegError("ffprobe binary check timed out")
        except Exception as e:
            raise FFmpegError(f"Error verifying ffprobe: {e}")

        logger.info(f"FFprobe found at: {ffprobe_path}")
        return ffprobe_path
