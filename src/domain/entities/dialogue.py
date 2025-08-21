from typing import List, NewType
from pydantic import BaseModel


VoiceId = NewType("VoiceId", str)


class Line(BaseModel):
    speaker: VoiceId
    text: str


class Dialogue(BaseModel):
    lines: List[Line]
