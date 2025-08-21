import os
from typing import List

from src.domain.ports.storage import IStorage, IStoredFile


class FilesystemStoredFile(IStoredFile):
    def __init__(self, storage_root: str, relative_path: str):
        self._root = storage_root
        self._relative_path = relative_path

    @property
    def relative_path(self) -> str:
        return self._relative_path

    def _abs_path(self) -> str:
        target_path = os.path.abspath(os.path.join(self._root, self._relative_path))
        if (
            not target_path.startswith(self._root + os.sep)
            and target_path != self._root
        ):
            raise ValueError(
                "Path traversal detected; refusing to access outside storage root"
            )
        return target_path

    def write_bytes(self, data: bytes) -> None:
        target_path = self._abs_path()
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(data)

    def read_bytes(self) -> bytes:
        target_path = self._abs_path()
        with open(target_path, "rb") as f:
            return f.read()

    def write_text(self, text: str, encoding: str = "utf-8") -> None:
        target_path = self._abs_path()
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "w", encoding=encoding) as f:
            f.write(text)

    def read_text(self, encoding: str = "utf-8") -> str:
        target_path = self._abs_path()
        with open(target_path, "r", encoding=encoding) as f:
            return f.read()

    def exists(self) -> bool:
        target_path = self._abs_path()
        return os.path.exists(target_path)

    def delete(self) -> None:
        target_path = self._abs_path()
        if os.path.isdir(target_path):
            raise IsADirectoryError(
                "Refusing to delete a directory; specify a file path"
            )
        if os.path.exists(target_path):
            os.remove(target_path)


class FilesystemStorage(IStorage):
    def __init__(self, root_dir: str):
        self._root_dir = os.path.abspath(root_dir)
        os.makedirs(self._root_dir, exist_ok=True)

    def _resolve(self, relative_path: str) -> str:
        # Normalize and sandbox the path to the storage root
        target_path = os.path.abspath(os.path.join(self._root_dir, relative_path))
        if (
            not target_path.startswith(self._root_dir + os.sep)
            and target_path != self._root_dir
        ):
            raise ValueError(
                "Path traversal detected; refusing to access outside storage root"
            )
        return target_path

    def file(self, relative_path: str) -> IStoredFile:
        # Ensure the provided path is treated as storage-relative
        clean_path = relative_path.lstrip("/\\")
        return FilesystemStoredFile(self._root_dir, clean_path)

    def write_bytes(self, relative_path: str, data: bytes) -> str:
        target_path = self._resolve(relative_path)
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(data)
        return target_path

    def read_bytes(self, relative_path: str) -> bytes:
        target_path = self._resolve(relative_path)
        with open(target_path, "rb") as f:
            return f.read()

    def write_text(self, relative_path: str, text: str, encoding: str = "utf-8") -> str:
        target_path = self._resolve(relative_path)
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "w", encoding=encoding) as f:
            f.write(text)
        return target_path

    def read_text(self, relative_path: str, encoding: str = "utf-8") -> str:
        target_path = self._resolve(relative_path)
        with open(target_path, "r", encoding=encoding) as f:
            return f.read()

    def exists(self, relative_path: str) -> bool:
        target_path = self._resolve(relative_path)
        return os.path.exists(target_path)

    def makedirs(self, relative_dir_path: str) -> None:
        target_dir = self._resolve(relative_dir_path)
        os.makedirs(target_dir, exist_ok=True)

    def list(self, relative_dir_path: str) -> List[str]:
        target_dir = self._resolve(relative_dir_path)
        if not os.path.isdir(target_dir):
            return []
        return sorted(os.listdir(target_dir))

    def delete(self, relative_path: str) -> None:
        target_path = self._resolve(relative_path)
        if os.path.isdir(target_path):
            # Avoid deleting directories implicitly
            raise IsADirectoryError(
                "Refusing to delete a directory; specify a file path"
            )
        if os.path.exists(target_path):
            os.remove(target_path)
