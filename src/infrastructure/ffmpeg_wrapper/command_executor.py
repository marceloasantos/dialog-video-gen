"""FFmpeg command execution with error handling and logging"""

import subprocess
import logging
from typing import List
from .interfaces import ICommandExecutor, IBinaryManager
from .exceptions import FFmpegError

logger = logging.getLogger(__name__)


class FFmpegCommandExecutor(ICommandExecutor):
    """Handles FFmpeg command execution"""

    def __init__(self, binary_manager: IBinaryManager):
        self.binary_manager = binary_manager

    def run_ffmpeg_command(
        self, args: List[str], timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Run an ffmpeg command with error handling and logging

        Args:
            args: List of command arguments (without 'ffmpeg')
            timeout: Timeout in seconds

        Returns:
            CompletedProcess result

        Raises:
            FFmpegError: If command fails or times out
        """
        cmd = [self.binary_manager.get_ffmpeg_path()] + args
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )

            if result.returncode != 0:
                error_msg = (
                    f"FFmpeg command failed with return code {result.returncode}\n"
                )
                error_msg += f"Command: {' '.join(cmd)}\n"
                error_msg += f"Stderr: {result.stderr}\n"
                error_msg += f"Stdout: {result.stdout}"
                logger.error(error_msg)
                raise FFmpegError(error_msg)

            logger.info("FFmpeg command completed successfully")
            return result

        except subprocess.TimeoutExpired:
            error_msg = (
                f"FFmpeg command timed out after {timeout} seconds: {' '.join(cmd)}"
            )
            logger.error(error_msg)
            raise FFmpegError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error running ffmpeg command: {e}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)

    def run_ffprobe_command(
        self, args: List[str], timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """
        Run an ffprobe command with error handling and logging

        Args:
            args: List of command arguments (without 'ffprobe')
            timeout: Timeout in seconds

        Returns:
            CompletedProcess result

        Raises:
            FFmpegError: If command fails or times out
        """
        cmd = [self.binary_manager.get_ffprobe_path()] + args
        logger.info(f"Running ffprobe command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )

            if result.returncode != 0:
                error_msg = (
                    f"FFprobe command failed with return code {result.returncode}\n"
                )
                error_msg += f"Command: {' '.join(cmd)}\n"
                error_msg += f"Stderr: {result.stderr}\n"
                error_msg += f"Stdout: {result.stdout}"
                logger.error(error_msg)
                raise FFmpegError(error_msg)

            logger.info("FFprobe command completed successfully")
            return result

        except subprocess.TimeoutExpired:
            error_msg = (
                f"FFprobe command timed out after {timeout} seconds: {' '.join(cmd)}"
            )
            logger.error(error_msg)
            raise FFmpegError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error running ffprobe command: {e}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)
