from typing import List, Dict
from src.domain.entities.dialogue import Dialogue, Line
from src.domain.entities.character import Character
from src.domain.ports.repositories import ICharacterRepository
from src.domain.ports.storage import IStorage


class DataPreparationService:
    """Service responsible for preparing and transforming input data into domain objects."""

    def __init__(
        self, character_repository: ICharacterRepository, input_storage: IStorage
    ):
        self.character_repository = character_repository
        self.input_storage = input_storage

    def prepare_characters(self, characters_data: dict) -> Dict[str, Character]:
        """
        Transform characters into domain models with instantiated image file handles.

        Returns:
            Dict[str, Character]: Mapping of character name to domain Character.
        """
        domain_characters: Dict[str, Character] = {}
        for name, char_dict in characters_data.items():
            image_path = char_dict.get("image_file")
            if image_path is None:
                raise ValueError(f"Character '{name}' is missing 'image_file' field")
            image_file = self.input_storage.file(image_path)
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
