from src.domain.ports.storage import IStorage
from src.domain.ports.presigned_url import IPresignedUrlProvider


class VideoRetrievalService:
    """Service responsible for retrieving produced videos from storage."""

    def __init__(self, output_storage: IStorage):
        self.output_storage = output_storage

    def get_video(self, video_id: str) -> bytes:
        """
        Read a produced video from output storage by its relative path.

        Args:
            video_id: The relative path/ID of the video in storage

        Returns:
            bytes: The video file content
        """
        return self.output_storage.file(video_id).read_bytes()

    def get_video_presigned_url(
        self, video_id: str, expires_in_seconds: int
    ) -> str | None:
        """Return a presigned GET URL if supported by the storage, else None."""
        if isinstance(self.output_storage, IPresignedUrlProvider):
            return self.output_storage.generate_presigned_get_url(
                video_id, expires_in_seconds
            )
        return None
