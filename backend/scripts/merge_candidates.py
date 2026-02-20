#!/usr/bin/env python3
"""
漏れ音節の候補を一括マージする（半自動レビュー用）

ワークフロー:
  1. analyze_remaining_hangul --json remaining.json で頻度集計
  2. remaining.json の syllable を generate_candidates へ渡して候補生成
  3. 本スクリプトで候補を確認し、OK のものを hangul_kana_dict に追加

使い方:
  # 候補JSONを確認して全件追加
  python scripts/merge_candidates.py candidates.json --merge

  # 対話で1件ずつ y/n
  python scripts/merge_candidates.py candidates.json --interactive

  # ドライラン（実際には書き込まない）
  python scripts/merge_candidates.py candidates.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESOURCES = os.path.join(os.path.dirname(__file__), "../resources")
DICT_PATH = os.path.join(RESOURCES, "hangul_kana_dict.json")


def load_candidates(path: str) -> list[dict]:
    """候補JSONを読み込む。analyze形式[{syllable,count}] も generate形式[{syllable,candidate,...}] も可"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSONは配列である必要があります")
    return data


def extract_merge_entries(data: list[dict]) -> dict[str, str]:
    """
    {syllable: kana} の辞書に変換。
    - generate形式: candidate があるエントリを採用
    - analyze形式: syllable のみ → 候補なしのためスキップ（generate を先に実行）
    """
    result = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        syl = item.get("syllable")
        kana = item.get("candidate") or item.get("kana")
        if syl and kana and len(syl) == 1:
            result[syl] = kana.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="候補を音節辞書に一括マージ")
    parser.add_argument(
        "candidates_file",
        help="候補JSON（generate_candidates --json の出力）",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="承認済み候補を hangul_kana_dict.json にマージ",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="1件ずつ y/n で確認してからマージ",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="マージ内容を表示するのみ（ファイルに書き込まない）",
    )
    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="頻度順の上位N件だけマージ（analyze→generate の順で作成した場合）",
    )
    args = parser.parse_args()

    if not os.path.exists(args.candidates_file):
        print(f"ファイルが見つかりません: {args.candidates_file}", file=sys.stderr)
        sys.exit(1)

    data = load_candidates(args.candidates_file)
    entries = extract_merge_entries(data)
    if args.top and args.top > 0:
        # 元の順序を維持して上位N件に制限
        order = [s for s in (x.get("syllable") for x in data if isinstance(x, dict)) if s and s in entries]
        limited = {s: entries[s] for s in order[: args.top] if s in entries}
        entries = limited

    if not entries:
        print("マージ対象がありません。candidate が null のエントリはスキップされます。")
        return

    # 対話モード: ユーザーが承認したものだけ残す
    if args.interactive:
        approved = {}
        for syl, kana in entries.items():
            try:
                ans = input(f"  {syl} → {kana} を追加しますか？ [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n中断しました。")
                break
            if ans in ("y", "yes"):
                approved[syl] = kana
        entries = approved
        if not entries:
            print("承認されたエントリはありません。")
            return

    print("=== マージ予定 ===")
    for syl, kana in sorted(entries.items()):
        print(f"  {syl} → {kana}")

    if args.dry_run:
        print("\n[--dry-run] 実際には書き込みません。")
        return

    if not args.merge and not args.interactive:
        print("\nマージするには --merge を指定してください。")
        return

    with open(DICT_PATH, encoding="utf-8") as f:
        d = json.load(f)
    d.update(entries)
    with open(DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"\n{len(entries)} 件を {DICT_PATH} に追加しました。")


if __name__ == "__main__":
    main()
