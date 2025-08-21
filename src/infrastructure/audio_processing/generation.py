import os
import hashlib
import json
import io
from pydub import AudioSegment
from src.infrastructure.elevenlabs import ElevenLabsClient
from src.domain.ports.storage import IStorage
from src.infrastructure.services.environment_service import VOICE_SETTINGS


class AudioGenerationService:
    def __init__(self, elevenlabs_client: ElevenLabsClient, cache_storage: IStorage):
        self.elevenlabs_client = elevenlabs_client
        self.cache_storage = cache_storage

    def _get_cache_key(
        self, text: str, voice_id: str, model_id: str, voice_settings: dict
    ) -> str:
        cache_payload = {
            "text": text,
            "voice_id": voice_id,
            "model_id": model_id,
            "voice_settings": voice_settings,
        }
        return hashlib.sha256(
            json.dumps(cache_payload, sort_keys=True).encode()
        ).hexdigest()

    def get_audio_segment(self, line: dict) -> AudioSegment:
        print(f"Processing: {line['speaker']}")

        cache_key = self._get_cache_key(
            text=line["text"],
            voice_id=line["speaker"],
            model_id="eleven_multilingual_v2",
            voice_settings=VOICE_SETTINGS,
        )
        cache_file = self.cache_storage.file(os.path.join("audio", f"{cache_key}.mp3"))

        if cache_file.exists():
            print(" -> Audio found in cache.")
            audio_bytes = cache_file.read_bytes()
            return AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        else:
            print(" -> Generating via API and saving to cache.")
            audio_bytes = self.elevenlabs_client.text_to_speech(
                text=line["text"],
                voice_id=line["speaker"],
            )
            cache_file.write_bytes(audio_bytes)
            return AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
