from abc import ABC, abstractmethod
from typing import Dict, Optional
from src.domain.entities.character import Character
from src.domain.entities.dialogue import VoiceId


class ICharacterRepository(ABC):
    """Abstract interface for character repository operations."""

    @abstractmethod
    def load_from_dict(self, data: Dict[str, Character]) -> None:
        """Load character configurations from a dictionary of domain Character models."""
        pass

    @abstractmethod
    def get_voice_id(self, character_name: str) -> VoiceId:
        """Retrieves the voice ID for a given character name."""
        pass

    @abstractmethod
    def get_all_characters(self) -> Dict[str, Character]:
        """Returns the entire dictionary of character configurations."""
        pass


class IVoiceConfigService(ABC):
    """Abstract interface for voice configuration operations."""

    @abstractmethod
    def get_config_for_voice(self, voice_id: VoiceId) -> Optional[Character]:
        """Retrieves the configuration for a given VoiceId."""
        pass
