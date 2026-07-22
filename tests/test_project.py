"""Tests for the .project file parser/serializer."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pytest

from ocpp.project import (
    OCPP_PROJECT_NAME,
    LineRecord,
    mask_dict,
    mask_value,
    parse_project,
    serialize_project,
)


class TestParseBasic:
    """Basic key-value parsing."""

    def test_single_key_value(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("ANTHROPIC_API_KEY=sk-ant-abc123\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("ANTHROPIC_API_KEY", "sk-ant-abc123")])
        assert len(lines) == 1
        assert lines[0].line_type == "kv"
        assert lines[0].key == "ANTHROPIC_API_KEY"

    def test_multiple_key_values(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text(
            "OPENAI_API_KEY=sk-openai-xyz\n"
            "ANTHROPIC_API_KEY=sk-ant-abc\n"
            "OPENROUTER_API_KEY=sk-or-789\n",
            encoding="utf-8",
        )
        kv, lines = parse_project(f)
        assert list(kv.keys()) == ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
        assert kv["OPENAI_API_KEY"] == "sk-openai-xyz"
        assert kv["ANTHROPIC_API_KEY"] == "sk-ant-abc"
        assert kv["OPENROUTER_API_KEY"] == "sk-or-789"
        assert len(lines) == 3

    def test_order_preservation(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")
        kv, _ = parse_project(f)
        assert list(kv.keys()) == ["A", "B", "C"]
        assert list(kv.values()) == ["1", "2", "3"]


class TestParseCommentsBlanksUnknowns:
    """Parsing with comments, blank lines, and unknown lines."""

    def test_comments_preserved(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text(
            "# This is a comment\nKEY=value\n# Another comment\n",
            encoding="utf-8",
        )
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("KEY", "value")])
        assert len(lines) == 3
        assert lines[0].line_type == "comment"
        assert lines[0].raw == "# This is a comment"
        assert lines[1].line_type == "kv"
        assert lines[1].key == "KEY"
        assert lines[2].line_type == "comment"
        assert lines[2].raw == "# Another comment"

    def test_blank_lines_preserved(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("A=1\n\n\nB=2\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("A", "1"), ("B", "2")])
        assert len(lines) == 4
        assert lines[0].line_type == "kv"
        assert lines[1].line_type == "blank"
        assert lines[1].raw == ""
        assert lines[2].line_type == "blank"
        assert lines[2].raw == ""
        assert lines[3].line_type == "kv"

    def test_unknown_lines_preserved(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text(
            "VALID=ok\nexport FOO=bar\n  INDENTED=no\nKEY2=val2\n",
            encoding="utf-8",
        )
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("VALID", "ok"), ("KEY2", "val2")])
        assert len(lines) == 4
        assert lines[0].line_type == "kv"
        assert lines[1].line_type == "unknown"
        assert lines[1].raw == "export FOO=bar"
        assert lines[2].line_type == "unknown"
        assert lines[2].raw == "  INDENTED=no"
        assert lines[3].line_type == "kv"

    def test_comment_with_leading_whitespace(self, tmp_path: Path) -> None:
        """Comments must start with # at the beginning of the line (no leading spaces)."""
        f = tmp_path / ".project"
        f.write_text("  # indented comment\nKEY=val\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("KEY", "val")])
        assert lines[0].line_type == "unknown"
        assert lines[0].raw == "  # indented comment"


class TestParseEmptyValues:
    """Empty values (KEY=) produce empty string."""

    def test_empty_value(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("EMPTY=\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("EMPTY", "")])
        assert lines[0].line_type == "kv"
        assert lines[0].key == "EMPTY"

    def test_empty_value_among_others(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("A=1\nB=\nC=3\n", encoding="utf-8")
        kv, _ = parse_project(f)
        assert kv == OrderedDict([("A", "1"), ("B", ""), ("C", "3")])


class TestParseDuplicateKeys:
    """Duplicate keys: last-wins semantics."""

    def test_duplicate_key_last_wins(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("KEY=first\nKEY=second\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == OrderedDict([("KEY", "second")])
        assert len(lines) == 2
        assert lines[0].key == "KEY"
        assert lines[1].key == "KEY"


class TestSerializeRoundTrip:
    """Serialization preserves comments, blanks, and unknown lines."""

    def test_round_trip_preserves_everything(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        original = (
            "# Project config\n\nAPI_KEY=secret123\n# Endpoint\nBASE_URL=https://api.example.com\n"
        )
        f.write_text(original, encoding="utf-8")
        kv, lines = parse_project(f)
        serialize_project(f, kv, lines)
        assert f.read_text(encoding="utf-8") == original

    def test_round_trip_with_unknown_lines(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        original = "A=1\nexport B=2\nC=3\n"
        f.write_text(original, encoding="utf-8")
        kv, lines = parse_project(f)
        serialize_project(f, kv, lines)
        assert f.read_text(encoding="utf-8") == original

    def test_round_trip_with_blank_lines(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        original = "A=1\n\n\nB=2\n"
        f.write_text(original, encoding="utf-8")
        kv, lines = parse_project(f)
        serialize_project(f, kv, lines)
        assert f.read_text(encoding="utf-8") == original


class TestSerializeUpdatedValues:
    """Serialization with updated values."""

    def test_update_existing_value(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("KEY=old_value\nOTHER=keep\n", encoding="utf-8")
        kv, lines = parse_project(f)
        kv["KEY"] = "new_value"
        serialize_project(f, kv, lines)
        result = f.read_text(encoding="utf-8")
        assert "KEY=new_value" in result
        assert "OTHER=keep" in result

    def test_update_multiple_values(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")
        kv, lines = parse_project(f)
        kv["A"] = "10"
        kv["C"] = "30"
        serialize_project(f, kv, lines)
        result = f.read_text(encoding="utf-8")
        assert result == "A=10\nB=2\nC=30\n"


class TestSerializeNewKeys:
    """New keys not in original line records are appended at end."""

    def test_new_key_appended(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("EXISTING=val\n", encoding="utf-8")
        kv, lines = parse_project(f)
        kv["NEW_KEY"] = "new_val"
        serialize_project(f, kv, lines)
        result = f.read_text(encoding="utf-8")
        assert result == "EXISTING=val\nNEW_KEY=new_val\n"

    def test_new_key_after_comments(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("# Header\nEXISTING=val\n", encoding="utf-8")
        kv, lines = parse_project(f)
        kv["NEW_KEY"] = "new_val"
        serialize_project(f, kv, lines)
        result = f.read_text(encoding="utf-8")
        assert result == "# Header\nEXISTING=val\nNEW_KEY=new_val\n"


class TestMaskValue:
    """Value masking."""

    def test_ocpp_project_name_not_masked(self) -> None:
        assert mask_value(OCPP_PROJECT_NAME, "my-project") == "OCPP_PROJECT_NAME=my-project"

    def test_other_keys_masked(self) -> None:
        assert mask_value("ANTHROPIC_API_KEY", "sk-ant-secret") == "ANTHROPIC_API_KEY=***"

    def test_all_api_keys_masked(self) -> None:
        keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY"]
        for key in keys:
            assert mask_value(key, "secret") == f"{key}=***"


class TestMaskDict:
    """Dict-level masking."""

    def test_mask_dict_returns_new_dict(self) -> None:
        original = {"KEY": "secret", OCPP_PROJECT_NAME: "my-proj"}
        masked = mask_dict(original)
        assert masked is not original
        assert masked["KEY"] == "***"
        assert masked[OCPP_PROJECT_NAME] == "my-proj"

    def test_mask_dict_all_masked_except_project_name(self) -> None:
        d = {"A": "1", "B": "2", OCPP_PROJECT_NAME: "proj"}
        result = mask_dict(d)
        assert result == {"A": "***", "B": "***", OCPP_PROJECT_NAME: "proj"}

    def test_mask_dict_empty(self) -> None:
        assert mask_dict({}) == {}


class TestValidation:
    """Validation of keys and values."""

    def test_invalid_key_starts_with_digit(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("1INVALID=value\n", encoding="utf-8")
        with pytest.raises(ValueError, match="1INVALID"):
            parse_project(f)

    def test_invalid_key_with_hyphen(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("MY-KEY=value\n", encoding="utf-8")
        with pytest.raises(ValueError, match="MY-KEY"):
            parse_project(f)

    def test_invalid_key_with_special_chars(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("KEY@FOO=value\n", encoding="utf-8")
        with pytest.raises(ValueError, match="KEY@FOO"):
            parse_project(f)

    def test_embedded_newline_in_value(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("KEY=line1\nline2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="embedded newline"):
            parse_project(f)

    def test_empty_key_part_returns_unknown(self, tmp_path: Path) -> None:
        """Line with = but empty key part (e.g. '=value') should be treated as unknown (line 97)."""
        f = tmp_path / ".project"
        f.write_text("=value\nVALID=ok\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv == {"VALID": "ok"}
        assert len(lines) == 2
        assert lines[0].line_type == "unknown"
        assert lines[0].raw == "=value"
        assert lines[1].line_type == "kv"


class TestMissingFile:
    """Missing file returns empty dict and empty list."""

    def test_missing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.project"
        kv, lines = parse_project(f)
        assert kv == OrderedDict()
        assert lines == []


class TestUtf8:
    """UTF-8 encoding with Unicode characters."""

    def test_unicode_values(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text("GREETING=Héllö Wörld\nEMOJI=🚀\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv["GREETING"] == "Héllö Wörld"
        assert kv["EMOJI"] == "🚀"
        assert len(lines) == 2

    def test_unicode_round_trip(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        original = "# Café\nCOFFEE=crème brûlée\n"
        f.write_text(original, encoding="utf-8")
        kv, lines = parse_project(f)
        serialize_project(f, kv, lines)
        assert f.read_text(encoding="utf-8") == original


class TestLineRecord:
    """LineRecord dataclass behavior."""

    def test_line_record_creation(self) -> None:
        rec = LineRecord(line_type="kv", raw="KEY=val", key="KEY")
        assert rec.line_type == "kv"
        assert rec.raw == "KEY=val"
        assert rec.key == "KEY"

    def test_line_record_default_key(self) -> None:
        rec = LineRecord(line_type="comment", raw="# hello")
        assert rec.line_type == "comment"
        assert rec.raw == "# hello"
        assert rec.key is None


class TestOcppProjectNameConstant:
    """OCPP_PROJECT_NAME constant."""

    def test_constant_value(self) -> None:
        assert OCPP_PROJECT_NAME == "OCPP_PROJECT_NAME"

    def test_parsed_like_any_other_key(self, tmp_path: Path) -> None:
        f = tmp_path / ".project"
        f.write_text(f"{OCPP_PROJECT_NAME}=my-cool-project\n", encoding="utf-8")
        kv, lines = parse_project(f)
        assert kv[OCPP_PROJECT_NAME] == "my-cool-project"
        assert lines[0].key == OCPP_PROJECT_NAME
