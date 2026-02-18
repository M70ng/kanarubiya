#!/usr/bin/env python3
"""
例外辞書の各エントリを g2pk 経路で変換した結果と比較する。
実行: backend/ から python scripts/compare_exceptions_vs_g2pk.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.g2pk_wrapper import G2pkWrapper
from core.hangul2kana import hangul_to_kana

EXC_PATH = os.path.join(os.path.dirname(__file__), '../resources/kana_exceptions.json')
USER_EXC_PATH = os.path.join(os.path.dirname(__file__), '../resources/user_kana_exceptions.json')

with open(EXC_PATH, encoding='utf-8') as f:
    exc = json.load(f)
try:
    with open(USER_EXC_PATH, encoding='utf-8') as f:
        user = json.load(f)
        if user:
            exc.update(user)
except (FileNotFoundError, json.JSONDecodeError):
    pass

g2pk = G2pkWrapper()
print("hangul       | exception     | g2pk path")
print("-" * 55)
for h, kana in exc.items():
    ph = g2pk.convert(h)
    via_g2pk = hangul_to_kana(ph)
    diff = "" if via_g2pk == kana else "  ← diff"
    print(f"{h:12} | {kana:12} | {via_g2pk:12}{diff}")
