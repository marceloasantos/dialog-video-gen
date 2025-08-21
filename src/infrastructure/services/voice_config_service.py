from typing import Dict, Optional

from src.domain.entities.dialogue import VoiceId
from src.domain.entities.character import Character
from src.domain.ports.repositories import IVoiceConfigService


class VoiceConfigService(IVoiceConfigService):
    """Provides UI and generation configurations for voices."""

    def __init__(self, character_repository):
        self.character_repository = character_repository

    def get_config_for_voice(self, voice_id: VoiceId) -> Optional[Character]:
        """Retrieves the configuration for a given VoiceId."""
        characters: Dict[str, Character] = (
            self.character_repository.get_all_characters()
        )
        for cfg in characters.values():
            if cfg.voice_id == voice_id:
                return cfg
        return None
