"""Video processing operations using FFmpeg"""

import logging
import re
import pysubs2
import tempfile
import os
from typing import Dict, Tuple
from .interfaces import ICommandExecutor, IMediaInfoExtractor, IFileValidator
from .exceptions import FFmpegError
from src.domain.entities.character import Character, CharacterPosition
from src.domain.entities.alignment import CropAlignment as CropAlignmentModel
from src.domain.entities.alignment import CropAlignmentType
from src.domain.ports.storage import IStorage

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing operations"""

    def __init__(
        self,
        command_executor: ICommandExecutor,
        media_info_extractor: IMediaInfoExtractor,
        file_validator: IFileValidator,
        input_storage: IStorage,
    ):
        self.command_executor = command_executor
        self.media_info_extractor = media_info_extractor
        self.file_validator = file_validator
        self.input_storage = input_storage
        self._temp_image_files: list[str] = []

    def _prepare_image_from_storage(self, image_source) -> str:
        """
        Prepare image file from storage for ffmpeg processing.

        Args:
            image_source: An IStoredFile-like object with read_bytes() and optional
            relative_path attribute.

        Returns:
            Local file path to the prepared image
        """
        if not hasattr(image_source, "read_bytes"):
            raise TypeError(
                "image_source must be an IStoredFile-like object with read_bytes()"
            )
        image_bytes = image_source.read_bytes()
        rel_path = getattr(image_source, "relative_path", "")
        _, ext = os.path.splitext(rel_path)
        ext = ext or ".png"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(image_bytes)
        temp_file.close()
        self._temp_image_files.append(temp_file.name)
        return temp_file.name

    def _cleanup_temp_images(self):
        """Clean up temporary image files."""
        for temp_file in self._temp_image_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
        self._temp_image_files.clear()

    def _parse_ass_for_speakers(self, ass_file: str, video_duration: float) -> list:
        """
        Parse ASS file to extract speaker information and timing.
        Merges consecutive events from the same speaker and extends display time.

        Args:
                ass_file: Path to ASS file
                video_duration: Duration of the video in seconds (used for last speaker)

        Returns:
                List of tuples: (start_time, end_time, speaker_id)
        """
        subs = pysubs2.load(ass_file)

        if not subs.events:
            return []

        # First pass: collect raw segments with speaker ID from styles
        raw_segments = []
        for event in subs.events:
            match = re.search(r"speaker_(\d+)", event.style)
            if match:
                speaker_id = match.group(1)
                start_time = event.start / 1000.0  # pysubs2 times are in ms
                end_time = event.end / 1000.0
                raw_segments.append(
                    {"start": start_time, "end": end_time, "id": speaker_id}
                )

        if not raw_segments:
            return []

        # Second pass: merge consecutive segments from the same speaker
        merged_segments = []
        if raw_segments:
            current_segment = raw_segments[0]
            for i in range(1, len(raw_segments)):
                next_segment = raw_segments[i]
                # Merge if same speaker and gap is small (e.g., < 0.2s)
                if (
                    next_segment["id"] == current_segment["id"]
                    and (float(next_segment["start"]) - float(current_segment["end"]))
                    < 0.2
                ):
                    current_segment["end"] = next_segment["end"]
                else:
                    merged_segments.append(current_segment)
                    current_segment = next_segment
            merged_segments.append(current_segment)

        # Third pass: extend each speaker's time until the next speaker appears
        speaker_segments = []
        for i, segment in enumerate(merged_segments):
            start_time = float(segment["start"])  # ensure type
            speaker_id = segment["id"]

            # Find the start time of the next segment with a different speaker
            next_start_time = None
            for j in range(i + 1, len(merged_segments)):
                if merged_segments[j]["id"] != speaker_id:
                    next_start_time = float(merged_segments[j]["start"])  # ensure type
                    break

            # If no next different speaker, extend to video duration or fallback
            extended_end_time = (
                next_start_time if next_start_time is not None else video_duration
            )
            if extended_end_time is None:  # Fallback if no duration and no next speaker
                extended_end_time = float(segment["end"]) + 2.0

            speaker_segments.append((start_time, extended_end_time, speaker_id))

        return speaker_segments

    def _build_speaker_image_filter(
        self,
        speaker_segments: list,
        video_width: int,
        video_height: int,
        speaker_mapping: Dict[str, Character],
    ) -> Tuple[str, str]:
        """
        Build FFmpeg filter for speaker images

        Args:
                speaker_segments: List of speaker timing data
                video_width: Video width
                video_height: Video height

        Returns:
                FFmpeg filter string
        """
        if not speaker_segments:
            return "", ""

        filter_parts = []
        current_input = "[0:v]"  # Start with the main video stream

        for i, (start_time, end_time, speaker_id) in enumerate(speaker_segments):
            character = speaker_mapping.get(speaker_id)
            if not character:
                logger.warning(
                    f"No character config found for speaker_id: {speaker_id}"
                )
                continue

            # Prepare image from storage using character.image_file
            try:
                local_image_path = self._prepare_image_from_storage(
                    character.image_file
                )
            except Exception as e:
                logger.warning(
                    f"Failed to prepare image for speaker_id: {speaker_id}, error: {e}"
                )
                continue

            # Get original image dimensions
            img_width, img_height = self.media_info_extractor.get_image_dimensions(
                local_image_path
            )

            # Calculate scaled dimensions, maintaining aspect ratio
            aspect_ratio = img_height / img_width
            scaled_width = int(video_width * character.scale)
            scaled_height = int(scaled_width * aspect_ratio)

            # Validate image size
            if scaled_width > video_width:
                raise FFmpegError(
                    f"Scaled image for speaker {speaker_id} is wider than the video ({scaled_width}px > {video_width}px)"
                )
            if scaled_height > video_height:
                raise FFmpegError(
                    f"Scaled image for speaker {speaker_id} is taller than the video ({scaled_height}px > {video_height}px)"
                )

            # Calculate position
            if character.position == CharacterPosition.BOTTOM_LEFT:
                image_x = f"{character.margin}"
            elif character.position == CharacterPosition.BOTTOM_RIGHT:
                image_x = f"main_w - overlay_w - {character.margin}"
            elif character.position == CharacterPosition.BOTTOM_CENTER:
                image_x = "(main_w - overlay_w) / 2"
            else:
                # This case should not be reachable if Character model validation is correct
                raise ValueError(
                    f"Invalid image position '{character.position}' for speaker {speaker_id}"
                )

            image_y = f"main_h - overlay_h - {character.margin}"

            escaped_image_path = local_image_path.replace("\\", "\\\\").replace(
                ":", "\\:"
            )

            movie_filter = f"movie=filename='{escaped_image_path}'[raw_img{i}];"
            filter_parts.append(movie_filter)

            scale_filter = f"[raw_img{i}]scale={scaled_width}:-1[img{i}];"
            filter_parts.append(scale_filter)

            output_stream_name = f"[out{i}]"
            overlay_filter = f"{current_input}[img{i}]overlay=x={image_x}:y={image_y}:enable='between(t,{start_time},{end_time})'{output_stream_name};"
            filter_parts.append(overlay_filter)

            current_input = output_stream_name

        # The filter parts create a chain, but we need to remove the final semicolon
        # and not return an output mapping, as the next filter in the chain will use it.
        # The last `current_input` will be used to link to the ass filter.
        full_filter = "".join(filter_parts)

        # We need to return the final output stream name to chain it
        return full_filter, current_input

    def crop_video_to_aspect_ratio(
        self,
        input_video: str,
        output_video: str,
        alignment: CropAlignmentModel,
        target_aspect: str = "9:16",
        start_time: float = 0,
        duration: float | None = None,
    ) -> str:
        """
        Crop video to target aspect ratio using ffmpeg

        Args:
                input_video: Input video file path
                output_video: Output video file path
                target_aspect: Target aspect ratio (e.g., "9:16")
                start_time: Start time in seconds
                duration: Duration in seconds (None for full length)
                alignment: Crop alignment entity ("center" or "left")

        Returns:
                Path to the processed video file
        """
        if not self.file_validator.validate_file_exists(input_video):
            raise FFmpegError(f"Input video file not found: {input_video}")

        # Get original video dimensions
        width, height = self.media_info_extractor.get_video_dimensions(input_video)

        # Calculate crop dimensions for 9:16 aspect ratio
        if target_aspect == "9:16":
            target_width = int(height * 9 / 16)
            if target_width > width:
                target_width = width
                target_height = int(width * 16 / 9)
            else:
                target_height = height

            match alignment.alignment:
                case CropAlignmentType.CENTER:
                    x_offset = (width - target_width) // 2
                case CropAlignmentType.LEFT:
                    x_offset = 0
                case _:
                    raise ValueError(
                        f"Alignment '{alignment.alignment.value}' not supported. Use 'center' or 'left'"
                    )

            y_offset = (height - target_height) // 2
        else:
            raise ValueError(f"Aspect ratio {target_aspect} not supported yet")

        # Build ffmpeg command
        args = []

        # Input seeking (faster than output seeking)
        if start_time > 0:
            args.extend(["-ss", str(start_time)])

        args.extend(["-i", input_video])

        # Duration
        if duration:
            args.extend(["-t", str(duration)])

        # Video filters
        crop_filter = f"crop={target_width}:{target_height}:{x_offset}:{y_offset}"
        args.extend(["-vf", crop_filter])

        # Encoding settings
        args.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "23",
                "-threads",
                "8",
                "-an",  # No audio for now
                "-y",  # Overwrite output
                output_video,
            ]
        )

        self.command_executor.run_ffmpeg_command(args, timeout=300)
        logger.info(f"Video cropped successfully: {output_video}")
        return output_video

    def add_subtitles_to_video(
        self, input_video: str, subtitle_file: str, output_video: str
    ) -> str:
        """
        Add subtitles to video using an ASS file.

        Args:
                input_video: Input video file path
                subtitle_file: Subtitle file path (.ass)
                output_video: Output video file path

        Returns:
                Path to the processed video file
        """
        if not self.file_validator.validate_file_exists(input_video):
            raise FFmpegError(f"Input video file not found: {input_video}")
        if not self.file_validator.validate_file_exists(subtitle_file):
            raise FFmpegError(f"Subtitle file not found: {subtitle_file}")

        escaped_path = subtitle_file.replace("\\", "\\\\").replace(":", "\\:")
        subtitle_filter = f"ass='{escaped_path}'"

        args = [
            "-i",
            input_video,
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-threads",
            "8",
            "-c:a",
            "copy",
            "-y",
            output_video,
        ]

        self.command_executor.run_ffmpeg_command(args, timeout=300)
        logger.info(f"Subtitles added successfully to {output_video}")
        return output_video

    def add_speaker_images_to_video(
        self,
        input_video: str,
        subtitle_file: str,
        output_video: str,
        speaker_mapping: Dict[str, Character],
    ) -> str:
        """
        Add speaker images to video based on speaker segments from an ASS file.

        Args:
                input_video: Input video file path
                subtitle_file: Subtitle file to parse for speaker timing
                output_video: Output video file path
                speaker_mapping: Mapping of speaker IDs to character configurations

        Returns:
                Path to the processed video file
        """
        if not self.file_validator.validate_file_exists(input_video):
            raise FFmpegError(f"Input video file not found: {input_video}")

        if not self.file_validator.validate_file_exists(subtitle_file):
            raise FFmpegError(f"Subtitle file not found: {subtitle_file}")

        video_width, video_height = self.media_info_extractor.get_video_dimensions(
            input_video
        )
        video_duration = self.media_info_extractor.get_video_duration(input_video)

        speaker_segments = self._parse_ass_for_speakers(subtitle_file, video_duration)
        if not speaker_segments:
            logger.warning(
                "No speaker segments found in subtitle file. Skipping image addition and copying video."
            )
            self.command_executor.run_ffmpeg_command(
                ["-i", input_video, "-c", "copy", "-y", output_video]
            )
            return output_video

        filter_tuple = self._build_speaker_image_filter(
            speaker_segments, video_width, video_height, speaker_mapping
        )
        if not filter_tuple or not filter_tuple[0]:
            logger.warning(
                "Could not build speaker image filter. Skipping image addition and copying video."
            )
            self.command_executor.run_ffmpeg_command(
                ["-i", input_video, "-c", "copy", "-y", output_video]
            )
            return output_video

        speaker_image_filter_str, final_video_stream = filter_tuple

        complex_filter = f"{speaker_image_filter_str.rstrip(';')}"

        args = [
            "-i",
            input_video,
            "-filter_complex",
            complex_filter,
            "-map",
            final_video_stream,
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-threads",
            "8",
            "-c:a",
            "copy",
            "-y",
            output_video,
        ]

        try:
            self.command_executor.run_ffmpeg_command(args, timeout=600)
            logger.info(f"Speaker images added successfully to {output_video}")
            return output_video
        finally:
            # Clean up temporary image files
            self._cleanup_temp_images()

    def combine_video_audio(
        self, video_file: str, audio_file: str, output_file: str
    ) -> str:
        """
        Combine video and audio files using ffmpeg

        Args:
                video_file: Video file path
                audio_file: Audio file path
                output_file: Output file path (temporary file for composability)

        Returns:
                Path to the combined video file
        """
        if not self.file_validator.validate_file_exists(video_file):
            raise FFmpegError(f"Video file not found: {video_file}")

        if not self.file_validator.validate_file_exists(audio_file):
            raise FFmpegError(f"Audio file not found: {audio_file}")

        args = [
            "-i",
            video_file,
            "-i",
            audio_file,
            "-c:v",
            "copy",  # Copy video stream
            "-c:a",
            "aac",  # Re-encode audio as AAC
            "-b:a",
            "128k",  # Audio bitrate
            "-shortest",  # End when shortest input ends
            "-threads",
            "8",
            "-y",
            output_file,
        ]

        self.command_executor.run_ffmpeg_command(args, timeout=600)
        logger.info(f"Video and audio combined successfully: {output_file}")
        return output_file

    def copy_video_to_destination(
        self, source_video: str, destination_video: str
    ) -> str:
        """
        Copy video file to final destination

        Args:
                source_video: Source video file path
                destination_video: Destination video file path

        Returns:
                Path to the destination video file
        """
        if not self.file_validator.validate_file_exists(source_video):
            raise FFmpegError(f"Source video file not found: {source_video}")

        args = [
            "-i",
            source_video,
            "-c",
            "copy",  # Copy all streams without re-encoding
            "-y",
            destination_video,
        ]

        self.command_executor.run_ffmpeg_command(args, timeout=300)
        logger.info(f"Video copied to destination successfully: {destination_video}")
        return destination_video

    def add_text_watermark_to_video(
        self, input_video: str, output_video: str, text: str
    ) -> str:
        """Draw a text watermark at the top of the video using ffmpeg drawtext."""
        if not self.file_validator.validate_file_exists(input_video):
            raise FFmpegError(f"Input video file not found: {input_video}")

        # Escape characters for drawtext
        escaped_text = (
            text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        )

        # Common font found on most Linux distros; can be overridden later if needed
        fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(fontfile):
            # Fallback: let ffmpeg pick default font if available
            drawtext_expr = (
                f"drawtext=text='{escaped_text}':fontcolor=white@0.6:fontsize=32:"
                "box=1:boxcolor=black@0.25:boxborderw=8:x=(w-text_w)/2:y=40"
            )
        else:
            drawtext_expr = (
                f"drawtext=fontfile='{fontfile}':text='{escaped_text}':fontcolor=white@0.6:fontsize=32:"
                "box=1:boxcolor=black@0.25:boxborderw=8:x=(w-text_w)/2:y=40"
            )

        args = [
            "-i",
            input_video,
            "-vf",
            drawtext_expr,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-threads",
            "8",
            "-c:a",
            "copy",
            "-y",
            output_video,
        ]

        self.command_executor.run_ffmpeg_command(args, timeout=300)
        logger.info(f"Watermark added successfully to {output_video}")
        return output_video
