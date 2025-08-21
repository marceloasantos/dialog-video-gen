from pydantic import BaseModel
from enum import Enum


class CropAlignmentType(str, Enum):
    CENTER = "center"
    LEFT = "left"


class CropAlignment(BaseModel):
    alignment: CropAlignmentType

    def __str__(self) -> str:
        return self.alignment.value
