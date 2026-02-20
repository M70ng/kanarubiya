"""
韓国語テキストを日本語カナに変換する変換ロジックの中核

■ 主に使う関数
  convert()  … 公開API。外部から呼ぶエントリポイント

■ 変換フロー（use_g2pk=True がデフォルト）
  convert()
    └─ _convert_with_g2pk_full_text()  … 全文一括変換の実処理
           └─ apply_exceptions()       … 例外辞書を適用
           └─ g2pk_wrapper.convert()   … g2pkで発音記号化（1回）
           └─ hangul_to_kana()         … カナへ変換

■ その他の関数（以前のバージョンで使っていたもの）
  convert_with_details()  … トークンごとの詳細付きで返す（UI向け）
  split_mixed_text()      … ハングル/英数字/記号で分割
  is_hangul()             … ハングル判定
"""
from collections import Counter

from .g2pk_wrapper import G2pkWrapper
from .hangul2kana import hangul_to_kana, get_merged_exceptions
import re


def count_remaining_hangul(text: str) -> Counter[str]:
    """
    変換後の文字列から残ったハングル音節 [가-힣] の頻度を返す。

    Returns:
        音節をキー、出現回数を値とする Counter
    """
    return Counter(re.findall(r"[가-힣]", text))


def _warn_remaining_hangul(kana_str: str) -> None:
    """
    韓国語→カナ変換後の文字列から残ったハングル [가-힣] を検出し、
    残っている場合のみ頻度付きで警告ログを出力する。
    （頻度の高い順で表示し、上位から潰しやすくする）
    """
    counter = count_remaining_hangul(kana_str)
    if counter:
        ranked = counter.most_common()
        items = ", ".join(f"{s}({c})" for s, c in ranked)
        print(f"[WARN] Remaining Hangul detected: [{items}]")


class KoreanToKanaConverter:
    def __init__(self):
        """韓国語→カナ変換器の初期化"""
        self.g2pk_wrapper = G2pkWrapper()
    
    def is_hangul(self, token: str) -> bool:
        """
        トークンがハングルのみで構成されているかチェック
        
        Args:
            token: チェックする文字列
        
        Returns:
            ハングルのみの場合True
        """
        return bool(re.fullmatch(r"[가-힣]+", token))
    
    def split_mixed_text(self, text: str) -> list[str]:
        """
        ハングル、英数字、その他記号を区別して分割
        
        Args:
            text: 分割するテキスト
        
        Returns:
            分割されたトークンのリスト
        """
        # ハングル、英数字、その他記号、空白を区別して分割
        return re.findall(r"[가-힣]+|[a-zA-Z0-9'']+|[^\s가-힣a-zA-Z0-9]+|\s", text)
    
    def apply_exceptions(self, text: str) -> str:
        """
        例外辞書を適用（g2pk処理前）
        
        Args:
            text: 適用するテキスト
        
        Returns:
            例外が適用されたテキスト
        """
        result = text
        for exc, kana in get_merged_exceptions().items():
            if exc in result:
                result = result.replace(exc, kana)
        return result

    def _convert_with_g2pk_full_text(self, korean_text: str) -> str:
        """
        g2pには全文を渡す。基本的にトークン別じゃなくてこっち使う！
        全文一括で変換: 例外辞書適用 → g2p 1回 → hangul_to_kana。
        """
        text_with_exceptions = self.apply_exceptions(korean_text)
        phonetic = self.g2pk_wrapper.convert(text_with_exceptions)
        return hangul_to_kana(phonetic)

    def convert(self, korean_text: str, use_g2pk: bool = True) -> str:
        """
        韓国語テキストを日本語カナに変換
        ハングル部分のみを変換し、英語・記号・数字はそのまま残す

        Args:
            korean_text: 韓国語テキスト
            use_g2pk: g2pkを使用するかどうか（True推奨）

        Returns:
            日本語カナ文字列（英語・記号はそのまま）
        """
        try:
            if use_g2pk:
                # 全文一括: 例外辞書 → g2p 1回 → hangul_to_kana
                result = self._convert_with_g2pk_full_text(korean_text)
                print(f"g2pk変換: {korean_text} → {result}")
            else:
                tokens = self.split_mixed_text(korean_text)
                result_tokens = []
                for token in tokens:
                    if self.is_hangul(token):
                        result_tokens.append(hangul_to_kana(token))
                    else:
                        result_tokens.append(token)
                result = ''.join(result_tokens)
                print(f"直接変換: {korean_text} → {result}")

            _warn_remaining_hangul(result)
            return result

        except Exception as e:
            print(f"変換エラー: {e}")
            return korean_text
    
    def convert_with_details(
        self,
        korean_text: str,
        use_g2pk: bool = True,
        include_overall_phonetic: bool = False,
    ) -> dict:
        """
        変換の詳細情報を含めて変換

        Args:
            korean_text: 韓国語テキスト
            use_g2pk: g2pkを使用するかどうか
            include_overall_phonetic: True の場合のみ、phonetic_hangul を返す

        Returns:
            変換詳細を含む辞書
        """
        result = {
            'original': korean_text,
            'phonetic_hangul': korean_text,
            'kana': korean_text,
            'use_g2pk': use_g2pk,
            'tokens': []
        }

        try:
            tokens = self.split_mixed_text(korean_text)

            if use_g2pk:
                # 全文一括: 例外辞書 → g2p 1回 → hangul_to_kana
                text_with_exceptions = self.apply_exceptions(korean_text)
                phonetic = self.g2pk_wrapper.convert(text_with_exceptions)
                final_result = hangul_to_kana(phonetic)
                if include_overall_phonetic:
                    result['phonetic_hangul'] = phonetic
                result_parts = self.split_mixed_text(final_result)
                phonetic_parts = self.split_mixed_text(phonetic)
            else:
                result_tokens = []
                for token in tokens:
                    if self.is_hangul(token):
                        result_tokens.append(hangul_to_kana(token))
                    else:
                        result_tokens.append(token)
                final_result = ''.join(result_tokens)
                result_parts = result_tokens
                phonetic_parts = result_parts  # use_g2pk=False では未使用

            token_details = []
            for i, token in enumerate(tokens):
                converted = result_parts[i] if i < len(result_parts) else token
                token_info = {
                    'token': token,
                    'is_hangul': self.is_hangul(token),
                    'converted': converted
                }
                if use_g2pk and self.is_hangul(token) and include_overall_phonetic and i < len(phonetic_parts):
                    token_info['phonetic_hangul'] = phonetic_parts[i]
                token_details.append(token_info)

            result['tokens'] = token_details
            result['kana'] = final_result
            _warn_remaining_hangul(final_result)

        except Exception as e:
            result['error'] = str(e)

        return result