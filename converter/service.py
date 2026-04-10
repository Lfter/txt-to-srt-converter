import re
from pathlib import Path
from typing import List, Tuple

from .errors import ConversionError
from .models import ConversionResult, SubtitleCue

TIME_RANGE_RE = re.compile(r"^\s*(\d{2}:\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2}:\d{2})\s*$")
TRACK_MARKER_RE = re.compile(r"^[A-Za-z]+\d*\s*,\s*\d+\s*$")


class ConversionService:
    def convert(self, txt_path: str, output_srt_path: str, fps: int = 25) -> ConversionResult:
        self._validate_fps(fps)
        raw_text = self._read_text(txt_path)
        cues, warnings = self._parse_txt(raw_text, fps=fps)
        if not cues:
            raise ConversionError("TXT 中没有可转换的有效字幕片段。")

        rendered_srt = self._render_srt(cues)
        self._write_text(output_srt_path, rendered_srt)
        return ConversionResult(
            output_path=str(output_srt_path),
            cue_count=len(cues),
            skipped_count=len(warnings),
            warnings=tuple(warnings),
            preview_lines=tuple(cue.text for cue in cues[:3]),
        )

    def _validate_fps(self, fps: int) -> None:
        if not isinstance(fps, int):
            raise ConversionError("FPS 必须是整数。")
        if fps <= 0:
            raise ConversionError("FPS 必须大于 0。")

    def _read_text(self, txt_path: str) -> str:
        path = Path(txt_path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ConversionError(f"无法读取 TXT 文件：{exc}") from exc

        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue

        raise ConversionError("TXT 文件编码无法识别，请使用 UTF-8 或 GB18030 编码。")

    def _write_text(self, output_srt_path: str, text: str) -> None:
        try:
            Path(output_srt_path).write_text(text, encoding="utf-8")
        except OSError as exc:
            raise ConversionError(f"无法写入 SRT 文件：{exc}") from exc

    def _parse_txt(self, raw_text: str, fps: int) -> Tuple[List[SubtitleCue], List[str]]:
        normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        blocks = re.split(r"\n\s*\n", normalized)
        cues: List[SubtitleCue] = []
        warnings: List[str] = []

        for block_index, block in enumerate(blocks, start=1):
            compact = block.strip()
            if not compact:
                continue

            lines = [line.rstrip() for line in compact.split("\n")]
            first_line = lines[0].strip()
            match = TIME_RANGE_RE.match(first_line)
            if not match:
                warnings.append("第{idx}块跳过：时间行格式无效（{line}）".format(idx=block_index, line=first_line))
                continue

            start_tc, end_tc = match.group(1), match.group(2)
            content_start = 1
            if len(lines) >= 2 and TRACK_MARKER_RE.match(lines[1].strip()):
                content_start = 2

            text_lines = [line for line in lines[content_start:] if line.strip()]
            if not text_lines:
                warnings.append("第{idx}块跳过：字幕文本为空。".format(idx=block_index))
                continue

            try:
                start_seconds = self._timecode_to_seconds(start_tc, fps)
                end_seconds = self._timecode_to_seconds(end_tc, fps)
            except ValueError as exc:
                warnings.append("第{idx}块跳过：{msg}".format(idx=block_index, msg=str(exc)))
                continue

            if end_seconds <= start_seconds:
                warnings.append("第{idx}块跳过：结束时间不晚于开始时间。".format(idx=block_index))
                continue

            cues.append(
                SubtitleCue(
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    text="\n".join(text_lines).strip(),
                )
            )

        return cues, warnings

    def _timecode_to_seconds(self, timecode: str, fps: int) -> float:
        parts = timecode.split(":")
        if len(parts) != 4:
            raise ValueError("时间码格式无效：{value}".format(value=timecode))

        try:
            hours, minutes, seconds, frames = [int(part) for part in parts]
        except ValueError as exc:
            raise ValueError("时间码包含非数字字段：{value}".format(value=timecode)) from exc

        if minutes < 0 or minutes >= 60:
            raise ValueError("时间码分钟越界：{value}".format(value=timecode))
        if seconds < 0 or seconds >= 60:
            raise ValueError("时间码秒越界：{value}".format(value=timecode))
        if frames < 0 or frames >= fps:
            raise ValueError("时间码帧数越界（FPS={fps}）：{value}".format(fps=fps, value=timecode))

        return hours * 3600.0 + minutes * 60.0 + seconds + frames / float(fps)

    def _render_srt(self, cues: List[SubtitleCue]) -> str:
        lines: List[str] = []
        for index, cue in enumerate(cues, start=1):
            lines.append(str(index))
            lines.append(
                "{start} --> {end}".format(
                    start=self._format_srt_timestamp(cue.start_seconds),
                    end=self._format_srt_timestamp(cue.end_seconds),
                )
            )
            lines.append(cue.text)
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def _format_srt_timestamp(self, total_seconds: float) -> str:
        if total_seconds < 0:
            raise ValueError("SRT 时间戳不能为负数。")

        total_milliseconds = int(total_seconds * 1000 + 0.5)
        hours, remainder = divmod(total_milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, milliseconds = divmod(remainder, 1000)
        return "{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}".format(
            hh=hours,
            mm=minutes,
            ss=seconds,
            ms=milliseconds,
        )
