#!/usr/bin/env python3
"""
辞書の品質検査: 値にハングル・ローマ字が混入していないかチェック

NG 条件（純カナ仕様）:
  - 値に [가-힣] が含まれる … ハングルがそのまま残っている（変換漏れ）
  - 値に [A-Za-z] が含まれる … ローマ字混入

該当キーを一覧表示。--fix で該当エントリの値を空文字に置換して修正可能。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESOURCES = os.path.join(os.path.dirname(__file__), "../resources")
HANGUL_DICT_PATH = os.path.join(RESOURCES, "hangul_kana_dict.json")
KANA_EXC_PATH = os.path.join(RESOURCES, "kana_exceptions.json")
USER_EXC_PATH = os.path.join(RESOURCES, "user_kana_exceptions.json")

HANGUL_PATTERN = re.compile(r"[가-힣]")
ROMAN_PATTERN = re.compile(r"[A-Za-z]")


def check_value(value: str) -> list[str]:
    """値の問題点を返す。問題なければ空リスト"""
    issues = []
    if HANGUL_PATTERN.search(value):
        issues.append("hangul")
    if ROMAN_PATTERN.search(value):
        issues.append("roman")
    return issues


def load_dicts() -> dict[str, dict[str, str]]:
    """全辞書を読み込む"""
    result = {}
    if os.path.exists(HANGUL_DICT_PATH):
        with open(HANGUL_DICT_PATH, encoding="utf-8") as f:
            result["hangul_kana_dict"] = json.load(f)
    if os.path.exists(KANA_EXC_PATH):
        with open(KANA_EXC_PATH, encoding="utf-8") as f:
            result["kana_exceptions"] = json.load(f)
    if os.path.exists(USER_EXC_PATH):
        try:
            with open(USER_EXC_PATH, encoding="utf-8") as f:
                data = json.load(f)
                result["user_kana_exceptions"] = data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            result["user_kana_exceptions"] = {}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="辞書品質検査")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="該当エントリの値を空文字に置換して保存（要確認）",
    )
    parser.add_argument(
        "--dict",
        choices=["hangul", "kana_exc", "user_exc", "all"],
        default="all",
        help="検査対象辞書",
    )
    args = parser.parse_args()

    dicts = load_dicts()
    targets = []
    if args.dict in ("hangul", "all") and "hangul_kana_dict" in dicts:
        targets.append(("hangul_kana_dict", HANGUL_DICT_PATH, dicts["hangul_kana_dict"]))
    if args.dict in ("kana_exc", "all") and "kana_exceptions" in dicts:
        targets.append(
            ("kana_exceptions", KANA_EXC_PATH, dicts["kana_exceptions"])
        )
    if args.dict in ("user_exc", "all") and "user_kana_exceptions" in dicts:
        targets.append(
            (
                "user_kana_exceptions",
                USER_EXC_PATH,
                dicts["user_kana_exceptions"],
            )
        )

    bad_entries: list[tuple[str, str, str, list[str]]] = []

    for name, path, d in targets:
        for key, value in d.items():
            issues = check_value(value)
            if issues:
                bad_entries.append((name, key, value, issues))

    if not bad_entries:
        print("問題のあるエントリはありません。")
        return

    print("=== 品質NGエントリ一覧 ===")
    for name, key, value, issues in bad_entries:
        issue_str = ", ".join(issues)
        print(f"  [{name}] {key!r} -> {value!r}  (NG: {issue_str})")

    if args.fix:
        print("\n--fix: 該当エントリを空文字に置換します。")
        for name, path, d in targets:
            modified = False
            for key, value in list(d.items()):
                if check_value(value):
                    d[key] = ""
                    modified = True
            if modified:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
                print(f"  更新: {path}")
    else:
        print("\n修正するには --fix を指定してください。")


if __name__ == "__main__":
    main()
