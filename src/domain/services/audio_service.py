from pydub import AudioSegment
from typing import List


class AudioService:
    def concatenate_audios(self, audio_segments: List[AudioSegment]) -> AudioSegment:
        if not audio_segments:
            return AudioSegment.empty()

        final_audio = AudioSegment.empty()
        for segment in audio_segments:
            final_audio += segment
        return final_audio
