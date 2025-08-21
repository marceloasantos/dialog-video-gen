from abc import ABC, abstractmethod


class IPresignedUrlProvider(ABC):
    """Optional port for storage implementations that can generate presigned URLs."""

    @abstractmethod
    def generate_presigned_get_url(
        self, relative_path: str, expires_in_seconds: int
    ) -> str:
        """Generate a presigned GET URL for reading an object at relative_path."""
