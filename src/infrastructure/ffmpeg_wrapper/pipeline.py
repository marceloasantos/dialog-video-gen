"""Video generation pipeline orchestration"""

import os
import tempfile
import logging
from .video_processor import VideoProcessor
from typing import Dict
from src.domain.entities.alignment import CropAlignment

logger = logging.getLogger(__name__)


class VideoGenerationPipeline:
    """Orchestrates the complete video generation pipeline"""

    def __init__(self, video_processor: VideoProcessor):
        self.video_processor = video_processor

    def generate_video_with_subtitles_and_audio(
        self,
        video_file: str,
        audio_file: str,
        ass_file: str,
        output_file: str,
        alignment: CropAlignment,
        start_time: float,
        speaker_mapping: Dict,
    ) -> None:
        """
        Complete video generation pipeline using ffmpeg:
        1. Crop video to 9:16 aspect ratio
        2. Add styled subtitles from an ASS file and speaker images
        3. Combine with audio

        Args:
            video_file: Input video file path
            audio_file: Audio file path
            ass_file: ASS subtitle file path
            output_file: Final output file path
            start_time: Start time in seconds for video cropping
            speaker_mapping: A mapping of speaker IDs to voice configurations
            alignment: Crop alignment enum (CENTER or LEFT; ALTERNATE resolved earlier)
        """
        # Get audio duration for video length
        audio_duration = self.video_processor.media_info_extractor.get_audio_duration(
            audio_file
        )

        # Check if ASS file exists
        if not os.path.exists(ass_file):
            raise FileNotFoundError(f"ASS file not found: {ass_file}.")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Crop video to 9:16 aspect ratio
            cropped_video = os.path.join(temp_dir, "cropped_video.mp4")
            logger.info("Step 1: Cropping video to 9:16 aspect ratio...")
            latest_video = self.video_processor.crop_video_to_aspect_ratio(
                video_file,
                cropped_video,
                alignment=alignment,
                target_aspect="9:16",
                start_time=start_time,
                duration=audio_duration,
            )

            # Step 2: Add speaker images to video
            video_with_images = os.path.join(temp_dir, "video_with_images.mp4")
            logger.info("Step 2: Adding speaker images to video...")
            latest_video = self.video_processor.add_speaker_images_to_video(
                latest_video, ass_file, video_with_images, speaker_mapping
            )

            # Step 3: Add subtitles to video
            video_with_subs = os.path.join(temp_dir, "video_with_subtitles.mp4")
            logger.info("Step 3: Adding subtitles to video...")
            latest_video = self.video_processor.add_subtitles_to_video(
                latest_video, ass_file, video_with_subs
            )

            # Step 4: Combine video with audio
            video_with_audio = os.path.join(temp_dir, "video_with_audio.mp4")
            logger.info("Step 4: Combining video with audio...")
            latest_video = self.video_processor.combine_video_audio(
                latest_video, audio_file, video_with_audio
            )

            # Step 5: Copy to destination
            logger.info("Step 5: Copying video to destination...")
            self.video_processor.copy_video_to_destination(latest_video, output_file)

            logger.info(f"Video generation completed successfully: {output_file}")
