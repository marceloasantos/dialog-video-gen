import pysubs2
from pysubs2 import Alignment
from typing import Dict
from src.domain.entities.character import Character
from src.domain.entities.segment_boundary import SegmentBoundary


class AssGenerator:
    """
    Generates styled ASS subtitles from word-level timestamp data.
    """

    def generate_ass_from_words(
        self,
        word_data: dict,
        output_ass_path: str,
        font_size: int,
        alignment: int,
        margin_v: int,
        outline: int,
        speaker_mapping: Dict[str, Character],
        segment_boundaries: list[SegmentBoundary],
    ):
        """
        Generates an ASS file from word-level timestamp data.
        Words are grouped into lines and styled with a karaoke effect for a smoother experience.

        Args:
            word_data (dict): The JSON data from ElevenLabs API with word timestamps.
            output_ass_path (str): The path to save the generated .ass file.
            font_size (int): The font size for the subtitles.
            alignment (int): The ASS alignment code (e.g., 2 for bottom-center).
            margin_v (int): The vertical margin from the edge of the video.
            outline (int): The thickness of the text border.
            speaker_mapping (Dict[str, Character]): A mapping from speaker ID to character configuration.
            segment_boundaries (list[SegmentBoundary]): Deterministic speaker assignment with items like
                {"start_s": float, "end_s": float, "speaker_index": int}.
        """
        subs = pysubs2.SSAFile()

        if not speaker_mapping:
            raise ValueError(
                "A speaker_mapping must be provided to define subtitle styles."
            )

        # Define styles for each speaker with a secondary color for the karaoke effect
        for speaker_id, config in speaker_mapping.items():
            style_name = f"speaker_{speaker_id}"
            primary_color = pysubs2.Color(*config.primary_color)
            secondary_color = pysubs2.Color(*config.secondary_color)
            subs.styles[style_name] = pysubs2.SSAStyle(
                fontname="Bangers",
                fontsize=float(font_size),
                primarycolor=primary_color,
                secondarycolor=secondary_color,
                outlinecolor=pysubs2.Color(0, 0, 0),
                borderstyle=1,
                outline=float(outline),
                shadow=float(1),
                alignment=Alignment(alignment),
                marginv=int(margin_v),
            )

        words = [
            word for word in word_data.get("words", []) if word.get("type") == "word"
        ]
        if not words:
            subs.save(output_ass_path)
            return

        # Always override diarizer labels to ensure speaker indices match dialogue mapping
        norm = [
            (
                float(b.get("start_s", 0.0)),
                float(b.get("end_s", 0.0)),
                int(b.get("speaker_index", 0)),
            )
            for b in segment_boundaries
        ]
        norm.sort(key=lambda x: x[0])

        def assign_speaker_index(word_start: float) -> int:
            for start, end, idx in norm:
                if start <= word_start < end:
                    return idx
            # Fallback: keep diarizer's last digit if present, else default to 0
            sid = str(words[0].get("speaker_id", "speaker_0"))
            try:
                return int(str(sid).split("_")[-1])
            except Exception:
                return 0

        for w in words:
            ws = float(w.get("start", 0.0))
            idx = assign_speaker_index(ws)
            w["speaker_id"] = f"speaker_{idx}"

        # Group words into subtitle lines
        lines = []
        current_line = []
        if words:
            current_line.append(words[0])

        for i in range(1, len(words)):
            word_info = words[i]
            prev_word_info = words[i - 1]

            # Conditions to start a new line
            speaker_changed = word_info.get("speaker_id") != prev_word_info.get(
                "speaker_id"
            )
            pause_is_long = (
                word_info.get("start") - prev_word_info.get("end")
            ) > 0.7  # 700ms pause
            is_end_of_sentence = any(p in prev_word_info["text"] for p in ".?!")
            line_is_long = (
                len(" ".join(w["text"] for w in current_line)) + len(word_info["text"])
                > 45
            )

            if (
                speaker_changed
                or (pause_is_long and not is_end_of_sentence)
                or is_end_of_sentence
                or line_is_long
            ):
                lines.append(current_line)
                current_line = [word_info]
            else:
                current_line.append(word_info)

        if current_line:
            lines.append(current_line)

        # Create an SSAEvent for each line with karaoke tags
        for line_words in lines:
            if not line_words:
                continue

            start_time = int(line_words[0]["start"] * 1000)
            end_time = int(line_words[-1]["end"] * 1000)

            # Get speaker from the first word of the line
            if "speaker_id" not in line_words[0]:
                raise ValueError(
                    f"Missing 'speaker_id' for word: {line_words[0].get('text')}"
                )
            speaker_id_str = line_words[0]["speaker_id"]

            try:
                speaker_index = int(speaker_id_str.split("_")[-1])
            except (ValueError, IndexError):
                speaker_index = 0

            style = f"speaker_{speaker_index}"
            if style not in subs.styles:
                style = "Default"

            # Build text with progressive karaoke tags (\k)
            karaoke_text = " ".join(
                f"{{\\k{int((w['end'] - w['start']) * 100)}}}{w['text']}"
                for w in line_words
            )

            event = pysubs2.SSAEvent(
                start=start_time, end=end_time, text=karaoke_text, style=style
            )
            subs.append(event)

        subs.save(output_ass_path)
