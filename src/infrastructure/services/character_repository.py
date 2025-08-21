from typing import Dict, List, Optional

from src.domain.entities.dialogue import VoiceId
from src.domain.entities.character import Character
from src.domain.ports.repositories import ICharacterRepository
from src.domain.ports.storage import IStorage


class CharacterNotFoundError(Exception):
    """Raised when a character is not found in the configuration."""

    def __init__(self, character_name: str, available_characters: List[str]):
        self.character_name = character_name
        self.available_characters = available_characters
        super().__init__(
            f"Character '{character_name}' not found. "
            f"Available characters are: {', '.join(available_characters)}. "
            f"Please add the character in the provided API payload."
        )


class CharacterRepository(ICharacterRepository):
    """Loads and provides access to character configurations provided in-memory."""

    _characters: Dict[str, Character]

    def __init__(self, input_storage: Optional[IStorage] = None):
        self._characters = {}
        self._input_storage = input_storage

    def load_from_dict(self, data: Dict[str, Character]) -> None:
        """Loads character configurations from a dictionary of domain Character models."""
        self._characters = self._validate_and_load_characters(data)

    def _validate_and_load_characters(
        self, data: Dict[str, Character]
    ) -> Dict[str, Character]:
        """Validates and loads character data using the domain model.

        Expects a mapping from character name (case-insensitive) to a domain Character instance.
        """
        loaded_characters: Dict[str, Character] = {}
        for name, character in data.items():
            if not isinstance(character, Character):
                raise TypeError(
                    f"Invalid character entry for '{name}'. Expected a domain Character model, "
                    f"but got: {type(character).__name__}."
                )

            # Validate the provided image handle
            image_file = character.image_file
            if image_file is None:
                raise RuntimeError(f"Character '{name}' is missing image file handle.")

            if not image_file.relative_path or image_file.relative_path.startswith("/"):
                raise ValueError(
                    f"Character '{name}' image_file.relative_path must be storage-relative."
                )

            # If storage available, ensure the file exists in storage
            if (
                self._input_storage
                and not self._input_storage.file(image_file.relative_path).exists()
            ):
                raise RuntimeError(
                    f"Image file for character '{name}' not found in storage at '{image_file.relative_path}'."
                )

            loaded_characters[name.lower()] = character
        return loaded_characters

    def get_voice_id(self, character_name: str) -> VoiceId:
        """
        Retrieves the voice ID for a given character name.
        """
        character_name = character_name.lower()
        if character_name not in self._characters:
            raise CharacterNotFoundError(character_name, list(self._characters.keys()))

        character = self._characters[character_name]
        return VoiceId(character.voice_id)

    def get_all_characters(self) -> Dict[str, Character]:
        """
        Returns the entire dictionary of character configurations.
        """
        return self._characters.copy()
