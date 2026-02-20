# core/jamo_utils.py
"""
ハングル音節の Jamo（초성/중성/종성）分解・合成ユーティリティ

Unicode 範囲: U+AC00–U+D7A3（完成形音節）
  rem = ord(c) - 0xAC00
  jong = rem % 28          # 0=받침なし
  jung = (rem // 28) % 21
  cho  = rem // (28 * 21)

Jamo→カナ合成:
  jamo_to_kana(cho, jung, jong) → カナ文字列
"""

_CHO_IDX = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")  # 0-18
_JUNG_IDX = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")  # 0-20
_JONG_IDX = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ",
    "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"
]  # 0-27, 0=なし

# ── Jamo → カナ 合成テーブル ──

# 초성 → (ア段, イ段, ウ段, エ段, オ段)
_CHO_KANA_BASE: dict[int, tuple[str, str, str, str, str]] = {
    0:  ("ガ", "ギ", "グ", "ゲ", "ゴ"),             # ㄱ
    1:  ("ッカ", "ッキ", "ック", "ッケ", "ッコ"),     # ㄲ
    2:  ("ナ", "ニ", "ヌ", "ネ", "ノ"),             # ㄴ
    3:  ("ダ", "ディ", "ドゥ", "デ", "ド"),          # ㄷ
    4:  ("ッタ", "ッティ", "ットゥ", "ッテ", "ット"), # ㄸ
    5:  ("ラ", "リ", "ル", "レ", "ロ"),             # ㄹ
    6:  ("マ", "ミ", "ム", "メ", "モ"),             # ㅁ
    7:  ("バ", "ビ", "ブ", "ベ", "ボ"),             # ㅂ
    8:  ("ッパ", "ッピ", "ップ", "ッペ", "ッポ"),     # ㅃ
    9:  ("サ", "シ", "ス", "セ", "ソ"),             # ㅅ
    10: ("ッサ", "ッシ", "ッス", "ッセ", "ッソ"),     # ㅆ
    11: ("ア", "イ", "ウ", "エ", "オ"),             # ㅇ (null onset)
    12: ("ジャ", "ジ", "ジュ", "ジェ", "ジョ"),      # ㅈ
    13: ("ッチャ", "ッチ", "ッチュ", "ッチェ", "ッチョ"), # ㅉ
    14: ("チャ", "チ", "チュ", "チェ", "チョ"),      # ㅊ
    15: ("カ", "キ", "ク", "ケ", "コ"),             # ㅋ
    16: ("タ", "ティ", "トゥ", "テ", "ト"),          # ㅌ
    17: ("パ", "ピ", "プ", "ペ", "ポ"),             # ㅍ
    18: ("ハ", "ヒ", "フ", "ヘ", "ホ"),             # ㅎ
}

# 중성 → (base_column, suffix)
# base_column: 0=ア段, 1=イ段, 2=ウ段, 3=エ段, 4=オ段
# suffix: 小書きカナ（拗音・合拗音）を付加
_JUNG_SYNTH_RULE: dict[int, tuple[int, str]] = {
    0:  (0, ""),    # ㅏ → ア段
    1:  (3, ""),    # ㅐ → エ段
    2:  (1, "ャ"),  # ㅑ → イ段+ャ
    3:  (3, ""),    # ㅒ → エ段
    4:  (4, ""),    # ㅓ → オ段
    5:  (3, ""),    # ㅔ → エ段
    6:  (1, "ョ"),  # ㅕ → イ段+ョ
    7:  (3, ""),    # ㅖ → エ段
    8:  (4, ""),    # ㅗ → オ段
    9:  (2, "ァ"),  # ㅘ → ウ段+ァ
    10: (2, "ェ"),  # ㅙ → ウ段+ェ
    11: (2, "ェ"),  # ㅚ → ウ段+ェ
    12: (1, "ョ"),  # ㅛ → イ段+ョ
    13: (2, ""),    # ㅜ → ウ段
    14: (2, "ォ"),  # ㅝ → ウ段+ォ
    15: (2, "ェ"),  # ㅞ → ウ段+ェ
    16: (2, "ィ"),  # ㅟ → ウ段+ィ
    17: (1, "ュ"),  # ㅠ → イ段+ュ
    18: (2, ""),    # ㅡ → ウ段
    19: (1, ""),    # ㅢ → イ段
    20: (1, ""),    # ㅣ → イ段
}

