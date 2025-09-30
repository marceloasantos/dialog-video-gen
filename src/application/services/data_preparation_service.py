from typing import List, Dict
from src.domain.entities.dialogue import Dialogue, Line
from src.domain.entities.character import Character
from src.domain.ports.repositories import ICharacterRepository
from src.domain.ports.storage import IStorage
from src.domain.ports.storage import IStoredFile

import hashlib
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class _InMemoryStoredFile(IStoredFile):
    """In-memory implementation of IStoredFile for ephemeral files.

    Used to hold downloaded assets without persisting them into the input storage.
    """

    def __init__(self, relative_path: str, initial_bytes: bytes | None = None):
        self._relative_path = relative_path
        self._buffer = initial_bytes or b""

    @property
    def relative_path(self) -> str:
        return self._relative_path

    def write_bytes(self, data: bytes) -> None:
        self._buffer = data

    def read_bytes(self) -> bytes:
        return self._buffer

    def write_text(self, text: str, encoding: str = "utf-8") -> None:
        self._buffer = text.encode(encoding)

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._buffer.decode(encoding)

    def exists(self) -> bool:
        # Ephemeral object is considered to exist while in memory
        return True


class DataPreparationService:
    """Service responsible for preparing and transforming input data into domain objects."""

    def __init__(
        self, character_repository: ICharacterRepository, input_storage: IStorage
    ):
        self.character_repository = character_repository
        self.input_storage = input_storage

    def _is_http_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _infer_image_extension(self, url_path: str) -> str:
        _, ext = os.path.splitext(url_path)
        ext = (ext or "").lower()
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            return ext
        return ".png"

    def _download_image_as_handle(self, url: str) -> IStoredFile:
        """
        Downloads an image from the given URL enforcing a 10 MB limit and returns an
        in-memory IStoredFile handle. No bytes are persisted to the input storage.
        """
        MAX_BYTES = 10 * 1024 * 1024  # 10 MB
        req = Request(url, headers={"User-Agent": "byteme/1.0"})
        with urlopen(req, timeout=30) as resp:
            # Optional early check via Content-Length
            content_length = resp.headers.get("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > MAX_BYTES:
                        raise ValueError(
                            f"Image at URL exceeds 10 MB limit (Content-Length: {content_length} bytes)"
                        )
                except ValueError:
                    # If header parsing fails, ignore and fall back to streaming enforcement
                    pass

            buffer = bytearray()
            chunk_size = 64 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                buffer.extend(chunk)
                if len(buffer) > MAX_BYTES:
                    raise ValueError("Image at URL exceeds 10 MB limit during download")

        # Derive a deterministic display path for validation and extension inference
        parsed = urlparse(url)
        ext = self._infer_image_extension(parsed.path)
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        relative_path = f"downloaded_images/{url_hash}{ext}"

        # Return an in-memory file handle carrying the downloaded bytes
        return _InMemoryStoredFile(
            relative_path=relative_path, initial_bytes=bytes(buffer)
        )

    def prepare_characters(self, characters_data: dict) -> Dict[str, Character]:
        """
        Transform characters into domain models with instantiated image file handles.

        Returns:
            Dict[str, Character]: Mapping of character name to domain Character.
        """
        domain_characters: Dict[str, Character] = {}
        for name, char_dict in characters_data.items():
            image_ref = char_dict.get("image_file")
            if image_ref is None:
                raise ValueError(f"Character '{name}' is missing 'image_file' field")

            # Support HTTP(S) URLs by downloading into an in-memory handle with a 10 MB cap
            if isinstance(image_ref, str) and self._is_http_url(image_ref):
                image_file = self._download_image_as_handle(image_ref)
            else:
                image_file = self.input_storage.file(image_ref)

            domain_characters[name] = Character(
                voice_id=char_dict["voice_id"],
                image_file=image_file,
                position=char_dict["position"],
                scale=char_dict["scale"],
                margin=char_dict["margin"],
                primary_color=char_dict["primary_color"],
                secondary_color=char_dict["secondary_color"],
            )
        return domain_characters

    def prepare_dialogues(
        self, dialogues_data: list, characters: Dict[str, Character]
    ) -> List[Dialogue]:
        """
        Load the provided character mapping into the repository and transform raw
        dialogues data into domain Dialogue objects.
        """
        if not dialogues_data:
            raise ValueError("At least one dialogue is required")

        self.character_repository.load_from_dict(characters)

        loaded_dialogues: List[Dialogue] = []
        for dialogue_data in dialogues_data:
            if not dialogue_data:
                raise ValueError("Dialogue must contain at least one line")

            lines: List[Line] = []
            for item in dialogue_data:
                character_name = item["character"].lower()
                phrase = item["phrase"]
                voice_id = self.character_repository.get_voice_id(character_name)
                lines.append(Line(speaker=voice_id, text=phrase))

            if lines:
                loaded_dialogues.append(Dialogue(lines=lines))

        return loaded_dialogues
