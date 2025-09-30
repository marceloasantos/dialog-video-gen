from pydantic import BaseModel, Field, StrictStr, model_validator
from pydantic import ConfigDict
from typing import List, Dict, Tuple, Literal, Annotated, Self


class DialogueLine(BaseModel):
    character: StrictStr
    phrase: StrictStr


class Character(BaseModel):
    voice_id: StrictStr
    image_file: StrictStr = Field(
        description=(
            "Either a storage-relative image path (e.g., 'images/peter.png') or an HTTP(S) URL. "
            "When a URL is provided, the image will be downloaded and must be at most 10 MB."
        )
    )
    position: Literal["bottom_left", "bottom_right", "bottom_center"]
    scale: float = Field(gt=0.0)
    margin: int = Field(ge=0)
    primary_color: Tuple[
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
    ]
    secondary_color: Tuple[
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
    ]


class VideoRequest(BaseModel):
    dialogues: List[List[DialogueLine]]
    characters: Dict[StrictStr, Character]
    input_video_path: StrictStr = Field(
        description="Path to the input video file in storage (e.g., 'videos/input.mp4')."
    )
    crop_alignment: Literal["center", "left"] = Field(
        description="Required crop alignment for 9:16 output. Allowed values: 'center', 'left'.",
    )
    watermark: bool = Field(
        default=False,
        description="When true, writes a text watermark at the top of the video.",
    )
    watermark_text: StrictStr | None = Field(
        default=None,
        description="Text to draw as a watermark at the top when 'watermark' is true.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dialogues": [
                    [
                        {
                            "character": "stewie",
                            "phrase": "Bom dia, eu sou o Stewie Griffin, vamos ver o que acontece",
                        },
                        {
                            "character": "peter",
                            "phrase": "Bom dia, eu sou o Peter Griffin, vamos ver o que acontece",
                        },
                    ]
                ],
                "characters": {
                    "peter": {
                        "voice_id": "MnLB3WqmrDuaBBzpe8tM",
                        "image_file": "images/peter.png",
                        "position": "bottom_left",
                        "scale": 0.5,
                        "margin": 0,
                        "primary_color": [255, 255, 255],
                        "secondary_color": [200, 200, 200, 128],
                    },
                    "stewie": {
                        "voice_id": "peBmLMo9G6E3bSbuVXeV",
                        "image_file": "images/stewie.png",
                        "position": "bottom_right",
                        "scale": 0.6,
                        "margin": 0,
                        "primary_color": [255, 255, 0],
                        "secondary_color": [200, 200, 100, 128],
                    },
                },
                "input_video_path": "videos/input.mp4",
                "crop_alignment": "center",
                "watermark": True,
                "watermark_text": "Byteme",
            }
        }
    )

    @model_validator(mode="after")
    def validate_dialogue_characters_exist(self) -> Self:  # type: ignore[override]
        if not self.dialogues:
            raise ValueError("At least one dialogue is required")

        missing: set[str] = set()
        available = set(self.characters.keys())
        for dialogue in self.dialogues:
            if not dialogue:
                raise ValueError("Dialogue must contain at least one line")
            for line in dialogue:
                if line.character not in available:
                    missing.add(line.character)

        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(
                f"Unknown character(s) referenced in dialogues: {missing_str}. "
                "Every character used in dialogues must be defined in 'characters'."
            )

        if self.watermark and not self.watermark_text:
            raise ValueError(
                "'watermark_text' must be provided when 'watermark' is true."
            )
        return self
