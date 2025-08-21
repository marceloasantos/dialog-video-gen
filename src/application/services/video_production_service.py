import os
import random
import tempfile
from typing import Dict, List
from src.domain.entities.character import Character
from src.domain.entities.alignment import CropAlignment

from src.domain.entities.dialogue import Dialogue
from src.domain.services.speaker_mapping_service import SpeakerMappingService
from src.domain.ports.storage import IStorage
from src.domain.ports.repositories import IVoiceConfigService
from src.infrastructure.video_generation import generate_video
from src.infrastructure.audio_processing.generation import AudioGenerationService
from src.domain.services.audio_service import AudioService
from src.infrastructure.subtitle_processing.generation import SubtitleGenerator
from src.infrastructure.ffmpeg_wrapper import IMediaInfoExtractor
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class VideoProductionService:
    def __init__(
        self,
        audio_service: AudioService,
        audio_generator: AudioGenerationService,
        subtitle_generator: SubtitleGenerator,
        media_info_extractor: IMediaInfoExtractor,
        dialogues: List[Dialogue],
        voice_config_service: IVoiceConfigService,
        local_input_video_path: str,
        crop_alignment: CropAlignment,
        intro_jumper_min_start_time: int,
        output_storage: IStorage,
    ):
        self.audio_service = audio_service
        self.audio_generator = audio_generator
        self.subtitle_generator = subtitle_generator
        self.media_info_extractor = media_info_extractor
        self.dialogues = dialogues
        self.voice_config_service = voice_config_service
        self.local_input_video_path = local_input_video_path
        self.output_storage = output_storage
        self.crop_alignment = crop_alignment
        self.intro_jumper_min_start_time = intro_jumper_min_start_time

    def produce_videos(self):
        """
        Produces videos for all dialogues found by the repository.
        """
        if not self.dialogues:
            print("No dialogues found to process.")
            logger.info("No dialogues found to process")
            return 0, 0, []

        successful_videos = 0
        failed_videos = 0
        generated_video_ids: List[str] = []

        total_dialogues = len(self.dialogues)
        logger.info("Beginning dialogue processing: %s dialogues", total_dialogues)

        for i, dialogue in enumerate(self.dialogues):
            result = self.process_dialogue(i, dialogue, total_dialogues)
            if result:
                successful_videos += 1
                generated_video_ids.append(result)
            else:
                failed_videos += 1

        return successful_videos, failed_videos, generated_video_ids

    def process_dialogue(
        self,
        dialogue_index: int,
        dialogue: Dialogue,
        total_dialogues: int,
    ):
        print(f"🎬 Processing dialogue {dialogue_index + 1}/{total_dialogues}...")

        try:
            # Build audio segments for lines
            audio_segments = []
            for line in dialogue.lines:
                line_data = {"text": line.text, "speaker": line.speaker}
                audio_segments.append(self.audio_generator.get_audio_segment(line_data))

            final_audio = self.audio_service.concatenate_audios(audio_segments)

            # Export concatenated audio to a temporary WAV file
            tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp_audio.close()
            base_filename = tmp_audio.name
            final_audio.export(base_filename, format="wav")

            audio_segments.clear()
            del final_audio

            speaker_to_voice_id_map = (
                SpeakerMappingService.create_speaker_mapping_from_dialogue(dialogue)
            )

            # Resolve character configurations for each speaker
            resolved_configs: Dict[str, Character | None] = {
                speaker_id: self.voice_config_service.get_config_for_voice(voice_id)
                for speaker_id, voice_id in speaker_to_voice_id_map.items()
            }

            # Collect any missing configurations and raise an error if found
            missing = {
                sid: vid
                for sid, vid in speaker_to_voice_id_map.items()
                if resolved_configs[sid] is None
            }
            if missing:
                missing_list = ", ".join(
                    f"speaker_id={sid}, voice_id={vid}" for sid, vid in missing.items()
                )
                raise ValueError(
                    f"No Character configuration found for the following speakers: {missing_list}. "
                    "Ensure each VoiceId used in the dialogue has a corresponding Character configured."
                )

            speaker_config_map: Dict[str, Character] = {
                sid: cfg for sid, cfg in resolved_configs.items() if cfg is not None
            }

            subtitle_style_options = {
                "font_size": 24,
                "alignment": 2,
                "margin_v": 150,
                "outline": 2,
            }

            ass_filename = self.process_subtitles(
                base_filename,
                speaker_mapping=speaker_config_map,
                font_size=subtitle_style_options["font_size"],
                alignment=subtitle_style_options["alignment"],
                margin_v=subtitle_style_options["margin_v"],
                outline=subtitle_style_options["outline"],
            )

            video_filename = self.local_input_video_path
            if not os.path.exists(video_filename):
                raise FileNotFoundError(f"Video file not found: {video_filename}")

            audio_duration = self.media_info_extractor.get_audio_duration(base_filename)
            video_duration = self.media_info_extractor.get_video_duration(
                video_filename
            )

            # Intro jumper feature: never select video segments from the first N minutes
            # Configured via INTRO_JUMPER_MIN_START_TIME environment variable

            if video_duration <= audio_duration:
                start_time = 0
                print(
                    f"📹 Video duration ({video_duration:.1f}s) ≤ audio duration ({audio_duration:.1f}s), starting from beginning"
                )
            else:
                max_start_time = video_duration - audio_duration
                # Ensure we never start before the configured minimum time
                min_start_time = min(self.intro_jumper_min_start_time, max_start_time)

                if min_start_time >= max_start_time:
                    # If the intro jumper constraint makes it impossible to fit the audio,
                    # fall back to starting from the beginning
                    print(
                        f"⚠️ Video too short to skip intro ({self.intro_jumper_min_start_time}s), starting from beginning"
                    )
                    start_time = 0
                else:
                    start_time = random.uniform(min_start_time, max_start_time)
                    print(
                        f"🎯 Selected random start time: {start_time:.1f}s (range: {min_start_time:.1f}s - {max_start_time:.1f}s)"
                    )

            date_tag = datetime.now().strftime("%Y_%m_%d")
            unique_tag = uuid.uuid4().hex
            rel_output_name = f"video_{date_tag}_{unique_tag}.mp4"
            # Create a temp output and then save into output storage
            tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp_output.close()
            final_video_name = tmp_output.name

            print(f"🎬 Using alignment: {self.crop_alignment}")

            try:
                generate_video(
                    video_filename,
                    base_filename,
                    ass_filename,
                    self.crop_alignment,
                    start_time=start_time,
                    output_filename=final_video_name,
                    speaker_mapping=speaker_config_map,
                )
                # Persist output into storage
                with open(final_video_name, "rb") as f:
                    video_bytes = f.read()
                self.output_storage.file(rel_output_name).write_bytes(video_bytes)
            finally:
                try:
                    os.remove(final_video_name)
                except OSError:
                    pass
                try:
                    os.remove(base_filename)
                except OSError:
                    pass
                try:
                    os.remove(ass_filename)
                except OSError:
                    pass

            print(
                f"✅ Video {dialogue_index + 1} generated successfully: {rel_output_name}"
            )
            return rel_output_name

        except Exception as e:
            print(f"❌ Error processing dialogue {dialogue_index + 1}: {e}")
            return None

    def process_subtitles(
        self,
        output_filename: str,
        font_size: int,
        alignment: int,
        margin_v: int,
        outline: int,
        speaker_mapping: dict = None,
    ):
        print(f"📝 Processing subtitles for: {os.path.basename(output_filename)}")

        ass_filename = output_filename.replace(".wav", ".ass")

        self.subtitle_generator.generate_ass_subtitles(
            output_filename,
            ass_filename,
            font_size=font_size,
            alignment=alignment,
            margin_v=margin_v,
            outline=outline,
            speaker_mapping={k: v for k, v in speaker_mapping.items()},
        )

        print(f"✅ Subtitles processed: {os.path.basename(ass_filename)}")
        return ass_filename
