from typing import Dict, List
from src.domain.entities.dialogue import VoiceId, Dialogue


class SpeakerMappingService:
    """Service to handle dynamic speaker mapping between domain voices and speaker indexes."""

    @staticmethod
    def create_speaker_mapping_from_dialogue(dialogue: Dialogue) -> Dict[str, VoiceId]:
        """
        Creates a mapping from a speaker index string (e.g., "0", "1") to a domain VoiceId
        based on the order of first appearance in the dialogue.

        Args:
            dialogue: The dialogue containing the conversation.

        Returns:
            A dictionary mapping the speaker index (as a string) to the corresponding VoiceId.
        """
        first_appearance_order: List[VoiceId] = []
        seen_voices = set()

        for line in dialogue.lines:
            if line.speaker not in seen_voices:
                first_appearance_order.append(line.speaker)
                seen_voices.add(line.speaker)

        speaker_mapping = {
            str(index): voice for index, voice in enumerate(first_appearance_order)
        }

        return speaker_mapping
