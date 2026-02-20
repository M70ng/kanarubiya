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

    def _is_english_or_mixed_alnum(self, token: str) -> bool:
        """英語または英数字混在トークンか（g2pk の convert_eng で変換させたくないもの）"""
        return bool(re.fullmatch(r"[a-zA-Z0-9'']+", token) and re.search(r"[a-zA-Z]", token))

    def _is_numeric_only(self, token: str) -> bool:
        """数字のみのトークンか（g2pk の convert_num の対象）"""
        return bool(re.fullmatch(r"[0-9]+", token))

    def _should_mask_token(self, token: str, convert_numbers: bool) -> bool:
        """
        g2pk に渡す前マスクすべきトークンか。
        英語・英数字混在は常にマスク。数字のみは convert_numbers=False のときのみマスク。
        """
        if self._is_english_or_mixed_alnum(token):
            return True
        if self._is_numeric_only(token) and not convert_numbers:
            return True
        return False

    def _convert_with_g2pk_full_text(
        self,
        korean_text: str,
        convert_numbers: bool = False,
        return_phonetic: bool = False,
    ) -> str | tuple[str, str]:
        """
        英語（＋convert_numbers=False のとき数字）をプレースホルダーでマスク → g2pk 1回 → アンマスク。
        g2pk には「英語→ハングル」「数字→読み」変換機能がありオプションで止められないため、
        事前マスクで回避する。g2pk 呼び出しは1回のみ。
        """
        text_with_exceptions = self.apply_exceptions(korean_text)
        tokens = self.split_mixed_text(text_with_exceptions)
        placeholders: list[tuple[str, str]] = []
        masked_parts = []
        for token in tokens:
            if self._should_mask_token(token, convert_numbers):
                # 数字を含むと g2pk の convert_num が変換して壊れるので、PUA のみで一意なプレースホルダーを使う
                ph = "\uE000" + chr(0xE002 + len(placeholders)) + "\uE001"
                placeholders.append((ph, token))
                masked_parts.append(ph)
            else:
                masked_parts.append(token)
        masked_text = "".join(masked_parts)
        phonetic = self.g2pk_wrapper.convert(masked_text)
        for ph, orig in placeholders:
            phonetic = phonetic.replace(ph, orig)
        result = hangul_to_kana(phonetic)
        for ph, orig in placeholders:
            result = result.replace(ph, orig)
        if return_phonetic:
            return result, phonetic
        return result

    def convert(
        self, korean_text: str, use_g2pk: bool = True, convert_numbers: bool = False
    ) -> str:
        """
        韓国語テキストを日本語カナに変換
        ハングル部分のみを変換し、英語・記号はそのまま残す。
        数字は convert_numbers=True のときのみ韓国語読み→カナに変換。

        Args:
            korean_text: 韓国語テキスト
            use_g2pk: g2pkを使用するかどうか（True推奨）
            convert_numbers: 数字を韓国語読みでカナ変換するか（False=そのまま）

        Returns:
            日本語カナ文字列（英語・記号はそのまま。数字は convert_numbers に依存）
        """
        try:
            if use_g2pk:
                result = self._convert_with_g2pk_full_text(korean_text, convert_numbers=convert_numbers)
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
        convert_numbers: bool = False,
        include_overall_phonetic: bool = False,
    ) -> dict:
        """
        変換の詳細情報を含めて変換

        Args:
            korean_text: 韓国語テキスト
            use_g2pk: g2pkを使用するかどうか
            convert_numbers: 数字を韓国語読みでカナ変換するか（False=そのまま）
            include_overall_phonetic: True の場合のみ、phonetic_hangul を返す

        Returns:
            変換詳細を含む辞書
        """
        result = {
            'original': korean_text,
            'phonetic_hangul': korean_text,
            'kana': korean_text,
            'use_g2pk': use_g2pk,
            'convert_numbers': convert_numbers,
            'tokens': []
        }

        try:
            tokens = self.split_mixed_text(korean_text)

            if use_g2pk:
                out = self._convert_with_g2pk_full_text(
                    korean_text,
                    convert_numbers=convert_numbers,
                    return_phonetic=include_overall_phonetic,
                )
                if include_overall_phonetic:
                    final_result, result['phonetic_hangul'] = out
                else:
                    final_result = out
                text_with_exceptions = self.apply_exceptions(korean_text)
                tokens = self.split_mixed_text(text_with_exceptions)
                result_parts = self.split_mixed_text(final_result)
                phonetic_parts = self.split_mixed_text(result.get('phonetic_hangul', korean_text))
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