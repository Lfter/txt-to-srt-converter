from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class ConversionResult:
    output_path: str
    cue_count: int
    skipped_count: int
    warnings: Tuple[str, ...]
    preview_lines: Tuple[str, ...]
