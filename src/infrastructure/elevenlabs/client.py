from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from src.infrastructure.services.environment_service import (
    ELEVENLABS_API_KEY,
    VOICE_SETTINGS,
)


class ElevenLabsClient:
    def __init__(self):
        self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    def text_to_speech(self, text: str, voice_id: str):
        """
        Synchronous version using ElevenLabs SDK
        """
        try:
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(**VOICE_SETTINGS),
            )
            return b"".join(audio_stream)
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def speech_to_text_json_v2(
        self,
        file_path: str,
        model_id: str,
        language_code: str,
        num_speakers: int,
        diarize: bool,
        timestamps_granularity: str,
    ):
        """
        Converts speech to text using the ElevenLabs API, requesting word-level timestamps.
        Returns the JSON response as a dictionary.
        """
        with open(file_path, "rb") as audio_file:
            response = self.client.speech_to_text.convert(
                model_id=model_id,
                file=audio_file,
                language_code=language_code,
                num_speakers=num_speakers,
                diarize=diarize,
                timestamps_granularity=timestamps_granularity,
            )

        # The response object is a Pydantic model. We convert it to a dict.
        return response.model_dump(exclude_none=True)
