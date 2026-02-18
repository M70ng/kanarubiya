from .g2pk_wrapper import G2pkWrapper
from .hangul2kana import hangul_to_kana, get_merged_exceptions
import re

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
        例外辞書を適用（組み込み＋ユーザー追加。g2pk処理前）
        
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

    def _convert_remaining_hangul(self, text: str, use_g2pk: bool) -> str:
        """
        例外適用後の文字列のうち、まだ残っているハングル部分だけを変換する。
        （例: "ッピョ족하다구" → "ッピョ" はそのまま、"족하다구" を g2pk+hangul_to_kana）
        """
        parts = self.split_mixed_text(text)
        result = []
        for part in parts:
            if self.is_hangul(part):
                if use_g2pk:
                    phonetic = self.g2pk_wrapper.convert(part)
                    result.append(hangul_to_kana(phonetic))
                else:
                    result.append(hangul_to_kana(self.apply_exceptions(part)))
            else:
                result.append(part)
        return ''.join(result)
    
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
            # テキストをトークンに分割
            tokens = self.split_mixed_text(korean_text)
            result_tokens = []
            
            for token in tokens:
                if self.is_hangul(token):
                    # ハングルの場合のみ変換処理
                    if use_g2pk:
                        # 1. 例外辞書を適用（g2pk処理前）
                        token_with_exceptions = self.apply_exceptions(token)
                        
                        # 2. 例外が適用されなかった場合のみg2pkで発音に近いハングルに変換
                        if token_with_exceptions == token:
                            phonetic_hangul = self.g2pk_wrapper.convert(token)
                            # 3. ハングルをカナに変換
                            kana_result = hangul_to_kana(phonetic_hangul)
                        else:
                            # 例外で一部置換したあと、残ったハングルも変換する
                            kana_result = self._convert_remaining_hangul(token_with_exceptions, use_g2pk)
                    else:
                        # g2pkを使わずに直接カナ変換
                        kana_result = hangul_to_kana(token)
                    
                    result_tokens.append(kana_result)
                else:
                    # 英語・記号・空白はそのまま
                    result_tokens.append(token)
            
            # 結果を結合
            result = ''.join(result_tokens)
            
            if use_g2pk:
                print(f"g2pk変換: {korean_text} → {result}")
            else:
                print(f"直接変換: {korean_text} → {result}")
            
            return result
                
        except Exception as e:
            print(f"変換エラー: {e}")
            # エラーの場合は元のテキストを返す
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
            include_overall_phonetic: True の場合のみ、全文g2pk結果を計算して返す
        
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
            # テキストをトークンに分割
            tokens = self.split_mixed_text(korean_text)
            result_tokens = []
            token_details = []
            
            for token in tokens:
                token_info = {
                    'token': token,
                    'is_hangul': self.is_hangul(token),
                    'converted': token
                }
                
                if self.is_hangul(token):
                    # ハングルの場合のみ変換処理
                    if use_g2pk:
                        # 1. 例外辞書を適用（g2pk処理前）
                        token_with_exceptions = self.apply_exceptions(token)
                        
                        # 2. 例外が適用されなかった場合のみg2pkで発音に近いハングルに変換
                        if token_with_exceptions == token:
                            # g2pk変換
                            phonetic_hangul = self.g2pk_wrapper.convert(token)
                            token_info['phonetic_hangul'] = phonetic_hangul
                            kana_result = hangul_to_kana(phonetic_hangul)
                            token_info['converted'] = kana_result
                        else:
                            token_info['phonetic_hangul'] = token_with_exceptions
                            kana_result = self._convert_remaining_hangul(token_with_exceptions, use_g2pk)
                            token_info['converted'] = kana_result
                    else:
                        # 直接カナ変換
                        kana_result = hangul_to_kana(token)
                        token_info['converted'] = kana_result
                    
                    result_tokens.append(token_info['converted'])
                else:
                    # 英語・記号・空白はそのまま
                    result_tokens.append(token)
                
                token_details.append(token_info)
            
            # 結果を結合
            final_result = ''.join(result_tokens)
            
            result['tokens'] = token_details
            result['kana'] = final_result
            
            if use_g2pk and include_overall_phonetic:
                # 必要な場合のみ、全体g2pk変換を追加で計算
                overall_phonetic = self.g2pk_wrapper.convert(korean_text)
                result['phonetic_hangul'] = overall_phonetic
                
        except Exception as e:
            result['error'] = str(e)
        
        return result