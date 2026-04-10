from pathlib import Path

import pytest

from converter import ConversionError, ConversionService


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_valid_sample_txt() -> None:
    service = ConversionService()
    sample_text = (FIXTURES_DIR / "input_sample.txt").read_text(encoding="utf-8")

    cues, warnings = service._parse_txt(sample_text, fps=25)

    assert warnings == []
    assert len(cues) == 3
    assert cues[0].start_seconds == pytest.approx(2.56)
    assert cues[0].end_seconds == pytest.approx(3.08)
    assert cues[0].text == "谢谢"
    assert cues[-1].start_seconds == pytest.approx(5.12)
    assert cues[-1].end_seconds == pytest.approx(7.4)


def test_timecode_conversion_fps25() -> None:
    service = ConversionService()
    seconds = service._timecode_to_seconds("00:00:02:14", fps=25)
    assert seconds == pytest.approx(2.56)
    assert service._format_srt_timestamp(seconds) == "00:00:02,560"


def test_skip_malformed_blocks() -> None:
    service = ConversionService()
    txt = """
00:00:00:00 - 00:00:01:00
V1, 1
第一条

invalid time line
V1, 1
第二条

00:00:02:26 - 00:00:03:00
V1, 1
第三条

00:00:04:00 - 00:00:03:20
V1, 1
第四条

00:00:05:00 - 00:00:06:00
V1, 1
    
"""

    cues, warnings = service._parse_txt(txt, fps=25)

    assert len(cues) == 1
    assert cues[0].text == "第一条"
    assert len(warnings) == 4
    assert "时间行格式无效" in warnings[0]
    assert "帧数越界" in warnings[1]
    assert "结束时间不晚于开始时间" in warnings[2]
    assert "字幕文本为空" in warnings[3]


def test_convert_generates_srt_file(tmp_path: Path) -> None:
    service = ConversionService()
    input_txt = FIXTURES_DIR / "input_sample.txt"
    output_srt = tmp_path / "out.srt"

    result = service.convert(str(input_txt), str(output_srt), fps=25)

    assert output_srt.exists()
    assert result.cue_count == 3
    assert result.skipped_count == 0
    assert result.preview_lines[0] == "谢谢"
    content = output_srt.read_text(encoding="utf-8")
    assert "1\n00:00:02,560 --> 00:00:03,080\n谢谢\n" in content
    assert "2\n00:00:03,600 --> 00:00:05,120\n在刚才的舞蹈当中\n" in content
    assert content.strip().endswith("我们感受到了侠客在大漠中")


def test_convert_with_custom_fps(tmp_path: Path) -> None:
    service = ConversionService()
    input_txt = tmp_path / "custom_fps.txt"
    output_srt = tmp_path / "custom_fps.srt"
    input_txt.write_text(
        "00:00:00:15 - 00:00:01:15\nV1, 1\nhello\n",
        encoding="utf-8",
    )

    result = service.convert(str(input_txt), str(output_srt), fps=30)

    assert result.cue_count == 1
    content = output_srt.read_text(encoding="utf-8")
    assert "00:00:00,500 --> 00:00:01,500" in content


def test_convert_raises_when_no_valid_cue(tmp_path: Path) -> None:
    service = ConversionService()
    input_txt = tmp_path / "invalid.txt"
    output_srt = tmp_path / "invalid.srt"
    input_txt.write_text("not a cue block", encoding="utf-8")

    with pytest.raises(ConversionError):
        service.convert(str(input_txt), str(output_srt), fps=25)
