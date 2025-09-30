import os
import hashlib
import json
from typing import Dict
from src.infrastructure.elevenlabs import ElevenLabsClient
from src.domain.ports.storage import IStorage
from src.domain.entities.character import Character
from src.domain.entities.segment_boundary import SegmentBoundary
from .ass_generator import AssGenerator


class SubtitleGenerator:
    def __init__(self, elevenlabs_client: ElevenLabsClient, cache_storage: IStorage):
        self.elevenlabs_client = elevenlabs_client
        self.ass_generator = AssGenerator()
        self.cache_storage = cache_storage

    def _get_cache_key(
        self,
        file_path: str,
        model_id: str,
        language_code: str,
        num_speakers: int,
        diarize: bool,
        additional_formats: str,
    ) -> str:
        with open(file_path, "rb") as f:
            file_content = f.read()

        cache_payload = {
            "file_content": hashlib.sha256(file_content).hexdigest(),
            "model_id": model_id,
            "language_code": language_code,
            "num_speakers": num_speakers,
            "diarize": diarize,
            "additional_formats": json.loads(additional_formats),
        }
        return hashlib.sha256(
            json.dumps(cache_payload, sort_keys=True).encode()
        ).hexdigest()

    def get_word_timestamps_from_audio(self, audio_path: str) -> dict:
        """
        Generates word-level timestamps for an audio file, using cache if available.
        Returns the JSON response from the API.
        """
        model_id = "scribe_v1"
        language_code = "pt"
        num_speakers = 2
        diarize = True
        # Request word-level timestamps
        additional_formats = json.dumps(
            [{"format": "json-v2", "timestamps_granularity": "word"}]
        )

        cache_key = self._get_cache_key(
            file_path=audio_path,
            model_id=model_id,
            language_code=language_code,
            num_speakers=num_speakers,
            diarize=diarize,
            additional_formats=additional_formats,
        )
        cache_file = self.cache_storage.file(
            os.path.join("word_timestamps", f"{cache_key}.json")
        )

        if cache_file.exists():
            print(" -> Word timestamps found in cache.")
            cached_text = cache_file.read_text(encoding="utf-8")
            return json.loads(cached_text)
        else:
            print(" -> Generating word timestamps via API and saving to cache.")
            response_dict = self.elevenlabs_client.speech_to_text_json_v2(
                file_path=audio_path,
                model_id=model_id,
                language_code=language_code,
                num_speakers=num_speakers,
                diarize=diarize,
                timestamps_granularity="word",
            )

            # Cache the original content
            cache_file.write_text(json.dumps(response_dict), encoding="utf-8")

            return response_dict

    def generate_ass_subtitles(
        self,
        audio_path: str,
        output_ass_path: str,
        font_size: int,
        alignment: int,
        margin_v: int,
        outline: int,
        speaker_mapping: Dict[str, Character],
        segment_boundaries: list[SegmentBoundary],
    ):
        """
        Generates styled ASS subtitles from an audio file.
        Returns the path to the generated ASS file.
        """
        word_data = self.get_word_timestamps_from_audio(audio_path)

        self.ass_generator.generate_ass_from_words(
            word_data,
            output_ass_path,
            font_size=font_size,
            alignment=alignment,
            margin_v=margin_v,
            outline=outline,
            speaker_mapping=speaker_mapping,
            segment_boundaries=segment_boundaries,
        )
        return output_ass_path
