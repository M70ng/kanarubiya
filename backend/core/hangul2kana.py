# core/hangul2kana.py
"""
ハングル→カナ変換モジュール

自作の辞書（hangul_kana_dict.json）に基づき、ハングルを日本語カナに変換する。
一部の特殊読みには例外辞書（kana_exceptions.json / user_kana_exceptions.json）を使用する。

【外部から利用する主な関数】
  - hangul_to_kana(text)    … ハングル文字列をカナに変換（1文字ずつ辞書引き）
  - get_merged_exceptions() … 組み込み＋ユーザー例外辞書をマージした dict を返す
  - add_user_exception(hangul, kana) … ユーザー辞書に1件追加してファイル（user_kana_exceptions.json）に保存
"""
import json
import os
from typing import Optional

# 例外辞書のロード
EXC_PATH = os.path.join(os.path.dirname(__file__), '../resources/kana_exceptions.json')
try:
    with open(EXC_PATH, encoding='utf-8') as f:
        KANA_EXC_DICT = json.load(f)
except FileNotFoundError:
    KANA_EXC_DICT = {}

# ユーザーが追加した例外辞書（変換漏れ報告で追加される）
USER_EXC_PATH = os.path.join(os.path.dirname(__file__), '../resources/user_kana_exceptions.json')
_USER_KANA_EXC: dict = {}
_MERGED_EXC_CACHE: Optional[dict] = None


def _load_user_exceptions() -> dict:
    global _USER_KANA_EXC, _MERGED_EXC_CACHE
    try:
        with open(USER_EXC_PATH, encoding='utf-8') as f:
            _USER_KANA_EXC = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _USER_KANA_EXC = {}
    _MERGED_EXC_CACHE = None
    return _USER_KANA_EXC


_load_user_exceptions()

DICT_PATH = os.path.join(os.path.dirname(__file__), '../resources/hangul_kana_dict.json')
try:
    with open(DICT_PATH, encoding='utf-8') as f:
        HANGUL_KANA_DICT = json.load(f)
except FileNotFoundError:
    HANGUL_KANA_DICT = {}


def get_merged_exceptions() -> dict:
    """組み込み例外とユーザー追加例外をマージ（ユーザーを優先）"""
    global _MERGED_EXC_CACHE
    if _MERGED_EXC_CACHE is None:
        _MERGED_EXC_CACHE = dict(KANA_EXC_DICT)
    return _MERGED_EXC_CACHE


def add_user_exception(hangul: str, kana: str) -> None:
    """ユーザー辞書に1件追加し、ファイルに保存。メモリ上の辞書も更新。"""
    global _USER_KANA_EXC, _MERGED_EXC_CACHE
    hangul = hangul.strip()
    kana = kana.strip()
    if not hangul or not kana:
        raise ValueError("hangul と kana は必須です")
    _load_user_exceptions()
    _USER_KANA_EXC[hangul] = kana
    with open(USER_EXC_PATH, 'w', encoding='utf-8') as f:
        json.dump(_USER_KANA_EXC, f, ensure_ascii=False, indent=2)
    _MERGED_EXC_CACHE = None


def _fallback_jamo(ch: str) -> str:
    """辞書にないハングル音節を Jamo 分解→合成でカナに変換する"""
    from .jamo_utils import decompose_syllable, jamo_to_kana
    comp = decompose_syllable(ch)
    if comp is None:
        return ch
    result = jamo_to_kana(*comp)
    return result if result is not None else ch


# g2pK後の代表的な終声を、母音を付けず短く読むための表記。
# ㇷ゚ は小書きの「ㇷ」に半濁点を組み合わせた文字。
_FINAL_KANA = {
    1: "ㇰ",   # ㄱ
    4: "ン",   # ㄴ
    7: "ッ",   # ㄷ
    8: "ㇽ",   # ㄹ
    16: "ㇺ",  # ㅁ
    17: "ㇷ゚",  # ㅂ
    21: "ン",  # ㅇ
}


def _syllable_to_kana(ch: str) -> str:
    """発音変化後の終声を統一し、それ以外は既存の辞書を使う。"""
    if len(ch) == 1 and "가" <= ch <= "힣":
        jong = (ord(ch) - 0xAC00) % 28
        if jong in _FINAL_KANA:
            open_syllable = chr(ord(ch) - jong)
            onset = HANGUL_KANA_DICT.get(open_syllable) or _fallback_jamo(open_syllable)
            return onset + _FINAL_KANA[jong]
    return HANGUL_KANA_DICT.get(ch) or _fallback_jamo(ch)


def hangul_to_kana(text: str) -> str:
    """発音変化後のハングルをカナへ変換し、その他の文字は保持する。"""
    return ''.join(_syllable_to_kana(ch) for ch in text)
