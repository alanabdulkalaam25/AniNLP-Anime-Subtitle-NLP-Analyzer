"""Tests for subtitle text preprocessing."""

from app.services.preprocessor import preprocess_text


def test_preprocess_text_removes_markup_and_preserves_japanese_punctuation() -> None:
    text = "<font color=\"white\">今日は  学校へ</font>\\N{\\an8}行きます。"

    assert preprocess_text(text) == "今日は 学校へ 行きます。"


def test_preprocess_text_strips_standalone_ass_line_breaks() -> None:
    assert preprocess_text("一行目\\N二行目") == "一行目 二行目"
    assert preprocess_text("一行目\\n二行目\\h三行目") == "一行目 二行目 三行目"
    assert preprocess_text("<i>一行目</i>\\N<i>二行目</i>") == "一行目 二行目"
