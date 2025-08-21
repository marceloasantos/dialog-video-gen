from abc import ABC, abstractmethod
from typing import List


class IStoredFile(ABC):
    """A handle to a file located within a storage root."""

    @property
    @abstractmethod
    def relative_path(self) -> str:  # storage-relative path
        pass

    @abstractmethod
    def write_bytes(self, data: bytes) -> None:
        """Write binary data to this file (overwrites)."""

    @abstractmethod
    def read_bytes(self) -> bytes:
        """Read binary data from this file."""

    @abstractmethod
    def write_text(self, text: str, encoding: str = "utf-8") -> None:
        """Write text data to this file (overwrites)."""

    @abstractmethod
    def read_text(self, encoding: str = "utf-8") -> str:
        """Read text data from this file."""

    @abstractmethod
    def exists(self) -> bool:
        pass


class IStorage(ABC):
    """Abstract storage interface for reading and writing files.

    Implementations must ensure paths are sandboxed within a configured root
    directory and prevent path traversal outside that root.
    """

    @abstractmethod
    def file(self, relative_path: str) -> IStoredFile:
        """Return a file handle bound to the given relative path."""

    @abstractmethod
    def write_bytes(self, relative_path: str, data: bytes) -> str:
        """Write binary data to a file at the given relative path.

        Returns the absolute path of the written file.
        """

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read binary data from a file at the given relative path."""

    @abstractmethod
    def write_text(self, relative_path: str, text: str, encoding: str = "utf-8") -> str:
        """Write text data to a file at the given relative path.

        Returns the absolute path of the written file.
        """

    @abstractmethod
    def read_text(self, relative_path: str, encoding: str = "utf-8") -> str:
        """Read text data from a file at the given relative path."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check whether the path exists within the storage root."""

    @abstractmethod
    def makedirs(self, relative_dir_path: str) -> None:
        """Create directories for the given relative directory path if missing."""

    @abstractmethod
    def list(self, relative_dir_path: str) -> List[str]:
        """List entries within the given relative directory path."""

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """Delete the file at the given relative path if it exists."""
