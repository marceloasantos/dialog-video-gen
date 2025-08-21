"""File validation operations"""

import os
from .interfaces import IFileValidator


class FileValidator(IFileValidator):
    """Handles file validation operations"""

    def validate_file_exists(self, file_path: str) -> bool:
        """Validate that a file exists and is readable"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
