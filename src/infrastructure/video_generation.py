from src.infrastructure.ffmpeg_wrapper.factory import FFmpegFactory
from src.domain.entities.alignment import CropAlignment


def generate_video(
    video_filename: str,
    audio_filename: str,
    ass_filename: str,
    alignment: CropAlignment,
    start_time: float,
    output_filename: str,
    speaker_mapping: dict,
):
    """
    Generate video using pure ffmpeg pipeline for maximum performance.

    This function:
    1. Crops the video to 9:16 aspect ratio
    2. Adds subtitles from ASS file
    3. Combines with audio track
    4. Outputs final video file

    All operations use ffmpeg directly, avoiding moviepy overhead.

    Args:
            video_filename: Path to input video file
            audio_filename: Path to input audio file
            ass_filename: Path to ASS subtitle file
            alignment: Crop alignment enum (CENTER or LEFT; ALTERNATE is resolved earlier)
            start_time: Start time in seconds for video cropping
            output_filename: Output file name
            speaker_mapping: A mapping of speaker IDs to voice configurations.
    """

    # Initialize FFmpeg components
    ffmpeg_components = FFmpegFactory.create_minimal_setup()
    pipeline = ffmpeg_components["pipeline"]

    # Generate video using pure ffmpeg pipeline
    pipeline.generate_video_with_subtitles_and_audio(
        video_file=video_filename,
        audio_file=audio_filename,
        ass_file=ass_filename,
        output_file=output_filename,
        alignment=alignment,
        start_time=start_time,
        speaker_mapping=speaker_mapping,
    )
