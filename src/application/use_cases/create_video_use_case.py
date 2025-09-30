from src.application.services import (
    VideoProductionService,
    DataPreparationService,
    FileManagementService,
    VideoRetrievalService,
)
from src.domain.entities.alignment import CropAlignment, CropAlignmentType
from src.domain.ports.storage import IStorage
from src.domain.ports.repositories import (
    ICharacterRepository,
    IVoiceConfigService,
)
from src.domain.services import AudioService
from src.infrastructure.services.file_processing_service import FileProcessingService
from src.infrastructure.audio_processing.generation import AudioGenerationService
from src.infrastructure.subtitle_processing.generation import SubtitleGenerator
from src.infrastructure.ffmpeg_wrapper.interfaces import IMediaInfoExtractor
import logging
from typing import Literal

logger = logging.getLogger(__name__)


class CreateVideoUseCase:
    """
    Use case responsible for orchestrating the video creation workflow.

    This class follows the Single Responsibility Principle by focusing solely on
    coordinating the video creation process, delegating specific responsibilities
    to specialized services.
    """

    def __init__(
        self,
        audio_service: AudioService,
        audio_generator: AudioGenerationService,
        subtitle_generator: SubtitleGenerator,
        media_info_extractor: IMediaInfoExtractor,
        intro_jumper_min_start_time: int,
        output_storage: IStorage,
        input_storage: IStorage,
        character_repository: ICharacterRepository,
        voice_config_service: IVoiceConfigService,
        file_processing_service: FileProcessingService,
        presigned_url_expires_in_seconds: int,
    ):
        # Core services for video production
        self.audio_service = audio_service
        self.audio_generator = audio_generator
        self.subtitle_generator = subtitle_generator
        self.media_info_extractor = media_info_extractor

        # Video-specific configurations
        self.output_storage = output_storage
        self.input_storage = input_storage
        self.intro_jumper_min_start_time = intro_jumper_min_start_time
        self.presigned_url_expires_in_seconds = presigned_url_expires_in_seconds

        # Domain services
        self.character_repository = character_repository
        self.voice_config_service = voice_config_service

        # Specialized services for different responsibilities
        self.data_preparation_service = DataPreparationService(
            character_repository, input_storage
        )
        self.file_management_service = FileManagementService(file_processing_service)
        self.video_retrieval_service = VideoRetrievalService(output_storage)

    def execute(
        self,
        dialogues_data: list,
        characters_data: dict,
        input_video_path: str,
        crop_alignment: Literal["center", "left"],
        watermark: bool = False,
        watermark_text: str | None = None,
    ):
        """
        Execute the video creation workflow.

        This method orchestrates the entire video creation process by:
        1. Preparing and transforming input data
        2. Managing file operations
        3. Coordinating video production
        """
        logger.info("Preparing characters and dialogues")
        # Prepare characters first, then dialogues
        prepared_characters = self.data_preparation_service.prepare_characters(
            characters_data
        )
        loaded_dialogues = self.data_preparation_service.prepare_dialogues(
            dialogues_data, prepared_characters
        )
        num_dialogues = len(loaded_dialogues)
        logger.info("Prepared input data: dialogues=%s", num_dialogues)
        logger.info("Preparing input video: %s", input_video_path)
        # Manage file operations using specialized service
        with self.file_management_service.prepare_input_video(
            input_video_path
        ) as local_input_video_path:
            # Determine crop alignment using enum coercion from string to enum
            effective_alignment = CropAlignment(
                alignment=CropAlignmentType(crop_alignment)
            )

            # Create and execute the video production service
            video_production_service = VideoProductionService(
                audio_service=self.audio_service,
                audio_generator=self.audio_generator,
                subtitle_generator=self.subtitle_generator,
                media_info_extractor=self.media_info_extractor,
                dialogues=loaded_dialogues,
                voice_config_service=self.voice_config_service,
                local_input_video_path=local_input_video_path,
                crop_alignment=effective_alignment,
                intro_jumper_min_start_time=self.intro_jumper_min_start_time,
                output_storage=self.output_storage,
                # new
                watermark_enabled=watermark,
                watermark_text=watermark_text,
            )
            logger.info("Starting video production for %s dialogues", num_dialogues)

            successful_videos, failed_videos, video_ids = (
                video_production_service.produce_videos()
            )
            return successful_videos, failed_videos, video_ids

    def get_video(self, video_id: str) -> bytes:
        """Read a produced video from output storage by its relative path."""
        return self.video_retrieval_service.get_video(video_id)

    def get_video_presigned_url(self, video_id: str) -> str | None:
        """Return a presigned GET URL if supported by the storage, else None."""
        return self.video_retrieval_service.get_video_presigned_url(
            video_id, self.presigned_url_expires_in_seconds
        )
