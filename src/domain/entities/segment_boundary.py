from typing import TypedDict


class SegmentBoundary(TypedDict):
    start_s: float
    end_s: float
    speaker_index: int
