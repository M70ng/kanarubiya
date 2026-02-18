# core/hangul2kana.py
import json
import os

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


def _load_user_exceptions() -> dict:
    global _USER_KANA_EXC
    try:
        with open(USER_EXC_PATH, encoding='utf-8') as f:
            _USER_KANA_EXC = json.load(f)
    except FileNotFoundError:
        _USER_KANA_EXC = {}
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
    return {**KANA_EXC_DICT, **_USER_KANA_EXC}


def add_user_exception(hangul: str, kana: str) -> None:
    """ユーザー辞書に1件追加し、ファイルに保存。メモリ上の辞書も更新。"""
    global _USER_KANA_EXC
    hangul = hangul.strip()
    kana = kana.strip()
    if not hangul or not kana:
        raise ValueError("hangul と kana は必須です")
    _load_user_exceptions()
    _USER_KANA_EXC[hangul] = kana
    with open(USER_EXC_PATH, 'w', encoding='utf-8') as f:
        json.dump(_USER_KANA_EXC, f, ensure_ascii=False, indent=2)


def hangul_to_kana(text: str) -> str:
    # 通常のカナ変換のみ（例外は上位で処理済み）
    return ''.join(HANGUL_KANA_DICT.get(ch, ch) for ch in text)
