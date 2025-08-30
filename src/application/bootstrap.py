from src.application.use_cases.create_video_use_case import CreateVideoUseCase
from src.domain.services import AudioService
from src.infrastructure.audio_processing.generation import AudioGenerationService
from src.infrastructure.elevenlabs.client import ElevenLabsClient
from src.infrastructure.ffmpeg_wrapper.factory import FFmpegFactory
from src.infrastructure.services.environment_service import (
    INTRO_JUMPER_MIN_START_TIME,
    PRESIGNED_URL_EXPIRES_IN_SECONDS,
)
from src.infrastructure.subtitle_processing.generation import SubtitleGenerator
from src.infrastructure.storage.factory import (
    create_cache_storage,
    create_input_storage,
    create_output_storage,
)
from src.infrastructure.services.character_repository import CharacterRepository
from src.infrastructure.services.voice_config_service import VoiceConfigService
from src.infrastructure.services.file_processing_service import FileProcessingService


def bootstrap() -> CreateVideoUseCase:
    """
    Initializes core services and returns a use case that expects input data.
    This is the composition root of the application.
    """
    # Infrastructure Services
    elevenlabs_client = ElevenLabsClient()
    cache_storage = create_cache_storage()
    input_storage = create_input_storage()
    output_storage = create_output_storage()
    audio_generator = AudioGenerationService(elevenlabs_client, cache_storage)
    subtitle_generator = SubtitleGenerator(elevenlabs_client, cache_storage)
    ffmpeg_components = FFmpegFactory.create_minimal_setup(input_storage)
    media_info_extractor = ffmpeg_components["media_info_extractor"]

    # Domain Services
    audio_service = AudioService()

    # Infrastructure Services (will be injected as dependencies)
    character_repository = CharacterRepository(input_storage)
    voice_config_service = VoiceConfigService(character_repository)
    file_processing_service = FileProcessingService(input_storage)

    # Use Case (repositories will be created from provided data at execution time)
    create_video_use_case = CreateVideoUseCase(
        audio_service=audio_service,
        audio_generator=audio_generator,
        subtitle_generator=subtitle_generator,
        media_info_extractor=media_info_extractor,
        intro_jumper_min_start_time=INTRO_JUMPER_MIN_START_TIME,
        output_storage=output_storage,
        input_storage=input_storage,
        character_repository=character_repository,
        voice_config_service=voice_config_service,
        file_processing_service=file_processing_service,
        presigned_url_expires_in_seconds=PRESIGNED_URL_EXPIRES_IN_SECONDS,
    )
    return create_video_use_case
