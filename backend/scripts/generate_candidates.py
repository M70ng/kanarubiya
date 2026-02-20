#!/usr/bin/env python3
"""
漏れ音節のカナ候補を自動生成する。

フロー:
  1. g2pk で発音ハングル（音韻反映）を得る
  2. 発音形が辞書にあればそのカナを候補に
  3. なければ Jamo 分解 → Jamo→カナルールで合成
  4. 変なものは例外辞書に落とす前提で出力

使い方:
  python scripts/generate_candidates.py [remaining_hangul.json]
  python scripts/generate_candidates.py --syllable 갂 --syllable 값
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jamo_utils import decompose_syllable, get_jamo_names, jamo_to_kana, JONG_TO_TRAIL
from core.hangul2kana import hangul_to_kana


def _get_g2pk():
    """g2pk を遅延ロード（インポート時にクラッシュする環境対策）"""
    try:
        from core.g2pk_wrapper import G2pkWrapper
        return G2pkWrapper()
    except ImportError:
        return None

RESOURCES = os.path.join(os.path.dirname(__file__), "../resources")
DICT_PATH = os.path.join(RESOURCES, "hangul_kana_dict.json")
REMAINING_PATH = os.path.join(RESOURCES, "remaining_hangul.json")

def _load_dict() -> dict[str, str]:
    with open(DICT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_base_table(hangul_dict: dict[str, str]) -> dict[tuple[int, int], str]:
    """jong=0 のエントリから (cho, jung) → カナ のテーブルを構築"""
    base: dict[tuple[int, int], str] = {}
    for syl, kana in hangul_dict.items():
        if not syl or not kana:
            continue
        comp = decompose_syllable(syl)
        if comp is None:
            continue
        cho, jung, jong = comp
        if jong == 0:
            base[(cho, jung)] = kana
    return base


def _generate_from_jamo(cho: int, jung: int, jong: int, base_table: dict) -> tuple[str | None, str]:
    """
    Jamo からカナ候補を合成。辞書ベース → Jamoルール のフォールバック。

    Returns:
        (candidate, source) source は "jamo_dict" or "jamo_synth"
    """
    # 1. 辞書の jong=0 エントリから (cho, jung) が見つかればそれを使用
    base = base_table.get((cho, jung))
    if base:
        if jong == 0:
            return base, "jamo_dict"
        trail = JONG_TO_TRAIL.get(jong, "ッ")
        return base + trail, "jamo_dict"

    # 2. フォールバック: Jamo→カナ合成テーブルで生成
    candidate = jamo_to_kana(cho, jung, jong)
    if candidate:
        return candidate, "jamo_synth"

    return None, "no_rule"


def generate_candidates(syllables: list[str], g2pk, hangul_dict: dict) -> list[dict]:
    """漏れ音節リストからカナ候補を生成"""
    base_table = _build_base_table(hangul_dict)
    results = []

    for syl in syllables:
        if len(syl) != 1:
            results.append({"syllable": syl, "candidate": None, "source": "skip", "note": "1音節のみ対象"})
            continue

        # 1. g2pk で発音形を取得
        phonetic = syl
        if g2pk:
            try:
                phonetic = g2pk.convert(syl)
            except Exception as e:
                results.append({"syllable": syl, "candidate": None, "source": "g2pk_error", "note": str(e)})
                continue

        # 2. 発音形を辞書で変換。全部変換できればそれを候補に
        kana_from_phonetic = hangul_to_kana(phonetic)
        if not any(0xAC00 <= ord(c) <= 0xD7A3 for c in kana_from_phonetic):
            results.append({
                "syllable": syl,
                "phonetic": phonetic,
                "candidate": kana_from_phonetic,
                "source": "g2pk_dict",
                "note": f"g2pk→{phonetic}→辞書で全変換",
            })
            continue

        # 4. Jamo 分解 → 合成
        comp = decompose_syllable(syl)
        if comp is None:
            results.append({"syllable": syl, "candidate": None, "source": "not_hangul", "note": "非ハングル"})
            continue

        cho, jung, jong = comp
        cname, vname, tname = get_jamo_names(cho, jung, jong)
        candidate, source = _generate_from_jamo(cho, jung, jong, base_table)
        jamo_str = f"{cname}+{vname}+{tname}" if tname else f"{cname}+{vname}"

        if candidate:
            results.append({
                "syllable": syl,
                "phonetic": phonetic,
                "jamo": jamo_str,
                "candidate": candidate,
                "source": source,
                "note": "辞書base+jong" if source == "jamo_dict" else "Jamo合成ルール",
            })
        else:
            results.append({
                "syllable": syl,
                "phonetic": phonetic,
                "jamo": jamo_str,
                "candidate": None,
                "source": "no_rule",
                "note": f"合成ルールなし ({cho},{jung},{jong})",
            })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="漏れ音節のカナ候補自動生成")
    parser.add_argument(
        "input_file",
        nargs="?",
        default=REMAINING_PATH,
        help="漏れ音節のJSON配列ファイル。省略時は remaining_hangul.json",
    )
    parser.add_argument(
        "--syllable",
        action="append",
        dest="syllables",
        help="直接音節を指定（複数可）",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="結果をJSONで出力",
    )
    parser.add_argument(
        "--no-g2pk",
        action="store_true",
        help="g2pk を使わず Jamo合成のみで候補生成（g2pk がクラッシュする環境向け）",
    )
    args = parser.parse_args()

    syllables: list[str] = []
    if args.syllables:
        syllables = args.syllables
    elif os.path.exists(args.input_file):
        with open(args.input_file, encoding="utf-8") as f:
            data = json.load(f)
        raw = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
        # analyze_remaining_hangul 出力 [{syllable,count}] または [syllable, ...]
        syllables = []
        for x in raw:
            if isinstance(x, dict) and "syllable" in x:
                syllables.append(x["syllable"])
            elif isinstance(x, str):
                syllables.append(x)
    else:
        print(f"入力ファイルが見つかりません: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    if not syllables:
        print("漏れ音節がありません。")
        return

    g2pk = None if args.no_g2pk else _get_g2pk()
    if not g2pk:
        print("[INFO] g2pk を使いません。Jamo合成のみで候補生成します。", file=sys.stderr)
    hangul_dict = _load_dict()
    results = generate_candidates(syllables, g2pk, hangul_dict)

    print("=== カナ候補生成結果 ===")
    for r in results:
        syl = r["syllable"]
        cand = r.get("candidate", "")
        src = r.get("source", "")
        note = r.get("note", "")
        status = "✓" if cand else "?"
        print(f"  {status} {syl} → {cand or '(なし)'}  [{src}] {note}")

    if args.json:
        out = [{"syllable": r["syllable"], "candidate": r.get("candidate"), "source": r.get("source"), "note": r.get("note")} for r in results]
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\nJSON出力: {args.json}")


if __name__ == "__main__":
    main()