# ㅇ(null onset) + 母音 → 直接カナ (イ+ャ=イャではなくヤ、等)
_NULL_ONSET_VOWEL: dict[int, str] = {
    0: "ア", 1: "エ", 2: "ヤ", 3: "イェ", 4: "オ",
    5: "エ", 6: "ヨ", 7: "イェ", 8: "オ", 9: "ワ",
    10: "ウェ", 11: "ウェ", 12: "ヨ", 13: "ウ", 14: "ウォ",
    15: "ウェ", 16: "ウィ", 17: "ユ", 18: "ウ", 19: "エ", 20: "イ",
}

# 종성 → トレーリングカナ
JONG_TO_TRAIL: dict[int, str] = {
    0: "",
    1: "ク",   # ㄱ
    2: "ッ",   # ㄲ
    3: "ッ",   # ㄳ
    4: "ン",   # ㄴ
    5: "ン",   # ㄵ
    6: "ン",   # ㄶ
    7: "ッ",   # ㄷ
    8: "ル",   # ㄹ
    9: "ッ",   # ㄺ
    10: "ム",  # ㄻ
    11: "プ",  # ㄼ
    12: "ル",  # ㄽ
    13: "ル",  # ㄾ
    14: "プ",  # ㄿ
    15: "ル",  # ㅀ
    16: "ム",  # ㅁ
    17: "ッ",  # ㅂ
    18: "ッ",  # ㅄ
    19: "ッ",  # ㅅ
    20: "ッ",  # ㅆ
    21: "ン",  # ㅇ
    22: "ッ",  # ㅈ
    23: "ッ",  # ㅊ
    24: "ク",  # ㅋ
    25: "ッ",  # ㅌ
    26: "プ",  # ㅍ
    27: "ッ",  # ㅎ
}


def decompose_syllable(syllable: str) -> tuple[int, int, int] | None:
    """
    完成形ハングル音節を (cho, jung, jong) のインデックスに分解する。

    Returns:
        (cho_idx, jung_idx, jong_idx) または 非ハングルなら None
    """
    if len(syllable) != 1:
        return None
    code = ord(syllable)
    if not (0xAC00 <= code <= 0xD7A3):
        return None
    rem = code - 0xAC00
    jong = rem % 28
    jung = (rem // 28) % 21
    cho = rem // (28 * 21)
    return (cho, jung, jong)


def get_jamo_names(cho: int, jung: int, jong: int) -> tuple[str, str, str]:
    """インデックスを字母名（HCJ）で返す"""
    c = _CHO_IDX[cho] if 0 <= cho < len(_CHO_IDX) else "?"
    v = _JUNG_IDX[jung] if 0 <= jung < len(_JUNG_IDX) else "?"
    t = _JONG_IDX[jong] if 0 <= jong < len(_JONG_IDX) else ""
    return (c, v, t)


def jamo_to_kana(cho: int, jung: int, jong: int = 0) -> str | None:
    """
    Jamo インデックスからカナを合成する（網羅性100%のフォールバック）。

    cho=0..18, jung=0..20, jong=0..27
    """
    base = _CHO_KANA_BASE.get(cho)
    if base is None:
        return None

    # 초성 + 중성
    if cho == 11:  # ㅇ は子音なし → 専用テーブル
        onset = _NULL_ONSET_VOWEL.get(jung)
        if onset is None:
            return None
    else:
        rule = _JUNG_SYNTH_RULE.get(jung)
        if rule is None:
            return None
        col, suffix = rule
        onset = base[col] + suffix

    # 종성
    trail = JONG_TO_TRAIL.get(jong, "")

    return onset + trail
