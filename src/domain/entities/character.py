from typing import List
from pydantic import BaseModel, Field
from enum import Enum
from src.domain.ports.storage import IStoredFile


class CharacterPosition(str, Enum):
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_CENTER = "bottom_center"


class Character(BaseModel):
    """Represents a character's configuration for video generation."""

    voice_id: str
    image_file: IStoredFile
    position: CharacterPosition
    scale: float = Field(gt=0, description="Image scale, must be greater than 0.")
    margin: int = Field(ge=0, description="Margin from the video edges in pixels.")
    primary_color: List[int]
    secondary_color: List[int]

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True
