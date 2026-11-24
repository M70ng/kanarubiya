"""発音変化とパッチム表記の回帰テスト。"""
import pytest

from core.hangul2kana import hangul_to_kana
from core.korean_to_kana import KoreanToKanaConverter


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("꼳", "ッコッ"),
        ("학", "ハㇰ"),
        ("달", "ダㇽ"),
        ("밤", "バㇺ"),
        ("밥", "バㇷ゚"),
        ("안", "アン"),
        ("랑", "ラン"),
        ("다", "ダ"),
        ("ABC 123!", "ABC 123!"),
    ],
)
def test_final_consonants(text, expected):
    assert hangul_to_kana(text) == expected


def test_all_hangul_syllables_have_kana_fallback():
    for code in range(0xAC00, 0xD7A4):
        converted = hangul_to_kana(chr(code))
        assert converted and not any("가" <= c <= "힣" for c in converted)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("꽃", "ッコッ"),
        ("꽃이", "ッコチ"),
        ("꽃을", "ッコチュㇽ"),
        ("먹다", "モㇰタ"),
        ("읽다", "イㇰタ"),
        ("안녕하세요", "アンニョンハセヨ"),
        ("한글 ABC 123", "ハングㇽ ABC 123"),
    ],
)
def test_g2pk_context_and_kana(text, expected):
    result = KoreanToKanaConverter().convert_with_details(text, use_g2pk=True)
    assert not result.get("error")
    assert result["kana"] == expected
