#!/usr/bin/env python3
"""
コーパス（ユーザー入力/テスト文/歌詞）から残ったハングル音節を集計し、
頻度の高い順で出力する。上位から潰すための分析用。

使い方:
  cd backend && python scripts/analyze_remaining_hangul.py [corpus.txt]
  cd backend && python scripts/analyze_remaining_hangul.py --json output.json [corpus.txt]

corpus: 1行1テキスト。省略時は resources/lyrics_input.txt を参照
--json: 結果をJSONで出力するパス（オプション）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter

from core.korean_to_kana import KoreanToKanaConverter, count_remaining_hangul

RESOURCES = os.path.join(os.path.dirname(__file__), "../resources")
DEFAULT_CORPUS = os.path.join(RESOURCES, "lyrics_input.txt")


def load_corpus(path: str) -> list[str]:
    """テキストファイルを1行1テキストとして読み込む"""
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="残ったハングル音節の頻度集計")
    parser.add_argument(
        "corpus",
        nargs="?",
        default=DEFAULT_CORPUS,
        help="コーパスファイル（1行1テキスト）。省略時は resources/corpus.txt",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        default=None,
        help="結果をJSONで出力するパス",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="変換ログを出力しない",
    )
    args = parser.parse_args()

    if not os.path.exists(args.corpus):
        fallback = os.path.join(RESOURCES, "corpus.txt")
        if args.corpus == DEFAULT_CORPUS and os.path.exists(fallback):
            args.corpus = fallback
        else:
            print(f"コーパスが見つかりません: {args.corpus}", file=sys.stderr)
            print("resources/lyrics_input.txt または corpus.txt を作成してください。", file=sys.stderr)
            sys.exit(1)

    texts = load_corpus(args.corpus)
    converter = KoreanToKanaConverter()
    total = Counter()

    if args.quiet:
        import io

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

    for text in texts:
        result = converter.convert(text, use_g2pk=True)
        total.update(count_remaining_hangul(result))

    if args.quiet:
        sys.stdout = old_stdout

    if not total:
        print("残ったハングルはありませんでした。")
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        return

    ranked = total.most_common()
    print("=== 残ったハングル音節（頻度順・上位から潰す） ===")
    for i, (syllable, count) in enumerate(ranked, 1):
        print(f"  {i:3}. {syllable}  : {count} 回")

    result_data = [{"syllable": s, "count": c} for s, c in ranked]
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"\nJSON出力: {args.json}")


if __name__ == "__main__":
    main()
